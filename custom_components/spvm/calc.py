"""Pure calculations for Smart PV Meter (no Home Assistant import)."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone

# Last PV value is reused at most this long when the PV sensor is unavailable.
PV_FALLBACK_MAX_AGE_S = 300


def _parse_utc(label: str) -> datetime:
    return datetime.strptime(label, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)


def interpolate_hourly_mean(
    times: list[str], values: list[float | None], now: datetime
) -> float | None:
    """Value at `now` from Open-Meteo hourly radiation.

    An hourly radiation value labelled T is the mean over [T - 1 h, T]: it is
    placed at the middle of that hour (T - 30 min), then values are linearly
    interpolated. Before the first point or after the last one, the nearest
    value is returned. Missing values (None) are skipped.
    """
    points = [
        (_parse_utc(t) - timedelta(minutes=30), float(v))
        for t, v in zip(times, values)
        if v is not None
    ]
    if not points:
        return None
    if now <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t0 <= now <= t1:
            span = (t1 - t0).total_seconds()
            ratio = (now - t0).total_seconds() / span if span else 0.0
            return v0 + (v1 - v0) * ratio
    return points[-1][1]


def pv_with_fallback(
    pv_w: float | None,
    last_pv_w: float | None,
    last_pv_time: datetime | None,
    now: datetime,
    max_age_s: float = PV_FALLBACK_MAX_AGE_S,
) -> tuple[float | None, bool]:
    """Return (pv value to use, fallback used).

    A fresh reading wins. Otherwise the last value is reused only if it is
    younger than max_age_s; after that the PV value is unknown (None).
    """
    if pv_w is not None:
        return pv_w, False
    if last_pv_w is None or last_pv_time is None:
        return None, True
    if (now - last_pv_time).total_seconds() > max_age_s:
        return None, True
    return last_pv_w, True


def surplus_net(pv_w: float, house_w: float, grid_w: float | None, reserve_w: float) -> float:
    """v0.7.7 surplus rule, unchanged: max(max(pv - house, export) - reserve, 0)."""
    surplus = pv_w - house_w
    if grid_w is not None:
        surplus = max(surplus, max(-grid_w, 0.0))
    return max(surplus - float(reserve_w), 0.0)


class RollingMean:
    """Time-based moving average over `window_s` seconds."""

    def __init__(self, window_s: float) -> None:
        self.window_s = float(window_s)
        self._items: deque[tuple[datetime, float]] = deque()

    def add(self, when: datetime, value: float) -> None:
        self._items.append((when, float(value)))
        limit = when - timedelta(seconds=self.window_s)
        while len(self._items) > 1 and self._items[0][0] < limit:
            self._items.popleft()
        if self.window_s <= 0:
            while len(self._items) > 1:
                self._items.popleft()

    def mean(self) -> float | None:
        if not self._items:
            return None
        return sum(v for _, v in self._items) / len(self._items)
