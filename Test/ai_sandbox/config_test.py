"""
Cấu hình đơn giản cho AI sandbox.

Lưu ý: Đây chỉ là cấu hình TEST (không dùng trực tiếp cho production).
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"


@dataclass
class ThresholdConfig:
    """Ngưỡng quyết định mưa theo mùa (đơn giản hóa cho sandbox)."""

    spring_threshold: float = 0.8  # Tháng 2-4
    summer_threshold: float = 0.5  # Tháng 5-7
    fall_winter_threshold: float = 0.4  # Còn lại


@dataclass
class ModelConfig:
    model_path: Path = MODELS_DIR / "xgb_virtual_rain_test.pkl"
    feature_schema_path: Path = MODELS_DIR / "feature_schema.json"


THRESHOLDS = ThresholdConfig()
MODEL_CFG = ModelConfig()


def ensure_dirs() -> None:
    """Đảm bảo các thư mục cần thiết tồn tại."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "MODELS_DIR",
    "THRESHOLDS",
    "MODEL_CFG",
    "ensure_dirs",
]


