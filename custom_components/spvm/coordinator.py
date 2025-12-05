from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
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
    CONF_UNIT_PV, CONF_UNIT_HOUSE, CONF_UNIT_GRID, CONF_UNIT_BATTERY,
    DEF_UNIT_PV, DEF_UNIT_HOUSE, DEF_UNIT_GRID, DEF_UNIT_BATTERY,
    # reserve / caps / ageing
    CONF_RESERVE_W, DEF_RESERVE_W, CONF_CAP_MAX_W, DEF_CAP_MAX_W,
    CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT,
    # solar model params
    CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER, CONF_PANEL_TILT, DEF_PANEL_TILT,
    CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH,
    CONF_SITE_LATITUDE, DEF_SITE_LATITUDE, CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE,
    CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE, CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY,
    # lux correction & seasonal shading
    CONF_LUX_MIN_ELEVATION, DEF_LUX_MIN_ELEVATION, CONF_LUX_FLOOR_FACTOR, DEF_LUX_FLOOR_FACTOR,
    CONF_SHADING_WINTER_PCT, DEF_SHADING_WINTER_PCT,
    CONF_SHADING_MONTH_START, DEF_SHADING_MONTH_START, CONF_SHADING_MONTH_END, DEF_SHADING_MONTH_END,
    # timing
    CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL,
    CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW,
    # labels
    ATTR_MODEL_TYPE, ATTR_SOURCE, ATTR_DEGRADATION_PCT, ATTR_SYSTEM_EFFICIENCY,
    ATTR_SITE, ATTR_PANEL, ATTR_NOTE, NOTE_SOLAR_MODEL,
)
from .solar_model import SolarInputs, compute as solar_compute

_LOGGER = logging.getLogger(__name__)
Number = Union[float, int]


@dataclass
class SPVMData:
    expected_w: float
    yield_ratio_pct: Optional[float]
    surplus_net_w: Optional[float]
    attrs: Dict[str, Any]


def _safe_float(state: Optional[State]) -> Optional[float]:
    if not state or state.state in (None, "", "unknown", "unavailable"):
        return None
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return None


class SPVMCoordinator(DataUpdateCoordinator[SPVMData]):
    """Compute expected solar production with physical model + KPIs."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._last_pv_w: Optional[float] = None  # Cache dernière valeur PV pour tolérance

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

        # Units (per-sensor with fallback to legacy global unit)
        legacy_unit_power = data.get(CONF_UNIT_POWER, DEF_UNIT_POWER)
        self.unit_pv: str = data.get(CONF_UNIT_PV, legacy_unit_power)
        self.unit_house: str = data.get(CONF_UNIT_HOUSE, legacy_unit_power)
        self.unit_grid: str = data.get(CONF_UNIT_GRID, legacy_unit_power)
        self.unit_battery: str = data.get(CONF_UNIT_BATTERY, legacy_unit_power)
        self.unit_temp: str = data.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP)

        # Behaviour
        self.reserve_w: Number = data.get(CONF_RESERVE_W, DEF_RESERVE_W)
        self.cap_max_w: Number = data.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W)
        self.degradation_pct: Number = data.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)

        # Solar model params (fallback to HA config if None)
        self.panel_peak_w: float = float(data.get(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER))
        self.panel_tilt_deg: float = float(data.get(CONF_PANEL_TILT, DEF_PANEL_TILT))
        self.panel_az_deg: float = float(data.get(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH))

        self.site_lat: float = float(
            data.get(CONF_SITE_LATITUDE, self.hass.config.latitude if self.hass.config.latitude is not None else 0.0)
            or 0.0
        )
        self.site_lon: float = float(
            data.get(CONF_SITE_LONGITUDE, self.hass.config.longitude if self.hass.config.longitude is not None else 0.0)
            or 0.0
        )
        self.site_alt: float = float(
            data.get(CONF_SITE_ALTITUDE, self.hass.config.elevation if self.hass.config.elevation is not None else 0.0)
            or 0.0
        )
        self.system_eff: float = float(data.get(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY))

        # Lux correction parameters (v0.6.9+)
        self.lux_min_elevation: float = float(data.get(CONF_LUX_MIN_ELEVATION, DEF_LUX_MIN_ELEVATION))
        self.lux_floor_factor: float = float(data.get(CONF_LUX_FLOOR_FACTOR, DEF_LUX_FLOOR_FACTOR))

        # Seasonal shading parameters (v0.6.9+)
        self.shading_winter_pct: float = float(data.get(CONF_SHADING_WINTER_PCT, DEF_SHADING_WINTER_PCT))
        self.shading_month_start: int = int(data.get(CONF_SHADING_MONTH_START, DEF_SHADING_MONTH_START))
        self.shading_month_end: int = int(data.get(CONF_SHADING_MONTH_END, DEF_SHADING_MONTH_END))

        # Timing
        self.update_interval_s: int = int(data.get(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL))
        self.smoothing_window_s: int = int(data.get(CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}-coordinator",
            update_interval=timedelta(seconds=self.update_interval_s),
        )

    async def _async_update_data(self) -> SPVMData:
        """Compute expected production (W) and KPIs with physical model."""
        # Read current states (inputs)
        pv_state = self.hass.states.get(self.pv_entity)
        house_state = self.hass.states.get(self.house_entity)

        pv = _safe_float(pv_state)
        house = _safe_float(house_state)
        grid = _safe_float(self.hass.states.get(self.grid_entity)) if self.grid_entity else None
        batt = _safe_float(self.hass.states.get(self.batt_entity)) if self.batt_entity else None
        lux = _safe_float(self.hass.states.get(self.lux_entity)) if self.lux_entity else None
        temp = _safe_float(self.hass.states.get(self.temp_entity)) if self.temp_entity else None
        hum = _safe_float(self.hass.states.get(self.hum_entity)) if self.hum_entity else None
        cloud = _safe_float(self.hass.states.get(self.cloud_entity)) if self.cloud_entity else None

        # Log detailed sensor state for debugging
        if pv is None:
            pv_state_str = pv_state.state if pv_state else "MISSING"
            _LOGGER.warning(
                f"PV sensor ({self.pv_entity}) has non-numeric state: '{pv_state_str}'. "
                f"Using last known value: {self._last_pv_w}W"
            )
            if self._last_pv_w is not None:
                pv = self._last_pv_w / (KW_TO_W if self.unit_pv == UNIT_KW else 1.0)
            else:
                raise UpdateFailed(f"pv_sensor has no numeric state ('{pv_state_str}') and no cached value available")

        if house is None:
            house_state_str = house_state.state if house_state else "MISSING"
            _LOGGER.warning(f"House sensor ({self.house_entity}) has non-numeric state: '{house_state_str}'")
            raise UpdateFailed(f"house_sensor has no numeric state ('{house_state_str}')")

        # Convert to W per sensor unit
        pv_w = pv * (KW_TO_W if self.unit_pv == UNIT_KW else 1.0)
        house_w = house * (KW_TO_W if self.unit_house == UNIT_KW else 1.0)
        grid_w = grid * (KW_TO_W if self.unit_grid == UNIT_KW else 1.0) if grid is not None else None
        batt_w = batt * (KW_TO_W if self.unit_battery == UNIT_KW else 1.0) if batt is not None else None

        # Cache dernière valeur PV valide pour tolérance aux erreurs temporaires
        self._last_pv_w = pv_w

        # ---- Physical solar model ----
        now_utc = datetime.now(timezone.utc)
        inputs = SolarInputs(
            dt_utc=now_utc,
            lat_deg=self.site_lat,
            lon_deg=self.site_lon,
            altitude_m=self.site_alt,
            panel_tilt_deg=self.panel_tilt_deg,
            panel_azimuth_deg=self.panel_az_deg,
            panel_peak_w=self.panel_peak_w,
            system_efficiency=self.system_eff,
            cloud_pct=cloud,
            temp_c=temp,
            lux=lux,
            lux_min_elevation_deg=self.lux_min_elevation,
            lux_floor_factor=self.lux_floor_factor,
            shading_winter_pct=self.shading_winter_pct,
            shading_month_start=self.shading_month_start,
            shading_month_end=self.shading_month_end,
        )
        model = solar_compute(inputs)

        # Degradation correction (linéaire) + cap
        expected_w = model.expected_corrected_w * max(0.0, 1.0 - float(self.degradation_pct) / 100.0)
        expected_w = min(expected_w, float(self.cap_max_w))

        # Logs de diagnostic détaillés pour comprendre les estimations faibles
        _LOGGER.info(
            f"SPVM DIAGNOSTIC - Production Estimate Breakdown:\n"
            f"  Solar Model Params:\n"
            f"    - panel_peak_w: {self.panel_peak_w}W\n"
            f"    - system_efficiency: {self.system_eff}\n"
            f"    - panel_tilt: {self.panel_tilt_deg}°\n"
            f"    - panel_azimuth: {self.panel_az_deg}°\n"
            f"    - site_lat/lon: {self.site_lat:.2f}/{self.site_lon:.2f}\n"
            f"  Solar Geometry:\n"
            f"    - elevation: {model.elevation_deg:.1f}°\n"
            f"    - azimuth: {model.azimuth_deg:.1f}°\n"
            f"    - incidence: {model.incidence_deg:.1f}°\n"
            f"  Irradiance:\n"
            f"    - GHI clear-sky: {model.ghi_clear_wm2:.1f} W/m²\n"
            f"    - POA clear-sky: {model.poa_clear_wm2:.1f} W/m²\n"
            f"  Expected Power (step-by-step):\n"
            f"    - Clear-sky (before corrections): {model.expected_clear_w:.1f}W\n"
            f"    - After cloud/temp/lux corrections: {model.expected_corrected_w:.1f}W\n"
            f"    - After degradation ({self.degradation_pct}%): {expected_w:.1f}W (before cap)\n"
            f"    - Final (after cap {self.cap_max_w}W): {expected_w:.1f}W\n"
            f"  Correction Factors:\n"
            f"    - Lux correction: {model.lux_factor if model.lux_factor is not None else 'N/A (using cloud_pct)'}\n"
            f"    - Lux value: {lux if lux is not None else 'N/A'}\n"
            f"    - Cloud coverage: {cloud if cloud is not None else 'N/A'}%\n"
            f"    - Temperature: {temp if temp is not None else 'N/A'}°C\n"
            f"  Current Production:\n"
            f"    - PV actual: {pv_w:.1f}W\n"
            f"    - PV expected: {expected_w:.1f}W\n"
            f"    - Yield ratio: {(pv_w/expected_w*100) if expected_w > 1e-6 else 0:.1f}%"
        )

        # KPIs
        yield_ratio_pct = (pv_w / expected_w) * 100.0 if expected_w > 1e-6 else None

        surplus_virtual = pv_w - house_w
        _LOGGER.debug(
            f"SPVM surplus calculation: pv_w={pv_w:.1f}W, house_w={house_w:.1f}W, "
            f"surplus_virtual={surplus_virtual:.1f}W, reserve={self.reserve_w}W"
        )
        if grid_w is not None:
            export_w = max(-grid_w, 0.0)  # grid +import/-export
            _LOGGER.debug(f"SPVM grid_w={grid_w:.1f}W, export_w={export_w:.1f}W")
            surplus_virtual = max(surplus_virtual, export_w)
            _LOGGER.debug(f"SPVM surplus_virtual after grid adjustment: {surplus_virtual:.1f}W")
        surplus_net_w = max(surplus_virtual - float(self.reserve_w), 0.0)
        _LOGGER.debug(f"SPVM surplus_net_w final: {surplus_net_w:.1f}W")

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
            ATTR_SYSTEM_EFFICIENCY: self.system_eff,
            ATTR_DEGRADATION_PCT: self.degradation_pct,
            ATTR_SITE: {"lat": self.site_lat, "lon": self.site_lon, "alt_m": self.site_alt},
            ATTR_PANEL: {"tilt_deg": self.panel_tilt_deg, "azimuth_deg": self.panel_az_deg, "peak_w": self.panel_peak_w},
            "reserve_w": self.reserve_w,
            "cap_max_w": self.cap_max_w,
            "model_elevation_deg": model.elevation_deg,
            "model_azimuth_deg": model.azimuth_deg,
            "model_declination_deg": model.declination_deg,
            "model_incidence_deg": model.incidence_deg,
            "ghi_clear_wm2": model.ghi_clear_wm2,
            "poa_clear_wm2": model.poa_clear_wm2,
            "debug_pv_w": round(pv_w, 1),
            "debug_house_w": round(house_w, 1),
            "debug_surplus_virtual": round(surplus_virtual, 1),
            ATTR_NOTE: "Physical clear-sky + incidence; cloud & temp corrections; lux correction if available; then degradation, reserve, cap.",
        }
        if model.lux_factor is not None:
            attrs["lux_factor"] = round(model.lux_factor, 3)
            attrs["lux_correction_active"] = True
        else:
            attrs["lux_correction_active"] = False
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

        return SPVMData(
            expected_w=float(round(expected_w, 3)),
            yield_ratio_pct=None if yield_ratio_pct is None else float(round(yield_ratio_pct, 2)),
            surplus_net_w=float(round(surplus_net_w, 1)),
            attrs=attrs,
        )
