"""Expected production calculator using k-NN algorithm."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
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

    async def async_calculate(self) -> dict[str, Any]:
        """Calculate expected production."""
        try:
            # Get current conditions
            current = self._get_current_conditions()
            
            if not current:
                _LOGGER.warning("Cannot get current conditions")
                return self._get_empty_result()

            # Get historical data
            historical_data = await self._get_historical_data()
            
            if not historical_data:
                _LOGGER.warning("No historical data available")
                return self._get_time_only_fallback(current)

            # Calculate k-NN
            result = self._calculate_knn(current, historical_data)
            
            return result

        except Exception as err:
            _LOGGER.error("Error calculating expected production: %s", err)
            return self._get_empty_result()

    def _get_current_conditions(self) -> dict[str, Any] | None:
        """Get current weather and time conditions."""
        # Use Home Assistant's local time
        now = dt_util.now()
        
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
            if cache_time and (dt_util.now() - cache_time).seconds < 3600:
                return self._cache["historical_data"]

        end_time = dt_util.now()
        start_time = end_time - timedelta(days=HISTORY_DAYS)

        try:
            # Get PV history
            pv_entity = str(self.config["pv_sensor"])
            pv_states = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period,
                self.hass,
                start_time,
                end_time,
                pv_entity,
            )

            # Get sun history
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
                lux_states = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    start_time,
                    end_time,
                    str(self.config["lux_sensor"]),
                )
            
            if self.config.get("temp_sensor"):
                temp_states = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    start_time,
                    end_time,
                    str(self.config["temp_sensor"]),
                )
            
            if self.config.get("hum_sensor"):
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

            # Process data
            data_points = self._process_historical_states(combined_states)
            
            # Cache results
            self._cache["historical_data"] = data_points
            self._cache["cache_time"] = dt_util.now()
            
            _LOGGER.debug("Loaded %d historical data points", len(data_points))
            
            return data_points

        except Exception as err:
            _LOGGER.error("Error fetching historical data: %s", err)
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
        
        for pv_state in pv_states:
            if pv_state.state in ("unknown", "unavailable", "none", None):
                continue
                
            try:
                pv_value = float(pv_state.state)
                
                # Convert kW to W if needed
                if self.config.get("unit_power") == UNIT_KW:
                    pv_value *= KW_TO_W
                
                if pv_value < 0:
                    continue
                
                # Get timestamp
                timestamp = pv_state.last_changed
                # Use dt_util for timezone handling
                timestamp = dt_util.as_local(timestamp)
                
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
                continue
        
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
        
        # Filter by time window
        candidates = self._filter_by_time_window(
            historical_data, current["minutes_of_day"], window_min, window_max
        )
        
        if not candidates:
            _LOGGER.info(
                "No candidates in time window, using fallback. "
                "This is normal during night or when historical data is limited."
            )
            return self._get_time_only_fallback(current)
        
        # Filter by sun elevation (only if sun.sun is available)
        if current["elevation"] != 0.0:
            candidates_before = len(candidates)
            candidates = self._filter_by_elevation(
                candidates, current["elevation"], threshold=15.0
            )
            
            if not candidates:
                _LOGGER.info(
                    "No candidates after elevation filter (from %d), using fallback. "
                    "This is normal at night or during weather changes.",
                    candidates_before
                )
                return self._get_time_only_fallback(current)
        else:
            _LOGGER.debug("Sun elevation not available, skipping elevation filter")
        
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
        """Fallback: average of same time Ã‚Â±120min with elevation filter."""
        _LOGGER.info("Using time-only fallback")
        
        if "historical_data" not in self._cache:
            return self._get_empty_result()
        
        historical_data = self._cache["historical_data"]
        target_minutes = current["minutes_of_day"]
        target_elevation = current["elevation"]
        
        # Filter by time window (Ã‚Â±120 minutes)
        candidates = self._filter_by_time_window(
            historical_data, target_minutes, 0, 120
        )
        
        if not candidates:
            return self._get_empty_result()
        
        # Filter by elevation
        candidates = self._filter_by_elevation(candidates, target_elevation, 15.0)
        
        if not candidates:
            return self._get_empty_result()
        
        # Simple average
        avg_pv = sum(c["pv_w"] for c in candidates) / len(candidates)
        
        return {
            "expected_w": max(0.0, avg_pv),
            "expected_kw": max(0.0, avg_pv / KW_TO_W),
            "method": "time_only_fallback",
            "samples": len(candidates),
            "samples_total": len(historical_data),
        }

    def _get_empty_result(self) -> dict[str, Any]:
        """Get empty result."""
        return {
            "expected_w": 0.0,
            "expected_kw": 0.0,
            "method": "none",
            "samples": 0,
        }

    def reset_cache(self) -> None:
        """Reset cache."""
        self._cache.clear()
        _LOGGER.debug("Calculator cache cleared")
