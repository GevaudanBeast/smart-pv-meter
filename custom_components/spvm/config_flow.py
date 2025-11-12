from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
    NumberSelector,
    NumberSelectorConfig,
)

from .const import (
    DOMAIN,
    DEFAULT_ENTRY_TITLE,
    # sensors
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
    # units
    CONF_UNIT_POWER, CONF_UNIT_TEMP, DEF_UNIT_POWER, DEF_UNIT_TEMP, UNIT_W, UNIT_KW, UNIT_C, UNIT_F,
    # reserve / caps / ageing
    CONF_RESERVE_W, DEF_RESERVE_W, CONF_CAP_MAX_W, DEF_CAP_MAX_W, CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT,
    # timing
    CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL, CONF_SMOOTHING_WINDOW_SECONDS, DEF_SMOOTHING_WINDOW,
)

REQUIRED = [CONF_PV_SENSOR, CONF_HOUSE_SENSOR]
OPTIONAL = [
    CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_LUX_SENSOR, CONF_TEMP_SENSOR, CONF_HUM_SENSOR, CONF_CLOUD_SENSOR,
]

def _ent_sel(domain: list[str] | None = None) -> EntitySelector:
    return EntitySelector(EntitySelectorConfig(domain=domain))

def _schema_user(hass: HomeAssistant) -> vol.Schema:
    return vol.Schema(
        {
            # Requis
            vol.Required(CONF_PV_SENSOR): _ent_sel(["sensor"]),
            vol.Required(CONF_HOUSE_SENSOR): _ent_sel(["sensor"]),

            # Optionnels
            vol.Optional(CONF_GRID_POWER_SENSOR): _ent_sel(["sensor"]),
            vol.Optional(CONF_BATTERY_SENSOR): _ent_sel(["sensor"]),
            vol.Optional(CONF_LUX_SENSOR): _ent_sel(["sensor"]),
            vol.Optional(CONF_TEMP_SENSOR): _ent_sel(["sensor"]),
            vol.Optional(CONF_HUM_SENSOR): _ent_sel(["sensor"]),
            vol.Optional(CONF_CLOUD_SENSOR): _ent_sel(["sensor"]),

            # Unités
            vol.Optional(
                CONF_UNIT_POWER, default=DEF_UNIT_POWER
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=UNIT_W, label="W"),
                        SelectOptionDict(value=UNIT_KW, label="kW"),
                    ],
                    mode="dropdown",
                )
            ),
            vol.Optional(
                CONF_UNIT_TEMP, default=DEF_UNIT_TEMP
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=UNIT_C, label="°C"),
                        SelectOptionDict(value=UNIT_F, label="°F"),
                    ],
                    mode="dropdown",
                )
            ),

            # Réserve / cap / vieillissement
            vol.Optional(
                CONF_RESERVE_W, default=DEF_RESERVE_W
            ): NumberSelector(NumberSelectorConfig(min=0, max=2000, step=10, mode="box")),
            vol.Optional(
                CONF_CAP_MAX_W, default=DEF_CAP_MAX_W
            ): NumberSelector(NumberSelectorConfig(min=0, max=10000, step=50, mode="box")),
            vol.Optional(
                CONF_DEGRADATION_PCT, default=DEF_DEGRADATION_PCT
            ): NumberSelector(NumberSelectorConfig(min=0, max=50, step=0.5, mode="box")),

            # Timing
            vol.Optional(
                CONF_UPDATE_INTERVAL_SECONDS, default=DEF_UPDATE_INTERVAL
            ): NumberSelector(NumberSelectorConfig(min=5, max=600, step=5, mode="box")),
            vol.Optional(
                CONF_SMOOTHING_WINDOW_SECONDS, default=DEF_SMOOTHING_WINDOW
            ): NumberSelector(NumberSelectorConfig(min=0, max=600, step=5, mode="box")),
        }
    )

class SPVMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Validation minimale : PV + HOUSE présents
            missing = [k for k in REQUIRED if not user_input.get(k)]
            if missing:
                for k in missing:
                    errors[k] = "required"
            else:
                return self.async_create_entry(title=DEFAULT_ENTRY_TITLE, data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema_user(self.hass), errors=errors)

class SPVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow (aucune option avancée spécifique pour l’instant)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        # Pour l’instant, on renvoie les données existantes telles quelles.
        return self.async_create_entry(title="", data=self.config_entry.options)

async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return SPVMOptionsFlowHandler(config_entry)
