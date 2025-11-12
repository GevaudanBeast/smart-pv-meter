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
    CONF_SITE_LATITUDE, CONF_SITE_LONGITUDE, CONF_SITE_ALTITUDE,
    CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY,
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

def _validate_required(user_input: dict) -> dict:
    errors: dict = {}
    for k in REQUIRED:
        if not user_input.get(k):
            errors[k] = "required"
    return errors

def _schema(hass: HomeAssistant, cur: dict | None) -> vol.Schema:
    """Construire le schéma sans injecter de default=None (cause 400)."""
    v = dict(cur or {})

    # helpers : ajout conditionnel du default (seulement si non None)
    def _opt_sel(schema: dict, key: str, selector):
        if key in v and v[key] not in (None, ""):
            schema[vol.Optional(key, default=v[key])] = selector
        else:
            schema[vol.Optional(key)] = selector

    def _req_sel(schema: dict, key: str, selector):
        # Requis: si pas de valeur -> pas de default (laisser le champ vide)
        if key in v and v[key] not in (None, ""):
            schema[vol.Required(key, default=v[key])] = selector
        else:
            schema[vol.Required(key)] = selector

    def _opt_num(schema: dict, key: str, selector, fallback=None):
        val = v.get(key, fallback)
        if val is not None:
            schema[vol.Optional(key, default=val)] = selector
        else:
            schema[vol.Optional(key)] = selector

    def _opt_sel_static(schema: dict, key: str, options: list[SelectOptionDict]):
        sel = SelectSelector(SelectSelectorConfig(options=options, mode="dropdown"))
        if key in v and v[key] not in (None, ""):
            schema[vol.Optional(key, default=v[key])] = sel
        else:
            schema[vol.Optional(key)] = sel

    schema: dict = {}

    # Requis
    _req_sel(schema, CONF_PV_SENSOR, _ent_sel())
    _req_sel(schema, CONF_HOUSE_SENSOR, _ent_sel())

    # Optionnels capteurs
    _opt_sel(schema, CONF_GRID_POWER_SENSOR, _ent_sel())
    _opt_sel(schema, CONF_BATTERY_SENSOR, _ent_sel())
    _opt_sel(schema, CONF_LUX_SENSOR, _ent_sel())
    _opt_sel(schema, CONF_TEMP_SENSOR, _ent_sel())
    _opt_sel(schema, CONF_HUM_SENSOR, _ent_sel())
    _opt_sel(schema, CONF_CLOUD_SENSOR, _ent_sel())

    # Unités
    _opt_sel_static(schema, CONF_UNIT_POWER, [
        SelectOptionDict(value=UNIT_W, label="W"),
        SelectOptionDict(value=UNIT_KW, label="kW"),
    ])
    _opt_sel_static(schema, CONF_UNIT_TEMP, [
        SelectOptionDict(value=UNIT_C, label="°C"),
        SelectOptionDict(value=UNIT_F, label="°F"),
    ])

    # Modèle solaire (physique)
    _opt_num(schema, CONF_PANEL_PEAK_POWER,
             NumberSelector(NumberSelectorConfig(min=100, max=20000, step=50, mode="box")),
             fallback=DEF_PANEL_PEAK_POWER)
    _opt_num(schema, CONF_PANEL_TILT,
             NumberSelector(NumberSelectorConfig(min=0, max=90, step=1, mode="box")),
             fallback=DEF_PANEL_TILT)
    _opt_num(schema, CONF_PANEL_AZIMUTH,
             NumberSelector(NumberSelectorConfig(min=0, max=360, step=1, mode="box")),
             fallback=DEF_PANEL_AZIMUTH)

    # GPS : prendre conf HA si dispo, sinon pas de default (pas None)
    lat_default = v.get(CONF_SITE_LATITUDE, hass.config.latitude)
    lon_default = v.get(CONF_SITE_LONGITUDE, hass.config.longitude)
    alt_default = v.get(CONF_SITE_ALTITUDE, hass.config.elevation)

    _opt_num(schema, CONF_SITE_LATITUDE,
             NumberSelector(NumberSelectorConfig(min=-90, max=90, step=0.0001, mode="box")),
             fallback=lat_default if lat_default is not None else None)
    _opt_num(schema, CONF_SITE_LONGITUDE,
             NumberSelector(NumberSelectorConfig(min=-180, max=180, step=0.0001, mode="box")),
             fallback=lon_default if lon_default is not None else None)
    _opt_num(schema, CONF_SITE_ALTITUDE,
             NumberSelector(NumberSelectorConfig(min=-500, max=6000, step=1, mode="box")),
             fallback=alt_default if alt_default is not None else None)

    _opt_num(schema, CONF_SYSTEM_EFFICIENCY,
             NumberSelector(NumberSelectorConfig(min=0.5, max=1.0, step=0.01, mode="box")),
             fallback=DEF_SYSTEM_EFFICIENCY)

    # Réserve / cap / vieillissement
    _opt_num(schema, CONF_RESERVE_W,
             NumberSelector(NumberSelectorConfig(min=0, max=2000, step=10, mode="box")),
             fallback=DEF_RESERVE_W)
    _opt_num(schema, CONF_CAP_MAX_W,
             NumberSelector(NumberSelectorConfig(min=0, max=10000, step=50, mode="box")),
             fallback=DEF_CAP_MAX_W)
    _opt_num(schema, CONF_DEGRADATION_PCT,
             NumberSelector(NumberSelectorConfig(min=0, max=50, step=0.5, mode="box")),
             fallback=DEF_DEGRADATION_PCT)

    # Timing
    _opt_num(schema, CONF_UPDATE_INTERVAL_SECONDS,
             NumberSelector(NumberSelectorConfig(min=5, max=600, step=5, mode="box")),
             fallback=DEF_UPDATE_INTERVAL)
    _opt_num(schema, CONF_SMOOTHING_WINDOW_SECONDS,
             NumberSelector(NumberSelectorConfig(min=0, max=600, step=5, mode="box")),
             fallback=DEF_SMOOTHING_WINDOW)

    return vol.Schema(schema)


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
    """Options (édition) avec préremplissage sans defaults None."""

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

            # ne conserver que les clés connues
            clean = {k: user_input.get(k) for k in ALL_KEYS if k in user_input}
            return self.async_create_entry(title="", data=clean)

        return self.async_show_form(step_id="init", data_schema=_schema(self.hass, merged), errors={})


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return SPVMOptionsFlowHandler(config_entry)
