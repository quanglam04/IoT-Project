"""
Decision logic cho sandbox Virtual Rain Sensor.

Nhiệm vụ:
- Nhận xác suất mưa hợp nhất (rain_prob_fusion) + các feature quan trọng.
- Áp dụng logic 4 mùa đơn giản (theo month).
- Sinh ra 2 JSON:
  - Output 1: virtual_rain_sensor + control + ui_message + telemetry_snapshot.
  - Output 2: scheduler đơn giản cho 4 giờ tới (timeline ngắn).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from .config_test import THRESHOLDS


@dataclass
class NowcastContext:
    timestamp: datetime
    month: int
    soil_moisture: float
    pressure_trend: float
    api_weather_code: int
    api_pop: float
    api_rain_1h: float


def _get_seasonal_threshold(month: int) -> float:
    if 2 <= month <= 4:
        return THRESHOLDS.spring_threshold
    if 5 <= month <= 7:
        return THRESHOLDS.summer_threshold
    return THRESHOLDS.fall_winter_threshold


def build_output_1(
    ctx: NowcastContext,
    rain_prob_fusion: float,
) -> Dict[str, Any]:
    """
    Sinh JSON Output 1 giống format trong yêu cầu.
    """

    threshold = _get_seasonal_threshold(ctx.month)
    is_raining = rain_prob_fusion >= threshold

    # Cường độ mưa tương đối đơn giản hóa
    if ctx.api_rain_1h < 1.0:
        rain_intensity = "LIGHT"
    elif ctx.api_rain_1h < 5.0:
        rain_intensity = "MODERATE"
    else:
        rain_intensity = "HEAVY"

    # Nguồn phát hiện
    if ctx.pressure_trend <= -2.0 and ctx.api_pop < 0.7:
        detection_source = "PRESSURE_DROP"
    elif ctx.pressure_trend > -0.5 and ctx.api_pop >= 0.7:
        detection_source = "API"
    else:
        detection_source = "HYBRID"

    # Quyết định điều khiển đơn giản hóa cho sandbox
    if ctx.pressure_trend <= -2.0:
        pump_command = "OFF"
        action_code = "EMERGENCY_STOP"
        override_scheduler = True
        title = "Đã ngắt bơm khẩn cấp!"
        body = "Áp suất tụt nhanh, nguy cơ dông lốc – ưu tiên bảo vệ thiết bị."
        icon_code = "STORM_ALERT"
    elif is_raining:
        pump_command = "OFF"
        action_code = "SKIP_WATERING_RAIN"
        override_scheduler = False
        title = "Hoãn tưới do mưa"
        body = "AI dự báo mưa trong giờ tới, hệ thống tạm hoãn tưới để tiết kiệm nước."
        icon_code = "RAIN_ALERT"
    elif ctx.soil_moisture < 35.0:
        pump_command = "ON"
        action_code = "WATER_NOW"
        override_scheduler = False
        title = "Bắt đầu tưới"
        body = "Đất đang khô, không có mưa đáng kể – hệ thống bắt đầu tưới."
        icon_code = "WATER_ON"
    else:
        pump_command = "OFF"
        action_code = "IDLE_OK"
        override_scheduler = False
        title = "Đất đủ ẩm"
        body = "Không mưa lớn, đất vẫn đủ ẩm – chưa cần tưới."
        icon_code = "IDLE"

    output = {
        "meta": {
            "device_id": "esp32_garden_01",
            "timestamp": ctx.timestamp.replace(tzinfo=timezone.utc).isoformat(),
            "system_mode": "FUSION_OPTIMAL",
            "api_status": "ONLINE",
        },
        "virtual_rain_sensor": {
            "is_raining": bool(is_raining),
            "rain_prob_fusion": round(float(rain_prob_fusion), 3),
            "rain_intensity": rain_intensity,
            "predicted_mm": round(float(ctx.api_rain_1h), 2),
            "detection_source": detection_source,
        },
        "control": {
            "pump_command": pump_command,
            "action_code": action_code,
            "override_scheduler": bool(override_scheduler),
        },
        "ui_message": {
            "title": title,
            "body": body,
            "icon_code": icon_code,
        },
        "telemetry_snapshot": {
            "soil_moisture": round(float(ctx.soil_moisture), 2),
            "pressure_trend": round(float(ctx.pressure_trend), 2),
            "api_weather_code": int(ctx.api_weather_code),
        },
    }

    return output


def build_output_2(
    now: datetime,
    advisory_text: str,
) -> Dict[str, Any]:
    """
    Sinh JSON Output 2 (scheduler đơn giản) cho 4 giờ tới.

    Sandbox: chỉ tạo timeline cho "Hôm nay" với 2 slot mẫu.
    Khi tích hợp thật, phần này sẽ được thay thế bằng logic cân bằng nước.
    """

    generated_at = now.replace(tzinfo=timezone.utc)
    valid_until = generated_at + timedelta(hours=4)

    today_date = generated_at.date().isoformat()
    h1 = (generated_at + timedelta(hours=1)).strftime("%H:%M")
    h3 = (generated_at + timedelta(hours=3)).strftime("%H:%M")

    output = {
        "meta": {
            "device_id": "esp32_garden_01",
            "generated_at": generated_at.isoformat(),
            "valid_until": valid_until.isoformat(),
        },
        "summary_advisory": advisory_text,
        "timeline": [
            {
                "day": "Hôm nay",
                "date": today_date,
                "slots": [
                    {
                        "time": h1,
                        "action": "SKIP",
                        "reason": "Dự báo có mưa rào nhẹ trong giờ tới (sandbox).",
                    },
                    {
                        "time": h3,
                        "action": "WATER",
                        "duration_min": 15,
                        "reason": "Bù ẩm sau mưa (sandbox).",
                    },
                ],
            }
        ],
    }

    return output


__all__ = [
    "NowcastContext",
    "build_output_1",
    "build_output_2",
]


