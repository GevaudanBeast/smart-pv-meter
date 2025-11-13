from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    DOMAIN, DEFAULT_ENTRY_TITLE,
    # sensors
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    # units
    CONF_UNIT_POWER, CONF_UNIT_TEMP, DEF_UNIT_POWER, DEF_UNIT_TEMP, UNIT_W, UNIT_KW, UNIT_C, UNIT_F,
    # reserve/cap/age
    CONF_RESERVE_W, DEF_RESERVE_W, CONF_CAP_MAX_W, DEF_CAP_MAX_W, CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT,
    # solar model
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

def _coerce_float(v):
    if v in (None, "", "unknown", "unavailable"):
        return vol.UNDEFINED
    try:
        return float(v)
    except Exception:
        raise vol.Invalid("must_be_number")

def _coerce_int(v):
    if v in (None, "", "unknown", "unavailable"):
        return vol.UNDEFINED
    try:
        return int(float(v))
    except Exception:
        raise vol.Invalid("must_be_int")

def _coerce_choice(v, allowed: list[str]):
    if v in (None, "", "unknown", "unavailable"):
        return vol.UNDEFINED
    if v not in allowed:
        raise vol.Invalid("invalid_choice")
    return v

def _merge_defaults(hass: HomeAssistant, cur: dict | None) -> dict:
    d = dict(cur or {})
    # Inject HA site if absent
    if d.get(CONF_SITE_LATITUDE) in (None, "", vol.UNDEFINED):
        if hass.config.latitude is not None:
            d[CONF_SITE_LATITUDE] = float(hass.config.latitude)
    if d.get(CONF_SITE_LONGITUDE) in (None, "", vol.UNDEFINED):
        if hass.config.longitude is not None:
            d[CONF_SITE_LONGITUDE] = float(hass.config.longitude)
    if d.get(CONF_SITE_ALTITUDE) in (None, "", vol.UNDEFINED):
        if hass.config.elevation is not None:
            d[CONF_SITE_ALTITUDE] = float(hass.config.elevation)

    # Hard defaults for safe display (without ever passing None)
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
    v = _merge_defaults(hass, cur)
    schema = {}

    # Requis
    if v.get(CONF_PV_SENSOR):
        schema[vol.Required(CONF_PV_SENSOR, default=v[CONF_PV_SENSOR])] = _ent_sel()
    else:
        schema[vol.Required(CONF_PV_SENSOR)] = _ent_sel()
    if v.get(CONF_HOUSE_SENSOR):
        schema[vol.Required(CONF_HOUSE_SENSOR, default=v[CONF_HOUSE_SENSOR])] = _ent_sel()
    else:
        schema[vol.Required(CONF_HOUSE_SENSOR)] = _ent_sel()

    # Optionnels capteurs
    for key in (CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR, CONF_LUX_SENSOR,
                CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR):
        if v.get(key):
            schema[vol.Optional(key, default=v[key])] = _ent_sel()
        else:
            schema[vol.Optional(key)] = _ent_sel()

    # Unités (choices simples, sans default=None)
    up = v.get(CONF_UNIT_POWER, DEF_UNIT_POWER)
    ut = v.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP)
    schema[vol.Optional(CONF_UNIT_POWER, default=up)] = vol.In([UNIT_W, UNIT_KW])
    schema[vol.Optional(CONF_UNIT_TEMP, default=ut)] = vol.In([UNIT_C, UNIT_F])

    # Numériques (coercitions sûres)
    def opt_num(key, default_val):
        curv = v.get(key, default_val)
        # pas de default si encore indéfini
        if curv in (None, "", vol.UNDEFINED):
            schema[vol.Optional(key)] = _coerce_float
        else:
            schema[vol.Optional(key, default=curv)] = _coerce_float

    def opt_int(key, default_val):
        curv = v.get(key, default_val)
        if curv in (None, "", vol.UNDEFINED):
            schema[vol.Optional(key)] = _coerce_int
        else:
            schema[vol.Optional(key, default=curv)] = _coerce_int

    # Modèle solaire
    opt_num(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER)
    opt_num(CONF_PANEL_TILT, DEF_PANEL_TILT)
    opt_num(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH)

    # GPS (HA si dispo, sinon champ sans default)
    lat_default = v.get(CONF_SITE_LATITUDE, DEF_SITE_LATITUDE)
    lon_default = v.get(CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE)
    alt_default = v.get(CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE)

    if lat_default in (None, "", vol.UNDEFINED):
        schema[vol.Optional(CONF_SITE_LATITUDE)] = _coerce_float
    else:
        schema[vol.Optional(CONF_SITE_LATITUDE, default=lat_default)] = _coerce_float

    if lon_default in (None, "", vol.UNDEFINED):
        schema[vol.Optional(CONF_SITE_LONGITUDE)] = _coerce_float
    else:
        schema[vol.Optional(CONF_SITE_LONGITUDE, default=lon_default)] = _coerce_float

    if alt_default in (None, "", vol.UNDEFINED):
        schema[vol.Optional(CONF_SITE_ALTITUDE)] = _coerce_float
    else:
        schema[vol.Optional(CONF_SITE_ALTITUDE, default=alt_default)] = _coerce_float

    opt_num(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY)

    # Réserve / cap / vieillissement
    opt_num(CONF_RESERVE_W, DEF_RESERVE_W)
    opt_num(CONF_CAP_MAX_W, DEF_CAP_MAX_W)
    opt_num(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)

    # Timing
    opt_int(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL)
    opt_int(CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW)

    return vol.Schema(schema)

def _validate_required(user_input: dict) -> dict:
    errors: dict = {}
    for k in REQUIRED:
        if not user_input.get(k):
            errors[k] = "required"
    # unités
    if user_input.get(CONF_UNIT_POWER) not in (UNIT_W, UNIT_KW, None, vol.UNDEFINED):
        errors[CONF_UNIT_POWER] = "invalid_choice"
    if user_input.get(CONF_UNIT_TEMP) not in (UNIT_C, UNIT_F, None, vol.UNDEFINED):
        errors[CONF_UNIT_TEMP] = "invalid_choice"
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

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return SPVMOptionsFlowHandler(config_entry)


class SPVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Options (édition) robustes sans defaults None et avec coercition."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        data_cur = dict(self.config_entry.data or {})
        opts_cur = dict(self.config_entry.options or {})
        merged = {**data_cur, **opts_cur}

        if user_input is not None:
            errors = _validate_required(user_input)
            if errors:
                return self.async_show_form(step_id="init", data_schema=_schema(self.hass, merged), errors=errors)

            clean = {k: user_input.get(k) for k in ALL_KEYS if k in user_input}
            return self.async_create_entry(title="", data=clean)

        return self.async_show_form(step_id="init", data_schema=_schema(self.hass, merged), errors={})
