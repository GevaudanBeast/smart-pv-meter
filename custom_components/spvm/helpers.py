"""Helper functions for SPVM integration."""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

from homeassistant.core import State

from .const import KW_TO_W, UNIT_KW


def to_float(state: State | None, default: float = 0.0) -> float:
    """Convert state to float safely."""
    if state is None or state.state in ("unknown", "unavailable", "none", ""):
        return default
    try:
        return float(str(state.state))
    except (ValueError, TypeError):
        return default


def kw_to_w(value: float, unit_power: str) -> float:
    """Convert kW to W if needed."""
    if unit_power == UNIT_KW:
        return value * KW_TO_W
    return value


def w_to_kw(value: float) -> float:
    """Convert W to kW."""
    return value / KW_TO_W


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5 / 9


class ExponentialMovingAverage:
    """Exponential Moving Average for smoothing."""

    def __init__(self, alpha: float = 0.3) -> None:
        """Initialize EMA."""
        self.alpha = alpha
        self.value: float | None = None

    def update(self, new_value: float) -> float:
        """Update and return smoothed value."""
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

    def reset(self) -> None:
        """Reset EMA."""
        self.value = None


class RollingAverage:
    """Rolling average calculator."""

    def __init__(self, window_size: int = 10) -> None:
        """Initialize rolling average."""
        self.window_size = max(1, window_size)
        self.values: deque[tuple[datetime, float]] = deque(maxlen=window_size)

    def add(self, timestamp: datetime, value: float) -> None:
        """Add a value with timestamp."""
        self.values.append((timestamp, value))

    def get_average(self) -> float | None:
        """Get current average."""
        if not self.values:
            return None
        return sum(v for _, v in self.values) / len(self.values)

    def clear(self) -> None:
        """Clear all values."""
        self.values.clear()


def normalize_value(
    value: float, min_val: float, max_val: float, epsilon: float = 1e-10
) -> float:
    """Normalize value to [0, 1] range."""
    if abs(max_val - min_val) < epsilon:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def calculate_distance(
    point1: dict[str, float], point2: dict[str, float], weights: dict[str, float]
) -> float:
    """Calculate weighted euclidean distance between two points."""
    distance = 0.0
    for key, weight in weights.items():
        if key in point1 and key in point2:
            diff = point1[key] - point2[key]
            distance += weight * (diff ** 2)
    return distance ** 0.5


def get_minutes_of_day(dt: datetime) -> int:
    """Get minutes since midnight."""
    return dt.hour * 60 + dt.minute


def circular_distance(minutes1: int, minutes2: int, period: int = 1440) -> float:
    """Calculate circular distance between two times (in minutes)."""
    diff = abs(minutes1 - minutes2)
    return min(diff, period - diff)


def state_to_float(state: State | None, default: float = 0.0) -> float:
    """Convert state to float safely."""
    if state is None or state.state in ("unknown", "unavailable", "none", ""):
        return default
    try:
        return float(str(state.state))
    except (ValueError, TypeError):
        return default


def convert_to_w(value: float, unit_power: str) -> float:
    """Convert power value to W based on unit."""
    if unit_power == UNIT_KW:
        return value * KW_TO_W
    return value


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def rolling_average(values: list[float], window_size: int) -> float:
    """Calculate rolling average of last window_size values."""
    if not values:
        return 0.0
    window = values[-window_size:] if len(values) >= window_size else values
    return sum(window) / len(window) if window else 0.0


def merge_config_options(data: dict, options: dict) -> dict:
    """Merge config data and options, with options taking precedence."""
    return {**data, **options}


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()
