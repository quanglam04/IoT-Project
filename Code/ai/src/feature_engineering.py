"""
Feature engineering theo báo cáo IoT - Virtual Rain Sensor.

13 features chính:
1. api_pop, api_rain_1h, uvi_index (từ OpenWeatherMap API)
2. pressure_slope_1h, temp_drop_15m, rh_rise_15m (từ sensor trend)
3. dew_point_diff, temp_bias (fusion API vs Sensor)
4. soil_moist_smooth (sensor)
5. month_sin, month_cos, hour_sin, hour_cos (cyclical encoding)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import numpy as np
import pandas as pd

# Constants
SECONDS_15 = 15
WINDOW_1H = int(60 * 60 / SECONDS_15)  # 240 điểm (nếu 15s/bản ghi)
WINDOW_15M = int(15 * 60 / SECONDS_15)  # 60 điểm
WINDOW_SOIL_SMOOTH = 20  # 5 phút (20 mẫu × 15s)

# Nếu dữ liệu là 5 phút/bản ghi (như hiện tại)
WINDOW_1H_5MIN = 12  # 12 điểm × 5 phút = 1 giờ
WINDOW_15M_5MIN = 3  # 3 điểm × 5 phút = 15 phút
WINDOW_SOIL_SMOOTH_5MIN = 1  # 1 điểm (5 phút)


@dataclass
class FeatureVector:
    """Vector feature 1 mẫu (theo báo cáo)."""

    api_pop: float
    api_rain_1h: float
    pressure_slope_1h: float
    temp_drop_15m: float
    rh_rise_15m: float
    dew_point_diff: float
    temp_bias: float
    soil_moist_smooth: float
    month_sin: float
    month_cos: float
    hour_sin: float
    hour_cos: float
    uvi_index: float

    def to_list(self) -> List[float]:
        return [
            self.api_pop,
            self.api_rain_1h,
            self.pressure_slope_1h,
            self.temp_drop_15m,
            self.rh_rise_15m,
            self.dew_point_diff,
            self.temp_bias,
            self.soil_moist_smooth,
            self.month_sin,
            self.month_cos,
            self.hour_sin,
            self.hour_cos,
            self.uvi_index,
        ]


FEATURE_NAMES: List[str] = [
    "api_pop",
    "api_rain_1h",
    "pressure_slope_1h",
    "temp_drop_15m",
    "rh_rise_15m",
    "dew_point_diff",
    "temp_bias",
    "soil_moist_smooth",
    "month_sin",
    "month_cos",
    "hour_sin",
    "hour_cos",
    "uvi_index",
]


def cyclical_encode_month(month: int) -> Dict[str, float]:
    """Cyclical encoding cho tháng (1-12)."""
    rad = 2 * np.pi * (month % 12) / 12.0
    return {
        "month_sin": float(np.sin(rad)),
        "month_cos": float(np.cos(rad)),
    }


def cyclical_encode_hour(hour: int) -> Dict[str, float]:
    """Cyclical encoding cho giờ (0-23)."""
    rad = 2 * np.pi * (hour % 24) / 24.0
    return {
        "hour_sin": float(np.sin(rad)),
        "hour_cos": float(np.cos(rad)),
    }


def compute_dew_point(temp_c: float, rh_pct: float) -> float:
    """
    Tính điểm sương (Magnus approximation).
    
    Args:
        temp_c: Nhiệt độ (°C)
        rh_pct: Độ ẩm tương đối (%)
    
    Returns:
        Điểm sương (°C)
    """
    import math
    a = 17.27
    b = 237.7
    gamma = (a * temp_c / (b + temp_c)) + math.log(max(rh_pct, 1e-3) / 100.0)
    return (b * gamma) / (a - gamma)


def compute_feature_from_window(
    sensor_df: pd.DataFrame,
    api_row: pd.Series,
    interval_seconds: int = 300,  # 5 phút (300s) hoặc 15s
) -> FeatureVector:
    """
    Tính feature từ sensor buffer + API data.
    
    Args:
        sensor_df: DataFrame chứa sensor data, có các cột:
            ['ts', 'temp_c', 'rh_pct', 'soil_moist_pct', 'pressure_hpa']
        api_row: Series chứa API data, có các field:
            ['api_pop', 'api_rain_1h', 'api_temp_c', 'api_rh_pct', 'api_uvi']
        interval_seconds: Khoảng thời gian giữa các bản ghi (300s = 5 phút, 15s = 15 giây)
    
    Returns:
        FeatureVector với 13 features
    """
    if len(sensor_df) < 2:
        # Nếu thiếu dữ liệu, trả về vector zero
        last_ts = pd.to_datetime(sensor_df.iloc[-1]["ts"]) if len(sensor_df) > 0 else pd.Timestamp.now()
        month_enc = cyclical_encode_month(last_ts.month)
        hour_enc = cyclical_encode_hour(last_ts.hour)
        return FeatureVector(
            api_pop=0.0,
            api_rain_1h=0.0,
            pressure_slope_1h=0.0,
            temp_drop_15m=0.0,
            rh_rise_15m=0.0,
            dew_point_diff=0.0,
            temp_bias=0.0,
            soil_moist_smooth=float(sensor_df.iloc[-1]["soil_moist_pct"]) if len(sensor_df) > 0 else 0.0,
            month_sin=month_enc["month_sin"],
            month_cos=month_enc["month_cos"],
            hour_sin=hour_enc["hour_sin"],
            hour_cos=hour_enc["hour_cos"],
            uvi_index=0.0,
        )
    
    # Sort theo thời gian
    sensor_df = sensor_df.sort_values("ts").reset_index(drop=True)
    last = sensor_df.iloc[-1]
    first = sensor_df.iloc[0]
    last_ts = pd.to_datetime(last["ts"])
    
    # Xác định window size dựa trên interval
    if interval_seconds == 15:
        window_1h = WINDOW_1H
        window_15m = WINDOW_15M
        window_soil = WINDOW_SOIL_SMOOTH
    else:  # 5 phút (300s)
        window_1h = WINDOW_1H_5MIN
        window_15m = WINDOW_15M_5MIN
        window_soil = WINDOW_SOIL_SMOOTH_5MIN
    
    # 1. pressure_slope_1h = P_t - P_(t-1h)
    # Nếu có đủ 1h dữ liệu, dùng điểm đầu; nếu không, dùng điểm xa nhất có
    if len(sensor_df) >= window_1h:
        first_1h = sensor_df.iloc[-window_1h]
        pressure_slope_1h = float(last["pressure_hpa"] - first_1h["pressure_hpa"])
    else:
        # Dùng điểm đầu tiên có
        pressure_slope_1h = float(last["pressure_hpa"] - first["pressure_hpa"])
    
    # 2. temp_drop_15m = T_(t-15m) - T_t (nhiệt độ giảm => dương)
    # rh_rise_15m = RH_t - RH_(t-15m) (độ ẩm tăng => dương)
    if len(sensor_df) >= window_15m:
        past_15 = sensor_df.iloc[-window_15m]
        temp_drop_15m = float(past_15["temp_c"] - last["temp_c"])
        rh_rise_15m = float(last["rh_pct"] - past_15["rh_pct"])
    else:
        # Dùng điểm đầu tiên có
        temp_drop_15m = float(first["temp_c"] - last["temp_c"])
        rh_rise_15m = float(last["rh_pct"] - first["rh_pct"])
    
    # 3. soil_moist_smooth = trung bình window_soil mẫu gần nhất
    if len(sensor_df) >= window_soil:
        soil_moist_smooth = float(
            sensor_df["soil_moist_pct"].tail(window_soil).mean()
        )
    else:
        soil_moist_smooth = float(last["soil_moist_pct"])
    
    # 4. Dew point diff (sensor vs api)
    dew_sensor = compute_dew_point(float(last["temp_c"]), float(last["rh_pct"]))
    dew_api = compute_dew_point(
        float(api_row.get("api_temp_c", last["temp_c"])),
        float(api_row.get("api_rh_pct", last["rh_pct"])),
    )
    dew_point_diff = float(dew_sensor - dew_api)
    
    # 5. temp_bias = api_temp - sensor_temp
    temp_bias = float(api_row.get("api_temp_c", last["temp_c"]) - last["temp_c"])
    
    # 6. Cyclical encoding (month, hour)
    month = int(last_ts.month)
    hour = int(last_ts.hour)
    month_enc = cyclical_encode_month(month)
    hour_enc = cyclical_encode_hour(hour)
    
    # 7. API fields
    api_pop = float(api_row.get("api_pop", 0.0))
    api_rain_1h = float(api_row.get("api_rain_1h", 0.0))
    uvi_index = float(api_row.get("api_uvi", 0.0))
    
    return FeatureVector(
        api_pop=api_pop,
        api_rain_1h=api_rain_1h,
        pressure_slope_1h=pressure_slope_1h,
        temp_drop_15m=temp_drop_15m,
        rh_rise_15m=rh_rise_15m,
        dew_point_diff=dew_point_diff,
        temp_bias=temp_bias,
        soil_moist_smooth=soil_moist_smooth,
        month_sin=month_enc["month_sin"],
        month_cos=month_enc["month_cos"],
        hour_sin=hour_enc["hour_sin"],
        hour_cos=hour_enc["hour_cos"],
        uvi_index=uvi_index,
    )


__all__ = [
    "FeatureVector",
    "FEATURE_NAMES",
    "compute_feature_from_window",
    "compute_dew_point",
    "cyclical_encode_month",
    "cyclical_encode_hour",
]

