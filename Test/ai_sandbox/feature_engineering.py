"""
Feature engineering cho sandbox Virtual Rain Sensor.

Phần này mô phỏng gần giống các đặc trưng mô tả trong báo cáo:
- pressure_slope_1h
- temp_drop_15m
- rh_rise_15m
- soil_moist_smooth
- dew_point_diff
- temp_bias
- month_sin, month_cos, hour_sin, hour_cos
- api_pop, api_rain_1h, uvi_index

Trong sandbox, ta sinh dữ liệu synthetic nhưng giữ đúng tên & ý nghĩa feature,
để sau này dễ map sang dữ liệu thật.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

import numpy as np
import pandas as pd


SECONDS_15 = 15
WINDOW_1H = int(60 * 60 / SECONDS_15)  # 240 điểm
WINDOW_15M = int(15 * 60 / SECONDS_15)  # 60 điểm
WINDOW_SOIL_SMOOTH = 20  # 5 phút


@dataclass
class FeatureVector:
    """Vector feature 1 mẫu (tương ứng 1 timestamp 15s)."""

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
    rad = 2 * np.pi * (month % 12) / 12.0
    return {
        "month_sin": float(np.sin(rad)),
        "month_cos": float(np.cos(rad)),
    }


def cyclical_encode_hour(hour: int) -> Dict[str, float]:
    rad = 2 * np.pi * (hour % 24) / 24.0
    return {
        "hour_sin": float(np.sin(rad)),
        "hour_cos": float(np.cos(rad)),
    }


def compute_dew_point(temp_c: float, rh_pct: float) -> float:
    """
    Tính điểm sương (Magnus approximation).
    Công thức đơn giản, đủ dùng cho sandbox.
    """

    a = 17.27
    b = 237.7
    gamma = (a * temp_c / (b + temp_c)) + np.log(max(rh_pct, 1e-3) / 100.0)
    return (b * gamma) / (a - gamma)


def compute_feature_from_window(
    sensor_df: pd.DataFrame,
    api_row: pd.Series,
) -> FeatureVector:
    """
    Tính feature từ:
    - sensor_df: DataFrame chứa 240 điểm (1h) sensor gần nhất, có các cột:
        ['timestamp', 'temp_c', 'rh_pct', 'soil_moist_pct', 'pressure_hpa']
    - api_row: 1 row chứa các trường API:
        ['api_pop', 'api_rain_1h', 'api_temp_c', 'api_rh_pct', 'api_uvi']
    """

    if len(sensor_df) < WINDOW_1H:
        # Nếu thiếu dữ liệu, fill bằng giá trị trung tính
        # (sandbox: chấp nhận đơn giản)
        sensor_df = sensor_df.copy()

    # Giả sử sensor_df đã sort theo thời gian, index tăng dần
    last = sensor_df.iloc[-1]
    last_ts = pd.to_datetime(last["timestamp"])

    # 1. pressure_slope_1h ~ P_t - P_(t-1h)
    first = sensor_df.iloc[0]
    pressure_slope_1h = float(last["pressure_hpa"] - first["pressure_hpa"])

    # 2. temp_drop_15m ~ T_(t-15m) - T_t (giảm => dương)
    if len(sensor_df) >= WINDOW_15M:
        past_15 = sensor_df.iloc[-WINDOW_15M]
        temp_drop_15m = float(past_15["temp_c"] - last["temp_c"])
        rh_rise_15m = float(last["rh_pct"] - past_15["rh_pct"])
    else:
        temp_drop_15m = 0.0
        rh_rise_15m = 0.0

    # 3. soil_moist_smooth ~ trung bình 20 mẫu gần nhất
    soil_moist_smooth = float(
        sensor_df["soil_moist_pct"].tail(WINDOW_SOIL_SMOOTH).mean()
    )

    # 4. Dew point diff (sensor vs api)
    dew_sensor = compute_dew_point(float(last["temp_c"]), float(last["rh_pct"]))
    dew_api = compute_dew_point(
        float(api_row["api_temp_c"]),
        float(api_row["api_rh_pct"]),
    )
    dew_point_diff = float(dew_sensor - dew_api)

    # 5. temp_bias (api vs sensor)
    temp_bias = float(api_row["api_temp_c"] - last["temp_c"])

    # 6. Thời gian (month, hour) -> cyclical
    month = int(last_ts.month)
    hour = int(last_ts.hour)
    month_enc = cyclical_encode_month(month)
    hour_enc = cyclical_encode_hour(hour)

    # 7. API fields
    api_pop = float(api_row["api_pop"])
    api_rain_1h = float(api_row["api_rain_1h"])
    uvi_index = float(api_row["api_uvi"])

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


