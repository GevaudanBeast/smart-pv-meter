from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig,
    SelectSelector, SelectSelectorConfig, SelectOptionDict,
    NumberSelector, NumberSelectorConfig,
)

from .const import (
    DOMAIN, DEFAULT_ENTRY_TITLE,
    # sensors
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    # units
    CONF_UNIT_POWER, CONF_UNIT_TEMP, DEF_UNIT_POWER, DEF_UNIT_TEMP, UNIT_W, UNIT_KW, UNIT_C, UNIT_F,
    # reserve/cap/age
    CONF_RESERVE_W, DEF_RESERVE_W, CONF_CAP_MAX_W, DEF_CAP_MAX_W, CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT,
    # solar model params
    CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER, CONF_PANEL_TILT, DEF_PANEL_TILT,
    CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH,
    CONF_SITE_LATITUDE, DEF_SITE_LATITUDE, CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE,
    CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE, CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY,
    # timing
    CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL,
    CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW,
)

REQUIRED = (CONF_PV_SENSOR, CONF_HOUSE_SENSOR)
ALL_KEYS = (
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    CONF_UNIT_POWER, CONF_UNIT_TEMP,
    CONF_PANEL_PEAK_POWER, CONF_PANEL_TILT, CONF_PANEL_AZIMUTH,
    CONF_SITE_LATITUDE, CONF_SITE_LONGITUDE, CONF_SITE_ALTITUDE,
    CONF_SYSTEM_EFFICIENCY,
    CONF_RESERVE_W, CONF_CAP_MAX_W, CONF_DEGRADATION_PCT,
    CONF_UPDATE_INTERVAL_SECONDS, CONF_SMOOTHING_WINDOW_SECONDS,
)

def _ent_sel() -> EntitySelector:
    return EntitySelector(EntitySelectorConfig(domain=["sensor"]))

def _defaults_from(hass: HomeAssistant, base: dict) -> dict:
    """Merge defaults for form prefill (base already merged: entry.data|options)."""
    d = dict(base or {})
    # Inject global HA defaults for site if missing
    d.setdefault(CONF_SITE_LATITUDE, hass.config.latitude)
    d.setdefault(CONF_SITE_LONGITUDE, hass.config.longitude)
    d.setdefault(CONF_SITE_ALTITUDE, hass.config.elevation)
    # Hard defaults (so selectors always get a number/string)
    d.setdefault(CONF_UNIT_POWER, DEF_UNIT_POWER)
    d.setdefault(CONF_UNIT_TEMP, DEF_UNIT_TEMP)
    d.setdefault(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER)
    d.setdefault(CONF_PANEL_TILT, DEF_PANEL_TILT)
    d.setdefault(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH)
    d.setdefault(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY)
    d.setdefault(CONF_RESERVE_W, DEF_RESERVE_W)
    d.setdefault(CONF_CAP_MAX_W, DEF_CAP_MAX_W)
    d.setdefault(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)
    d.setdefault(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL)
    d.setdefault(CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW)
    return d

def _schema(hass: HomeAssistant, cur: dict | None) -> vol.Schema:
    v = _defaults_from(hass, cur or {})
    return vol.Schema({
        # Requis
        vol.Required(CONF_PV_SENSOR, default=v.get(CONF_PV_SENSOR)): _ent_sel(),
        vol.Required(CONF_HOUSE_SENSOR, default=v.get(CONF_HOUSE_SENSOR)): _ent_sel(),

        # Optionnels (capteurs)
        vol.Optional(CONF_GRID_POWER_SENSOR, default=v.get(CONF_GRID_POWER_SENSOR)): _ent_sel(),
        vol.Optional(CONF_BATTERY_SENSOR, default=v.get(CONF_BATTERY_SENSOR)): _ent_sel(),
        vol.Optional(CONF_LUX_SENSOR, default=v.get(CONF_LUX_SENSOR)): _ent_sel(),
        vol.Optional(CONF_TEMP_SENSOR, default=v.get(CONF_TEMP_SENSOR)): _ent_sel(),
        vol.Optional(CONF_HUM_SENSOR, default=v.get(CONF_HUM_SENSOR)): _ent_sel(),
        vol.Optional(CONF_CLOUD_SENSOR, default=v.get(CONF_CLOUD_SENSOR)): _ent_sel(),

        # Unités
        vol.Optional(CONF_UNIT_POWER, default=v.get(CONF_UNIT_POWER)): SelectSelector(
            SelectSelectorConfig(options=[
                SelectOptionDict(value=UNIT_W, label="W"),
                SelectOptionDict(value=UNIT_KW, label="kW"),
            ], mode="dropdown")
        ),
        vol.Optional(CONF_UNIT_TEMP, default=v.get(CONF_UNIT_TEMP)): SelectSelector(
            SelectSelectorConfig(options=[
                SelectOptionDict(value=UNIT_C, label="°C"),
                SelectOptionDict(value=UNIT_F, label="°F"),
            ], mode="dropdown")
        ),

        # Modèle solaire (physique)
        vol.Optional(CONF_PANEL_PEAK_POWER, default=v.get(CONF_PANEL_PEAK_POWER)): NumberSelector(
            NumberSelectorConfig(min=100, max=20000, step=50, mode="box")
        ),
        vol.Optional(CONF_PANEL_TILT, default=v.get(CONF_PANEL_TILT)): NumberSelector(
            NumberSelectorConfig(min=0, max=90, step=1, mode="box")
        ),
        vol.Optional(CONF_PANEL_AZIMUTH, default=v.get(CONF_PANEL_AZIMUTH)): NumberSelector(
            NumberSelectorConfig(min=0, max=360, step=1, mode="box")
        ),
        vol.Optional(CONF_SITE_LATITUDE, default=v.get(CONF_SITE_LATITUDE)): NumberSelector(
            NumberSelectorConfig(min=-90, max=90, step=0.0001, mode="box")
        ),
        vol.Optional(CONF_SITE_LONGITUDE, default=v.get(CONF_SITE_LONGITUDE)): NumberSelector(
            NumberSelectorConfig(min=-180, max=180, step=0.0001, mode="box")
        ),
        vol.Optional(CONF_SITE_ALTITUDE, default=v.get(CONF_SITE_ALTITUDE)): NumberSelector(
            NumberSelectorConfig(min=-500, max=6000, step=1, mode="box")
        ),
        vol.Optional(CONF_SYSTEM_EFFICIENCY, default=v.get(CONF_SYSTEM_EFFICIENCY)): NumberSelector(
            NumberSelectorConfig(min=0.5, max=1.0, step=0.01, mode="box")
        ),

        # Réserve / cap / vieillissement
        vol.Optional(CONF_RESERVE_W, default=v.get(CONF_RESERVE_W)): NumberSelector(
            NumberSelectorConfig(min=0, max=2000, step=10, mode="box")
        ),
        vol.Optional(CONF_CAP_MAX_W, default=v.get(CONF_CAP_MAX_W)): NumberSelector(
            NumberSelectorConfig(min=0, max=10000, step=50, mode="box")
        ),
        vol.Optional(CONF_DEGRADATION_PCT, default=v.get(CONF_DEGRADATION_PCT)): NumberSelector(
            NumberSelectorConfig(min=0, max=50, step=0.5, mode="box")
        ),

        # Timing
        vol.Optional(CONF_UPDATE_INTERVAL_SECONDS, default=v.get(CONF_UPDATE_INTERVAL_SECONDS)): NumberSelector(
            NumberSelectorConfig(min=5, max=600, step=5, mode="box")
        ),
        vol.Optional(CONF_SMOOTHING_WINDOW_SECONDS, default=v.get(CONF_SMOOTHING_WINDOW_SECONDS)): NumberSelector(
            NumberSelectorConfig(min=0, max=600, step=5, mode="box")
        ),
    })

def _validate_required(user_input: dict) -> dict:
    errors: dict = {}
    for k in REQUIRED:
        if not user_input.get(k):
            errors[k] = "required"
    return errors


class SPVMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate_required(user_input)
            if not errors:
                return self.async_create_entry(title=DEFAULT_ENTRY_TITLE, data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema(self.hass, None), errors=errors)


class SPVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Full editable options form with prefilled values."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data_cur = dict(self.config_entry.data or {})
        opts_cur = dict(self.config_entry.options or {})
        merged = {**data_cur, **opts_cur}

        if user_input is not None:
            # Minimal validation
            errors = _validate_required(user_input)
            if errors:
                return self.async_show_form(step_id="init", data_schema=_schema(self.hass, merged), errors=errors)

            # Save to options (do not mutate data)
            # Keep only known keys to avoid stray values
            clean = {k: user_input.get(k) for k in ALL_KEYS if k in user_input}
            return self.async_create_entry(title="", data=clean)

        return self.async_show_form(step_id="init", data_schema=_schema(self.hass, merged), errors={})


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return SPVMOptionsFlowHandler(config_entry)
