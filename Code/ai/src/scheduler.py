"""
Production-like scheduler: sinh lịch tưới 7 ngày dựa trên sensor + weather, bám theo báo cáo.

Mục tiêu:
- Rõ ràng 3 horizon: 1–2 ngày, 3–5 ngày, 7 ngày.
- Output có:
    - summary theo từng horizon
    - days_detail: từng ngày có gì (mưa, ẩm, tổng phút tưới, horizon_group)
    - slots: chi tiết từng lần tưới (start/end/duration)
    - water_balance rất đơn giản (rain_mm_7d, irrigation_mm_7d, target_mm_7d)

Lưu ý:
- Đây vẫn là bản rule-based (chưa cắm model XGBoost nowcast), nhưng đã:
    - Phân tách horizon 1–2 ngày / 3–5 ngày / 6–7 ngày.
    - Áp dụng cấu hình mùa vụ (Anti‑Nồm / Fast‑Reaction / Saving) theo tháng.
    - Dùng forecast_7days.csv làm dự báo 7 ngày (thay vì tự chế từ history).

Chạy:
    cd D:\\IoT\\Code\\ai
    python src\\scheduler.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Literal

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

SENSOR_SYNTH = DATA_DIR / "sensor_raw_60d_synth.csv"
SENSOR_REAL = DATA_DIR / "sensor_raw_60d.csv"
OWM_HISTORY_3Y = DATA_DIR / "owm_history_3years.csv"
FORECAST_7D_CSV = DATA_DIR / "forecast_7days.csv"

# Giả định đơn giản: 1 phút tưới ≈ 0.4 mm nước (tuỳ cấu hình béc tưới ngoài thực tế)
MM_PER_MIN_IRRIGATION = 0.4
TARGET_MM_7D = 50.0  # nhu cầu nước mục tiêu / tuần (mm) – chỉ là giá trị tham khảo cho demo


HorizonGroup = Literal["d1_2", "d3_5", "d6_7"]


@dataclass
class SeasonConfig:
    """Ngưỡng theo mùa, bám phần Seasonal Adaptation trong báo cáo."""

    name: str
    # Ngưỡng soil (theo %)
    soil_critical: float  # rất khô → luôn ưu tiên tưới
    soil_ok: float        # trên mức này coi là đủ ẩm
    # Nhu cầu nước mục tiêu / tuần (mm)
    target_mm_7d: float
    # Ngưỡng mưa/ngày để coi là “mưa lớn” hoặc “mưa vừa” (mm)
    heavy_rain_mm: float
    medium_rain_mm: float


@dataclass
class DayPlan:
    date: date
    rain_mm: float
    soil_moist_ref: float
    slots: List[Dict[str, Any]]
    note: str
    horizon_group: HorizonGroup
    season_name: str


def get_season_config(month: int) -> SeasonConfig:
    """
    Map tháng → chế độ mùa vụ theo báo cáo:
    - Tháng 2–4: Xuân (Anti‑Nồm)  → ưu tiên tránh hiểu nhầm nồm là mưa, target trung bình.
    - Tháng 5–7: Hè (Fast‑Reaction) → nhu cầu nước cao hơn, nhưng rất nhạy với mưa/dông.
    - Còn lại : Thu/Đông (Saving)   → nhu cầu nước thấp, dễ hoãn tưới khi có mưa nhỏ.
    """
    if month in (2, 3, 4):
        # Spring – Anti‑Nồm
        return SeasonConfig(
            name="spring_anti_nom",
            soil_critical=28.0,
            soil_ok=40.0,
            target_mm_7d=45.0,
            heavy_rain_mm=20.0,
            medium_rain_mm=5.0,
        )
    if month in (5, 6, 7):
        # Summer – Fast Reaction
        return SeasonConfig(
            name="summer_fast_reaction",
            soil_critical=30.0,
            soil_ok=45.0,
            target_mm_7d=70.0,
            heavy_rain_mm=15.0,
            medium_rain_mm=3.0,
        )
    # Fall / Winter – Saving
    return SeasonConfig(
        name="fall_winter_saving",
        soil_critical=25.0,
        soil_ok=38.0,
        target_mm_7d=35.0,
        heavy_rain_mm=12.0,
        medium_rain_mm=3.0,
    )


def _choose_sensor_source() -> Path:
    """Ưu tiên sensor_real, nếu không có thì dùng sensor_synth."""
    if SENSOR_REAL.exists():
        return SENSOR_REAL
    if SENSOR_SYNTH.exists():
        return SENSOR_SYNTH
    raise FileNotFoundError(
        f"Không tìm thấy {SENSOR_REAL} hoặc {SENSOR_SYNTH}. "
        "Cần chạy collect_data_mqtt.py hoặc generate_synthetic_sensor_from_labels.py trước."
    )


def load_sensor() -> pd.DataFrame:
    sensor_path = _choose_sensor_source()
    df = pd.read_csv(sensor_path, parse_dates=["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    print(f"✓ Loaded sensor data from {sensor_path.name}: {len(df)} rows")
    return df


def load_api_history() -> pd.DataFrame:
    if not OWM_HISTORY_3Y.exists():
        raise FileNotFoundError(
            f"owm_history_3years.csv không tồn tại tại {OWM_HISTORY_3Y}. "
            "Hãy chạy fetch_openmeteo_history.py trước."
        )
    df = pd.read_csv(OWM_HISTORY_3Y, parse_dates=["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    if "api_rain_1h" not in df.columns:
        raise KeyError("Cột 'api_rain_1h' không có trong owm_history_3years.csv")
    print(f"✓ Loaded API history 3y: {len(df)} rows")
    return df


def load_forecast_daily() -> pd.DataFrame:
    """
    Load forecast_7days.csv (hourly) và tổng hợp theo ngày.

    Các yếu tố chính cho lịch tưới (theo báo cáo):
    - Tổng lượng mưa/ngày (rain_mm)
    - Xác suất mưa lớn nhất trong ngày (pop_max)
    - Weather_code chủ đạo (để sau này có thể phân biệt mưa phùn / nồm / dông)
    """
    if not FORECAST_7D_CSV.exists():
        # Fallback: tự build pseudo từ history nếu chưa có forecast_7days.
        api_df = load_api_history()
        api_df["date"] = api_df["ts"].dt.date
        daily = (
            api_df.groupby("date", as_index=False)["api_rain_1h"]
            .sum()
            .rename(columns={"api_rain_1h": "rain_mm"})
        )
        # Dùng 7 ngày cuối, map sang tương lai (giống logic cũ)
        last7 = daily.tail(7).reset_index(drop=True)
        today = datetime.utcnow().date()
        last7["date"] = [today + timedelta(days=i + 1) for i in range(7)]
        last7["pop_max"] = 0.0
        last7["weather_code_main"] = 0
        print("⚠️  forecast_7days.csv not found, using pseudo forecast from history.")
        return last7[["date", "rain_mm", "pop_max", "weather_code_main"]]

    df = pd.read_csv(FORECAST_7D_CSV, parse_dates=["ts"])
    if "api_rain_1h" not in df.columns or "api_pop" not in df.columns:
        raise KeyError("forecast_7days.csv phải có cột 'api_rain_1h' và 'api_pop'.")

    df["date"] = df["ts"].dt.date
    agg = (
        df.groupby("date")
        .agg(
            rain_mm=("api_rain_1h", "sum"),
            pop_max=("api_pop", "max"),
            # Lấy weather_code xuất hiện nhiều nhất trong ngày (mode đơn giản)
            weather_code_main=("api_weather_code", lambda x: x.value_counts().idxmax() if len(x) else 0),
        )
        .reset_index()
    )
    print(
        f"✓ Loaded forecast_7days.csv → aggregated to {len(agg)} days "
        f"({agg['date'].min()} → {agg['date'].max()})"
    )
    return agg


def compute_soil_reference(sensor_df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính soil_moist trung bình theo ngày cho 7 ngày gần nhất trong dữ liệu sensor,
    sau đó map sang 7 ngày tương lai.
    """
    df = sensor_df.copy()
    df["date"] = df["ts"].dt.date
    daily = (
        df.groupby("date", as_index=False)["soil_moist_pct"]
        .mean()
        .rename(columns={"soil_moist_pct": "soil_moist_mean"})
    )
    last7 = daily.tail(7).reset_index(drop=True)

    today = datetime.utcnow().date()
    forecast_dates = [today + timedelta(days=i + 1) for i in range(7)]
    last7["forecast_date"] = forecast_dates
    print(
        "✓ Built soil moisture reference 7d "
        f"({last7['date'].min()} → {last7['date'].max()} "
        f"mapped to {forecast_dates[0]} → {forecast_dates[-1]})"
    )
    return last7[["forecast_date", "soil_moist_mean"]]


def _assign_horizon_group(idx: int) -> HorizonGroup:
    """
    Map index (0..6) → horizon group:
    - 0,1 → d1_2
    - 2,3,4 → d3_5
    - 5,6 → d6_7
    """
    if idx <= 1:
        return "d1_2"
    if idx <= 4:
        return "d3_5"
    return "d6_7"


def build_day_plans(
    forecast_df: pd.DataFrame, soil_ref_df: pd.DataFrame
) -> List[DayPlan]:
    """
    Rule-based scheduler có season-aware (theo báo cáo):
    - Input:
        + forecast_df: daily rain_mm, pop_max, weather_code_main (từ forecast_7days.csv)
        + soil_ref_df: soil_moist_mean 7 ngày gần nhất (sensor)
    - Logic (high level):
        + Mỗi ngày xác định SeasonConfig theo month.
        + So sánh rain_mm với heavy_rain_mm / medium_rain_mm của mùa đó.
        + So sánh soil_moist_ref với soil_critical / soil_ok.
        + Quyết định số slot và duration.
    """
    # Đồng bộ theo ngày: forecast_df.date vs soil_ref_df.forecast_date
    soil = soil_ref_df.rename(columns={"forecast_date": "date"})
    merged = forecast_df.merge(soil, on="date", how="left")
    plans: List[DayPlan] = []

    for idx, row in merged.reset_index(drop=True).iterrows():
        d: date = row["date"]
        rain_mm = float(row["rain_mm"])
        soil_ref = float(row["soil_moist_mean"]) if not np.isnan(row["soil_moist_mean"]) else 35.0
        pop_max = float(row.get("pop_max", 0.0))
        wc_main = int(row.get("weather_code_main", 0))

        season = get_season_config(month=d.month)

        slots: List[Dict[str, Any]] = []
        note = ""

        # Anti‑Nồm handling (Spring): nếu weather_code thuộc nhóm 7xx (sương mù/nồm)
        # và soil rất khô thì vẫn ưu tiên tưới dù pop/mưa nhỏ.
        is_nom_like = 700 <= wc_main < 800

        if rain_mm >= season.heavy_rain_mm and pop_max >= 0.6 and not is_nom_like:
            note = (
                f"Mưa lớn dự kiến ~{rain_mm:.1f}mm (pop_max={pop_max:.0%}), "
                "hoãn toàn bộ tưới để tận dụng nước trời."
            )
        elif rain_mm >= season.medium_rain_mm and not is_nom_like:
            if soil_ref < season.soil_critical:
                note = (
                    f"Mưa vừa ~{rain_mm:.1f}mm, đất rất khô ({soil_ref:.1f}%), "
                    "tưới nhẹ 10 phút buổi sáng (tưới bù)."
                )
                start = datetime.combine(d, datetime.min.time()).replace(hour=7)
                slots.append(
                    {
                        "start_ts": start.isoformat(),
                        "end_ts": (start + timedelta(minutes=10)).isoformat(),
                        "device_id": "esp32-01",
                        "duration_min": 10,
                    }
                )
            else:
                note = (
                    f"Mưa vừa ~{rain_mm:.1f}mm, đất đủ ẩm ({soil_ref:.1f}%), không tưới."
                )
        else:
            # Ít mưa trong ngày (< medium_rain_mm) → quyết định theo độ ẩm đất + mùa vụ
            if soil_ref < season.soil_critical:
                note = (
                    f"Ít mưa trong ngày và đất rất khô ({soil_ref:.1f}%), tưới 2 lần 20 phút."
                )
                for hour in (7, 17):
                    start = datetime.combine(d, datetime.min.time()).replace(hour=hour)
                    slots.append(
                        {
                            "start_ts": start.isoformat(),
                            "end_ts": (start + timedelta(minutes=20)).isoformat(),
                            "device_id": "esp32-01",
                            "duration_min": 20,
                        }
                    )
            elif soil_ref < season.soil_ok:
                note = (
                    f"Ít mưa trong ngày và đất khá khô ({soil_ref:.1f}%), tưới 1 lần 15 phút."
                )
                start = datetime.combine(d, datetime.min.time()).replace(hour=7)
                slots.append(
                    {
                        "start_ts": start.isoformat(),
                        "end_ts": (start + timedelta(minutes=15)).isoformat(),
                        "device_id": "esp32-01",
                        "duration_min": 15,
                    }
                )
            else:
                note = (
                    f"Đất đủ ẩm ({soil_ref:.1f}%), mưa ít, chưa cần tưới."
                )

        plans.append(
            DayPlan(
                date=d,
                rain_mm=rain_mm,
                soil_moist_ref=soil_ref,
                slots=slots,
                note=note,
                horizon_group=_assign_horizon_group(idx),
                season_name=season.name,
            )
        )

    return plans


def _summarize_horizon(plans: List[DayPlan], group: HorizonGroup) -> str:
    """Ghép note của các ngày thuộc một horizon_group."""
    notes = [p.note for p in plans if p.horizon_group == group]
    return " | ".join(notes)


def _compute_water_balance(plans: List[DayPlan]) -> Dict[str, Any]:
    """
    Water-balance rất đơn giản:
    - rain_mm_7d: tổng mưa dự kiến 7 ngày.
    - irrigation_min_7d: tổng phút tưới trong 7 ngày.
    - irrigation_mm_7d: quy đổi từ phút → mm bằng MM_PER_MIN_IRRIGATION.
    - target_mm_7d: nhu cầu mục tiêu (config).
    - status: 'deficit' nếu < 0.8 * target, 'excess' nếu > 1.2 * target, else 'ok'.
    """
    rain_mm_7d = sum(p.rain_mm for p in plans)
    irrigation_min_7d = sum(
        sum(s.get("duration_min", 0.0) for s in p.slots) for p in plans
    )
    irrigation_mm_7d = irrigation_min_7d * MM_PER_MIN_IRRIGATION

    total_mm_7d = rain_mm_7d + irrigation_mm_7d

    # Lấy target theo mùa của ngày đầu tiên (giả định 7 ngày không qua quá nhiều mùa)
    first_season = get_season_config(month=datetime.fromisoformat(plans[0].date.isoformat()).month)
    target_mm_7d = first_season.target_mm_7d
    if total_mm_7d < 0.8 * target_mm_7d:
        status = "deficit"
    elif total_mm_7d > 1.2 * target_mm_7d:
        status = "excess"
    else:
        status = "ok"

    return {
        "rain_mm_7d": round(rain_mm_7d, 2),
        "irrigation_min_7d": round(irrigation_min_7d, 1),
        "irrigation_mm_7d": round(irrigation_mm_7d, 2),
        "target_mm_7d": target_mm_7d,
        "total_mm_7d": round(total_mm_7d, 2),
        "status": status,
        "comment": (
            "Thiếu nước so với mục tiêu, có thể tăng thời lượng tưới."
            if status == "deficit"
            else "Dư nước so với mục tiêu, có thể giảm tưới."
            if status == "excess"
            else "Tổng mưa + tưới tuần tới gần với mục tiêu."
        ),
        "mm_per_min_irrigation": MM_PER_MIN_IRRIGATION,
    }


def build_output_json(plans: List[DayPlan]) -> Dict[str, Any]:
    now = datetime.utcnow()

    # Summary 3 horizon
    summary_short = _summarize_horizon(plans, "d1_2")
    summary_mid = _summarize_horizon(plans, "d3_5")
    summary_long = _summarize_horizon(plans, "d6_7")

    # Days detail
    days_detail: List[Dict[str, Any]] = []
    for p in plans:
        total_min = sum(s.get("duration_min", 0.0) for s in p.slots)
        days_detail.append(
            {
                "date": p.date.isoformat(),
                "season": p.season_name,
                "horizon_group": p.horizon_group,  # d1_2 / d3_5 / d6_7
                "rain_mm": round(p.rain_mm, 2),
                "soil_moist_ref": round(p.soil_moist_ref, 2),
                "total_irrigation_min": round(total_min, 1),
                "note": p.note,
            }
        )

    # All slots
    slots_all: List[Dict[str, Any]] = []
    for p in plans:
        for s in p.slots:
            slots_all.append(
                {
                    **s,
                    "rain_mm_day": round(p.rain_mm, 2),
                    "soil_moist_ref": round(p.soil_moist_ref, 2),
                    "date": p.date.isoformat(),
                    "horizon_group": p.horizon_group,
                    "season": p.season_name,
                }
            )

    water_balance = _compute_water_balance(plans)

    return {
        "timestamp": now.isoformat() + "Z",
        "location": {"lat": 21.0245, "lon": 105.8412},
        "mode": "scheduler_rule_based_v1",
        "summary": {
            "horizon_1_2_days": summary_short,
            "horizon_3_5_days": summary_mid,
            "horizon_7_days": summary_long,
        },
        "meta": {
            "source_sensor": _choose_sensor_source().name,
            "source_api": str(FORECAST_7D_CSV.name)
            if FORECAST_7D_CSV.exists()
            else OWM_HISTORY_3Y.name,
            "days": len(plans),
        },
        "water_balance": water_balance,
        "days_detail": days_detail,
        "slots": slots_all,
    }


def main() -> None:
    print("=" * 70)
    print("🗓️  SCHEDULER – LẬP LỊCH TƯỚI 7 NGÀY (RULE-BASED)")
    print("=" * 70)
    print(f"Sensor real  : {SENSOR_REAL}")
    print(f"Sensor synth : {SENSOR_SYNTH}")
    print(f"Forecast 7d  : {FORECAST_7D_CSV}")
    print("-" * 70)

    sensor_df = load_sensor()
    forecast_daily = load_forecast_daily()
    soil_ref_7d = compute_soil_reference(sensor_df)
    plans = build_day_plans(forecast_daily, soil_ref_7d)
    out = build_output_json(plans)

    # Lưu vào file JSON
    output_file = ROOT / "data" / "lich_tuoi.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved schedule to {output_file}")
    print("\nDone.")


if __name__ == "__main__":
    main()


