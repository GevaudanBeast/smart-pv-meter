"""Expected production calculator using k-NN algorithm."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import time
from typing import Any

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import HISTORY_DAYS, KW_TO_W, TIMEZONE, UNIT_KW
from .helpers import (
    calculate_distance,
    circular_distance,
    get_minutes_of_day,
    normalize_value,
    to_float,
)

_LOGGER = logging.getLogger(__name__)


class ExpectedProductionCalculator:
    """Calculate expected PV production using k-NN."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize calculator."""
        self.hass = hass
        self.config = config
        self._cache: dict[str, Any] = {}
        
        # Use dt_util instead of pytz to avoid blocking calls
        try:
            self._timezone = dt_util.get_time_zone(TIMEZONE)
            _LOGGER.debug("Timezone loaded: %s", TIMEZONE)
        except Exception as err:
            _LOGGER.warning(
                "Could not load timezone %s: %s - using default",
                TIMEZONE,
                err
            )
            self._timezone = dt_util.DEFAULT_TIME_ZONE

    async def async_calculate(self) -> dict[str, Any]:
        """Calculate expected production with timeout protection."""
        _LOGGER.debug("Starting expected production calculation...")
        calc_start = time.time()
        
        try:
            # Get current conditions
            current = self._get_current_conditions()
            
            if not current:
                _LOGGER.warning("Cannot get current conditions")
                return self._get_empty_result()
            
            _LOGGER.debug(
                "Current conditions: elevation=%.1f°, minutes=%d, lux=%s, temp=%s",
                current.get("elevation", 0),
                current.get("minutes_of_day", 0),
                current.get("lux"),
                current.get("temp"),
            )

            # Get historical data with timeout
            _LOGGER.info("Fetching historical data (timeout: 90s)...")
            try:
                async with asyncio.timeout(90):  # 90 seconds max
                    historical_data = await self._get_historical_data()
                    
                fetch_elapsed = time.time() - calc_start
                _LOGGER.info(
                    "Historical data fetched in %.2fs: %d points",
                    fetch_elapsed,
                    len(historical_data)
                )
                
            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Historical data fetch TIMEOUT after 90s - using theoretical fallback"
                )
                return self._fallback_level_4_theoretical(current)
            
            if not historical_data:
                _LOGGER.warning("No historical data available - using fallback")
                return self._get_time_only_fallback(current)

            # Calculate k-NN
            _LOGGER.debug("Calculating k-NN prediction...")
            result = self._calculate_knn(current, historical_data)
            
            total_elapsed = time.time() - calc_start
            _LOGGER.info(
                "Expected calculation completed in %.2fs: method=%s, expected=%.1fW",
                total_elapsed,
                result.get("method"),
                result.get("expected_w", 0)
            )
            
            return result

        except Exception as err:
            _LOGGER.error(
                "Error calculating expected production: %s",
                err,
                exc_info=True
            )
            return self._get_empty_result()

    def _get_current_conditions(self) -> dict[str, Any] | None:
        """Get current weather and time conditions."""
        now = dt_util.now(self._timezone)
        
        # Get sun elevation - make it optional
        sun_state = self.hass.states.get("sun.sun")
        elevation = 0.0
        
        if sun_state is None:
            _LOGGER.debug("Sun entity not available, using elevation=0")
        else:
            try:
                elevation = float(sun_state.attributes.get("elevation", 0))
            except (ValueError, TypeError):
                _LOGGER.debug("Could not read sun elevation, using 0")
                elevation = 0.0

        # Get sensors
        lux = None
        if self.config.get("lux_sensor"):
            lux_state = self.hass.states.get(self.config["lux_sensor"])
            lux = to_float(lux_state, None)

        temp = None
        if self.config.get("temp_sensor"):
            temp_state = self.hass.states.get(self.config["temp_sensor"])
            temp = to_float(temp_state, None)

        hum = None
        if self.config.get("hum_sensor"):
            hum_state = self.hass.states.get(self.config["hum_sensor"])
            hum = to_float(hum_state, None)
        
        return {
            "timestamp": now,
            "minutes_of_day": get_minutes_of_day(now),
            "elevation": elevation,
            "lux": lux,
            "temp": temp,
            "hum": hum,
        }

    async def _get_historical_data(self) -> list[dict[str, Any]]:
        """Get historical data from recorder."""
        # Check cache
        if "historical_data" in self._cache:
            cache_time = self._cache.get("cache_time")
            if cache_time:
                cache_age_seconds = (dt_util.now() - cache_time).total_seconds()
                if cache_age_seconds < 3600:  # 1 hour cache
                    _LOGGER.debug(
                        "Using cached historical data (age: %.1fmin)",
                        cache_age_seconds / 60
                    )
                    return self._cache["historical_data"]
                else:
                    _LOGGER.debug(
                        "Cache expired (age: %.1fmin), reloading",
                        cache_age_seconds / 60
                    )

        end_time = dt_util.now()
        start_time = end_time - timedelta(days=HISTORY_DAYS)
        
        _LOGGER.info(
            "Querying recorder: %s to %s (%d days)",
            start_time.strftime("%Y-%m-%d"),
            end_time.strftime("%Y-%m-%d"),
            HISTORY_DAYS
        )

        try:
            # Get PV history
            pv_entity = str(self.config["pv_sensor"])
            _LOGGER.debug("Fetching PV states for %s", pv_entity)
            
            pv_states = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period,
                self.hass,
                start_time,
                end_time,
                pv_entity,
            )

            # Get sun history
            _LOGGER.debug("Fetching sun states")
            sun_states = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period,
                self.hass,
                start_time,
                end_time,
                "sun.sun",
            )

            # Get weather sensors history if configured
            lux_states = {}
            temp_states = {}
            hum_states = {}
            
            if self.config.get("lux_sensor"):
                _LOGGER.debug("Fetching lux states")
                lux_states = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    start_time,
                    end_time,
                    str(self.config["lux_sensor"]),
                )
            
            if self.config.get("temp_sensor"):
                _LOGGER.debug("Fetching temperature states")
                temp_states = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    start_time,
                    end_time,
                    str(self.config["temp_sensor"]),
                )
            
            if self.config.get("hum_sensor"):
                _LOGGER.debug("Fetching humidity states")
                hum_states = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    start_time,
                    end_time,
                    str(self.config["hum_sensor"]),
                )

            # Combine all states
            combined_states = {
                **pv_states,
                **sun_states,
                **lux_states,
                **temp_states,
                **hum_states,
            }
            
            _LOGGER.debug("Processing historical states...")

            # Process data
            data_points = self._process_historical_states(combined_states)
            
            # Cache results
            self._cache["historical_data"] = data_points
            self._cache["cache_time"] = dt_util.now()
            
            _LOGGER.info("Loaded and cached %d historical data points", len(data_points))
            
            return data_points

        except Exception as err:
            _LOGGER.error("Error fetching historical data: %s", err, exc_info=True)
            return []

    def _process_historical_states(
        self, historical_states: dict[str, list]
    ) -> list[dict[str, Any]]:
        """Process historical states into data points."""
        data_points = []
        
        # Get PV states - historical_states is a dict with entity_id as key
        pv_entity = self.config["pv_sensor"]
        pv_states = historical_states.get(pv_entity, [])
        
        if not pv_states:
            _LOGGER.warning("No PV states found for entity %s", pv_entity)
            return []
        
        _LOGGER.debug("Processing %d PV states...", len(pv_states))
        skipped = 0
        
        for pv_state in pv_states:
            if pv_state.state in ("unknown", "unavailable", "none", None):
                skipped += 1
                continue
                
            try:
                pv_value = float(pv_state.state)
                
                # Convert kW to W if needed
                if self.config.get("unit_power") == UNIT_KW:
                    pv_value *= KW_TO_W
                
                if pv_value < 0:
                    skipped += 1
                    continue
                
                # Get timestamp - handle timezone safely
                timestamp = pv_state.last_changed
                
                # Ensure timezone is set
                if timestamp.tzinfo is None:
                    if self._timezone:
                        timestamp = self._timezone.localize(timestamp)
                    else:
                        timestamp = dt_util.as_local(timestamp)
                else:
                    # Convert to our timezone
                    target_tz = self._timezone or dt_util.DEFAULT_TIME_ZONE
                    timestamp = timestamp.astimezone(target_tz)
                
                # Create data point
                point = {
                    "timestamp": timestamp,
                    "minutes_of_day": get_minutes_of_day(timestamp),
                    "pv_w": pv_value,
                }
                
                # Add weather data (find closest)
                point.update(self._get_closest_weather(timestamp, historical_states))
                
                data_points.append(point)
                
            except (ValueError, TypeError) as err:
                _LOGGER.debug("Skipping invalid PV state: %s", err)
                skipped += 1
                continue
        
        _LOGGER.debug(
            "Processed %d valid points (skipped %d invalid)",
            len(data_points),
            skipped
        )
        
        return data_points

    def _get_closest_weather(
        self, timestamp: datetime, historical_states: dict[str, list]
    ) -> dict[str, float | None]:
        """Get closest weather data for timestamp."""
        result = {
            "elevation": None,
            "lux": None,
            "temp": None,
            "hum": None,
        }
        
        # Sun elevation
        sun_states = historical_states.get("sun.sun", [])
        closest_sun = self._find_closest_state(sun_states, timestamp)
        if closest_sun:
            try:
                result["elevation"] = float(
                    closest_sun.attributes.get("elevation", 0)
                )
            except (ValueError, TypeError):
                pass
        
        # Lux
        if self.config.get("lux_sensor"):
            lux_states = historical_states.get(self.config["lux_sensor"], [])
            closest_lux = self._find_closest_state(lux_states, timestamp)
            if closest_lux:
                result["lux"] = to_float(closest_lux, None)
        
        # Temperature
        if self.config.get("temp_sensor"):
            temp_states = historical_states.get(self.config["temp_sensor"], [])
            closest_temp = self._find_closest_state(temp_states, timestamp)
            if closest_temp:
                result["temp"] = to_float(closest_temp, None)
        
        # Humidity
        if self.config.get("hum_sensor"):
            hum_states = historical_states.get(self.config["hum_sensor"], [])
            closest_hum = self._find_closest_state(hum_states, timestamp)
            if closest_hum:
                result["hum"] = to_float(closest_hum, None)
        
        return result

    @staticmethod
    def _find_closest_state(states: list, target_time: datetime):
        """Find state closest to target time."""
        if not states:
            return None
        
        closest = None
        min_diff = float("inf")
        
        for state in states:
            diff = abs((state.last_changed - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = state
        
        return closest

    def _calculate_knn(
        self, current: dict[str, Any], historical_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate k-NN expected production."""
        k = self.config.get("k", 5)
        window_min = self.config.get("window_min", 30)
        window_max = self.config.get("window_max", 90)
        
        _LOGGER.debug(
            "k-NN: k=%d, time_window=%d-%dmin, %d historical points",
            k,
            window_min,
            window_max,
            len(historical_data)
        )
        
        # Filter by time window
        candidates = self._filter_by_time_window(
            historical_data, current["minutes_of_day"], window_min, window_max
        )
        
        _LOGGER.debug("After time filter: %d candidates", len(candidates))
        
        if not candidates:
            _LOGGER.warning("No candidates in time window, using fallback")
            return self._get_time_only_fallback(current)
        
        # Filter by sun elevation (only if sun.sun is available)
        if current["elevation"] != 0.0:
            candidates_before = len(candidates)
            candidates = self._filter_by_elevation(
                candidates, current["elevation"], threshold=15.0
            )
            
            _LOGGER.debug(
                "After elevation filter: %d candidates (removed %d)",
                len(candidates),
                candidates_before - len(candidates)
            )
            
            if not candidates:
                _LOGGER.info(
                    "No candidates after elevation filter (from %d), using fallback. "
                    "This is normal at night or during weather changes.",
                    candidates_before
                )
                return self._get_time_only_fallback(current)
        else:
            _LOGGER.debug("Sun elevation = 0, skipping elevation filter")
        
        # Calculate normalization ranges
        norm_ranges = self._calculate_normalization_ranges(candidates)
        
        # Calculate distances
        distances = []
        for candidate in candidates:
            dist = self._calculate_weighted_distance(
                current, candidate, norm_ranges
            )
            distances.append((dist, candidate))
        
        # Sort by distance and take k nearest
        distances.sort(key=lambda x: x[0])
        neighbors = distances[:k]
        
        _LOGGER.debug(
            "Found %d neighbors, distances: %s",
            len(neighbors),
            [f"{d:.3f}" for d, _ in neighbors[:3]]
        )
        
        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        
        for dist, neighbor in neighbors:
            # Inverse distance weighting
            weight = 1.0 / (dist + 0.001)  # Add small epsilon
            weighted_sum += weight * neighbor["pv_w"]
            total_weight += weight
        
        expected_w = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Build result
        return {
            "expected_w": max(0.0, expected_w),
            "expected_kw": max(0.0, expected_w / KW_TO_W),
            "method": "knn",
            "k": k,
            "neighbors": len(neighbors),
            "candidates": len(candidates),
            "samples_total": len(historical_data),
            "window_min": window_min,
            "window_max": window_max,
            "weights": {
                "lux": self.config.get("weight_lux", 0.4),
                "temp": self.config.get("weight_temp", 0.2),
                "hum": self.config.get("weight_hum", 0.1),
                "elev": self.config.get("weight_elev", 0.3),
            },
            "neighbor_values": [n["pv_w"] for _, n in neighbors],
            "neighbor_distances": [d for d, _ in neighbors],
        }

    def _filter_by_time_window(
        self, data: list[dict], target_minutes: int, window_min: int, window_max: int
    ) -> list[dict]:
        """Filter data by time window."""
        result = []
        for point in data:
            dist = circular_distance(point["minutes_of_day"], target_minutes)
            if window_min <= dist <= window_max:
                result.append(point)
        return result

    def _filter_by_elevation(
        self, data: list[dict], target_elevation: float, threshold: float = 10.0
    ) -> list[dict]:
        """Filter by sun elevation."""
        result = []
        for point in data:
            if point.get("elevation") is None:
                continue
            if abs(point["elevation"] - target_elevation) <= threshold:
                result.append(point)
        return result

    def _calculate_normalization_ranges(
        self, data: list[dict]
    ) -> dict[str, tuple[float, float]]:
        """Calculate min/max ranges for normalization."""
        ranges = {}
        
        for key in ["lux", "temp", "hum", "elevation"]:
            values = [p[key] for p in data if p.get(key) is not None]
            if values:
                ranges[key] = (min(values), max(values))
            else:
                ranges[key] = (0.0, 1.0)
        
        return ranges

    def _calculate_weighted_distance(
        self,
        current: dict[str, Any],
        candidate: dict[str, Any],
        norm_ranges: dict[str, tuple[float, float]],
    ) -> float:
        """Calculate weighted distance."""
        weights = {
            "lux": self.config.get("weight_lux", 0.4),
            "temp": self.config.get("weight_temp", 0.2),
            "hum": self.config.get("weight_hum", 0.1),
            "elev": self.config.get("weight_elev", 0.3),
        }
        
        distance = 0.0
        
        for key, weight in weights.items():
            if current.get(key) is None or candidate.get(key) is None:
                continue
            
            min_val, max_val = norm_ranges.get(key, (0, 1))
            norm_current = normalize_value(current[key], min_val, max_val)
            norm_candidate = normalize_value(candidate[key], min_val, max_val)
            
            diff = norm_current - norm_candidate
            distance += weight * (diff ** 2)
        
        return distance ** 0.5

    def _get_time_only_fallback(self, current: dict[str, Any]) -> dict[str, Any]:
        """Fallback: average of same time ±120min with elevation filter."""
        _LOGGER.info("Using time-only fallback")
        
        if "historical_data" not in self._cache:
            _LOGGER.warning("No cached data for fallback")
            return self._fallback_level_4_theoretical(current)
        
        historical_data = self._cache["historical_data"]
        target_minutes = current["minutes_of_day"]
        target_elevation = current["elevation"]
        
        # Filter by time window (±120 minutes)
        candidates = self._filter_by_time_window(
            historical_data, target_minutes, 0, 120
        )
        
        if not candidates:
            _LOGGER.warning("No candidates in expanded time window")
            return self._fallback_level_4_theoretical(current)
        
        # Filter by elevation
        candidates = self._filter_by_elevation(candidates, target_elevation, 15.0)
        
        if not candidates:
            _LOGGER.warning("No candidates after elevation filter in fallback")
            return self._fallback_level_4_theoretical(current)
        
        # Simple average
        avg_pv = sum(c["pv_w"] for c in candidates) / len(candidates)
        
        _LOGGER.info(
            "Time-only fallback: %d samples, avg=%.1fW",
            len(candidates),
            avg_pv
        )
        
        return {
            "expected_w": max(0.0, avg_pv),
            "expected_kw": max(0.0, avg_pv / KW_TO_W),
            "method": "time_only_fallback",
            "samples": len(candidates),
            "samples_total": len(historical_data),
        }

    def _fallback_level_4_theoretical(
        self, 
        current: dict[str, Any]
    ) -> dict[str, Any]:
        """Fallback: theoretical capacity based on sun elevation."""
        elevation = current.get("elevation", 0)
        
        _LOGGER.warning(
            "Using theoretical capacity fallback (elevation=%.1f°)",
            elevation
        )
        
        if elevation <= 0:
            theoretical_w = 0.0
        else:
            # sin(elevation) gives a good proxy for irradiance
            import math
            elevation_rad = math.radians(elevation)
            irradiance_factor = math.sin(elevation_rad)
            
            # Performance factor (panel efficiency + losses)
            performance_factor = 0.75
            
            # Get cap from config or use default
            cap_max_w = self.config.get("cap_max_w", 3000)
            
            theoretical_w = cap_max_w * irradiance_factor * performance_factor
        
        return {
            "expected_w": max(0.0, theoretical_w),
            "expected_kw": max(0.0, theoretical_w / KW_TO_W),
            "method": "theoretical_capacity",
            "elevation": elevation,
            "samples": 0,
            "note": "No historical data - using theoretical model",
            "warning": "Install will improve accuracy as historical data accumulates",
        }

    def _get_empty_result(self) -> dict[str, Any]:
        """Get empty result (error state)."""
        _LOGGER.error("Returning empty result (error state)")
        return {
            "expected_w": 0.0,
            "expected_kw": 0.0,
            "method": "error",
            "samples": 0,
            "error": True,
        }

    def reset_cache(self) -> None:
        """Reset cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        _LOGGER.info("Calculator cache cleared (%d items removed)", cache_size)
