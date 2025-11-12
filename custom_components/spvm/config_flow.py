"""Config flow pour Smart PV Meter v0.6.0 (autonome, sans expected externe)."""
from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    SelectSelector, SelectSelectorConfig, SelectOptionDict,
)

from .const import (
    DOMAIN,
    # Entities
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR,
    CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    # System params
    CONF_RESERVE_W, CONF_UNIT_POWER, CONF_UNIT_TEMP, CONF_CAP_MAX_W, CONF_DEGRADATION_PCT,
    DEF_RESERVE_W, DEF_UNIT_POWER, DEF_UNIT_TEMP, DEF_CAP_MAX_W, DEF_DEGRADATION_PCT,
    # Solar model
    CONF_PANEL_PEAK_POWER, CONF_PANEL_TILT, CONF_PANEL_AZIMUTH,
    CONF_SITE_LATITUDE, CONF_SITE_LONGITUDE, CONF_SITE_ALTITUDE,
    CONF_SYSTEM_EFFICIENCY,
    DEF_PANEL_PEAK_POWER, DEF_PANEL_TILT, DEF_PANEL_AZIMUTH,
    DEF_SITE_LATITUDE, DEF_SITE_LONGITUDE, DEF_SITE_ALTITUDE,
    DEF_SYSTEM_EFFICIENCY,
    # Update / smoothing / debug
    CONF_UPDATE_INTERVAL_SECONDS, CONF_SMOOTHING_WINDOW_SECONDS, CONF_DEBUG_EXPECTED,
    DEF_UPDATE_INTERVAL, DEF_SMOOTHING_WINDOW, DEF_DEBUG_EXPECTED,
    # Entry
    CONF_ENTRY_VERSION, DEFAULT_ENTRY_TITLE,
)

def _entity_selector(domain: str | None = None) -> EntitySelector:
    return EntitySelector(EntitySelectorConfig(domain=[domain] if domain else None, multiple=False))

def _number_selector(mini: float, maxi: float, step: float, mode: NumberSelectorMode = NumberSelectorMode.BOX) -> NumberSelector:
    return NumberSelector(NumberSelectorConfig(min=mini, max=maxi, step=step, mode=mode))

def _required_entity(field: str, defaults: dict[str, Any]):
    if field in defaults and defaults[field]:
        return vol.Required(field, default=defaults[field])
    return vol.Required(field)

def _optional_entity(field: str, defaults: dict[str, Any]):
    if field in defaults and defaults[field]:
        return vol.Optional(field, default=defaults[field])
    return vol.Optional(field)

class SPVMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = CONF_ENTRY_VERSION

    @staticmethod
    def _coerce_bool(value: Any, fallback: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("true", "1", "yes", "on"): return True
            if v in ("false", "0", "no", "off"): return False
        return fallback

    @staticmethod
    def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
        out = dict(user_input)
        if out.get(CONF_UNIT_POWER) not in ("W", "kW"):
            out[CONF_UNIT_POWER] = DEF_UNIT_POWER
        if out.get(CONF_UNIT_TEMP) not in ("°C", "°F"):
            out[CONF_UNIT_TEMP] = DEF_UNIT_TEMP

        for k, d in (
            (CONF_RESERVE_W, DEF_RESERVE_W), (CONF_CAP_MAX_W, DEF_CAP_MAX_W), (CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT),
            (CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER), (CONF_PANEL_TILT, DEF_PANEL_TILT), (CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH),
            (CONF_SITE_LATITUDE, DEF_SITE_LATITUDE), (CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE), (CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE),
            (CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY),
            (CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL), (CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW),
        ):
            try:
                out[k] = float(out.get(k, d))
            except Exception:
                out[k] = d

        out[CONF_DEBUG_EXPECTED] = SPVMConfigFlow._coerce_bool(out.get(CONF_DEBUG_EXPECTED, DEF_DEBUG_EXPECTED), DEF_DEBUG_EXPECTED)
        return out

    @staticmethod
    def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        debug_default = SPVMConfigFlow._coerce_bool(defaults.get(CONF_DEBUG_EXPECTED, DEF_DEBUG_EXPECTED), DEF_DEBUG_EXPECTED)
        return vol.Schema({
            # Required
            _required_entity(CONF_PV_SENSOR, defaults): _entity_selector("sensor"),
            _required_entity(CONF_HOUSE_SENSOR, defaults): _entity_selector("sensor"),
            # Optional other sensors
            _optional_entity(CONF_GRID_POWER_SENSOR, defaults): _entity_selector("sensor"),
            _optional_entity(CONF_BATTERY_SENSOR, defaults): _entity_selector("sensor"),
            _optional_entity(CONF_LUX_SENSOR, defaults): _entity_selector("sensor"),
            _optional_entity(CONF_TEMP_SENSOR, defaults): _entity_selector("sensor"),
            _optional_entity(CONF_HUM_SENSOR, defaults): _entity_selector("sensor"),
            _optional_entity(CONF_CLOUD_SENSOR, defaults): _entity_selector("sensor"),
            # System
            vol.Optional(CONF_RESERVE_W, default=defaults.get(CONF_RESERVE_W, DEF_RESERVE_W)): _number_selector(0, 2000, 10),
            vol.Optional(CONF_CAP_MAX_W, default=defaults.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W)): _number_selector(0, 10000, 50),
            vol.Optional(CONF_DEGRADATION_PCT, default=defaults.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)): _number_selector(0, 100, 0.5),
            # Solar model
            vol.Optional(CONF_PANEL_PEAK_POWER, default=defaults.get(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER)): _number_selector(100, 20000, 50),
            vol.Optional(CONF_PANEL_TILT, default=defaults.get(CONF_PANEL_TILT, DEF_PANEL_TILT)): _number_selector(0, 90, 1),
            vol.Optional(CONF_PANEL_AZIMUTH, default=defaults.get(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH)): _number_selector(0, 360, 5),
            vol.Optional(CONF_SITE_LATITUDE, default=defaults.get(CONF_SITE_LATITUDE, DEF_SITE_LATITUDE)): _number_selector(-90, 90, 0.0001),
            vol.Optional(CONF_SITE_LONGITUDE, default=defaults.get(CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE)): _number_selector(-180, 180, 0.0001),
            vol.Optional(CONF_SITE_ALTITUDE, default=defaults.get(CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE)): _number_selector(0, 5000, 10),
            vol.Optional(CONF_SYSTEM_EFFICIENCY, default=defaults.get(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY)): _number_selector(0.5, 1.0, 0.01),
            # Update / smoothing / units / debug
            vol.Optional(CONF_UPDATE_INTERVAL_SECONDS, default=defaults.get(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL)): _number_selector(10, 300, 5),
            vol.Optional(CONF_SMOOTHING_WINDOW_SECONDS, default=defaults.get(CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW)): _number_selector(10, 180, 5),
            vol.Optional(CONF_UNIT_POWER, default=defaults.get(CONF_UNIT_POWER, DEF_UNIT_POWER)): SelectSelector(
                SelectSelectorConfig(options=[SelectOptionDict(value="W", label="W"), SelectOptionDict(value="kW", label="kW")], mode="dropdown")
            ),
            vol.Optional(CONF_UNIT_TEMP, default=defaults.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP)): SelectSelector(
                SelectSelectorConfig(options=[SelectOptionDict(value="°C", label="°C"), SelectOptionDict(value="°F", label="°F")], mode="dropdown")
            ),
            vol.Optional(CONF_DEBUG_EXPECTED, default=debug_default): bool,
        })

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = self._normalize_input(user_input)
            await self.async_set_unique_id(f"{DOMAIN}_{data[CONF_PV_SENSOR]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_ENTRY_TITLE, data=data)
        return self.async_show_form(step_id="user", data_schema=self._schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return SPVMOptionsFlow(config_entry)

class SPVMOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = SPVMConfigFlow._normalize_input(user_input)
            return self.async_create_entry(title="", data=data)
        defaults = {**self.entry.data, **self.entry.options}
        return self.async_show_form(step_id="init", data_schema=SPVMConfigFlow._schema(defaults))
