from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional, Union, Dict

from homeassistant.core import HomeAssistant, State
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    # inputs
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    # units & defaults
    CONF_UNIT_POWER, CONF_UNIT_TEMP, DEF_UNIT_POWER, DEF_UNIT_TEMP, UNIT_W, UNIT_KW, KW_TO_W,
    # reserve / caps / ageing
    CONF_RESERVE_W, DEF_RESERVE_W, CONF_CAP_MAX_W, DEF_CAP_MAX_W,
    CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT,
    # timing
    CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL,
    CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW,
    # labels
    ATTR_MODEL_TYPE, ATTR_SOURCE, ATTR_DEGRADATION_PCT, ATTR_NOTE, NOTE_SOLAR_MODEL,
)

_LOGGER = logging.getLogger(__name__)
Number = Union[float, int]


@dataclass
class SPVMData:
    expected_w: float
    attrs: Dict[str, Any]


def _safe_float(state: Optional[State]) -> Optional[float]:
    if not state or state.state in (None, "", "unknown", "unavailable"):
        return None
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return None


class SPVMCoordinator(DataUpdateCoordinator[SPVMData]):
    """Compute expected solar production (minimal v0.6.0)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        data = {**(entry.data or {}), **(entry.options or {})}

        # Required
        self.pv_entity: Optional[str] = data.get(CONF_PV_SENSOR)
        self.house_entity: Optional[str] = data.get(CONF_HOUSE_SENSOR)
        if not self.pv_entity or not self.house_entity:
            raise HomeAssistantError("SPVM: pv_sensor and house_sensor are required.")

        # Optional inputs
        self.grid_entity: Optional[str] = data.get(CONF_GRID_POWER_SENSOR)
        self.batt_entity: Optional[str] = data.get(CONF_BATTERY_SENSOR)
        self.lux_entity: Optional[str] = data.get(CONF_LUX_SENSOR)
        self.temp_entity: Optional[str] = data.get(CONF_TEMP_SENSOR)
        self.hum_entity: Optional[str] = data.get(CONF_HUM_SENSOR)
        self.cloud_entity: Optional[str] = data.get(CONF_CLOUD_SENSOR)

        # Units
        self.unit_power: str = data.get(CONF_UNIT_POWER, DEF_UNIT_POWER)
        self.unit_temp: str = data.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP)

        # Behaviour
        self.reserve_w: Number = data.get(CONF_RESERVE_W, DEF_RESERVE_W)
        self.cap_max_w: Number = data.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W)
        self.degradation_pct: Number = data.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)

        # Timing
        self.update_interval_s: int = int(data.get(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL))
        self.smoothing_window_s: int = int(data.get(CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW))

        super().__init__(
            hass,
            logger=_LOGGER,  # <- logger standard, pas d'adapter
            name=f"{DOMAIN}-coordinator",
            update_interval=timedelta(seconds=self.update_interval_s),
        )

    async def _async_update_data(self) -> SPVMData:
        """Compute expected production (W) with simple corrections."""

        # Read current states
        pv = _safe_float(self.hass.states.get(self.pv_entity))
        house = _safe_float(self.hass.states.get(self.house_entity))
        grid = _safe_float(self.hass.states.get(self.grid_entity)) if self.grid_entity else None
        batt = _safe_float(self.hass.states.get(self.batt_entity)) if self.batt_entity else None
        lux = _safe_float(self.hass.states.get(self.lux_entity)) if self.lux_entity else None
        temp = _safe_float(self.hass.states.get(self.temp_entity)) if self.temp_entity else None
        hum = _safe_float(self.hass.states.get(self.hum_entity)) if self.hum_entity else None
        cloud = _safe_float(self.hass.states.get(self.cloud_entity)) if self.cloud_entity else None

        if pv is None:
            raise UpdateFailed("pv_sensor has no numeric state")

        # Convert PV to W if provided in kW
        pv_w = pv * KW_TO_W if self.unit_power == UNIT_KW else pv

        # --- Minimal expected model ---
        expected_clear_w = float(min(max(pv_w, 0.0), float(self.cap_max_w)))
        deg_factor = max(0.0, 1.0 - float(self.degradation_pct) / 100.0)
        expected_after_deg = expected_clear_w * deg_factor

        if cloud is not None:
            c = min(max(cloud, 0.0), 100.0)
            expected_after_cloud = expected_after_deg * (1.0 - c / 100.0)
        else:
            expected_after_cloud = expected_after_deg

        expected_final_w = max(expected_after_cloud - float(self.reserve_w), 0.0)
        expected_final_w = min(expected_final_w, float(self.cap_max_w))

        attrs: Dict[str, Any] = {
            ATTR_MODEL_TYPE: NOTE_SOLAR_MODEL,
            ATTR_SOURCE: {
                "pv": self.pv_entity,
                "house": self.house_entity,
                "grid": self.grid_entity,
                "battery": self.batt_entity,
                "lux": self.lux_entity,
                "temp": self.temp_entity,
                "hum": self.hum_entity,
                "cloud": self.cloud_entity,
            },
            "unit_power": self.unit_power,
            "reserve_w": self.reserve_w,
            "cap_max_w": self.cap_max_w,
            ATTR_DEGRADATION_PCT: self.degradation_pct,
            ATTR_NOTE: "Minimal clear-sky proxy with degradation + cloud + reserve; capped.",
        }

        if grid is not None:
            attrs["grid_now"] = grid
        if batt is not None:
            attrs["battery_now"] = batt
        if lux is not None:
            attrs["lux_now"] = lux
        if temp is not None:
            attrs["temp_now"] = temp
        if hum is not None:
            attrs["hum_now_pct"] = hum
        if cloud is not None:
            attrs["cloud_now_pct"] = cloud

        return SPVMData(expected_w=expected_final_w, attrs=attrs)
