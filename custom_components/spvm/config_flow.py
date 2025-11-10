"""Config flow for Smart PV Meter integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
)

from .const import (
    CONF_BATTERY_SENSOR,
    CONF_CAP_MAX_W,
    CONF_DEBUG_EXPECTED,
    CONF_DEGRADATION_PCT,
    CONF_ENTRY_VERSION,
    CONF_EXPECTED_SENSOR,
    CONF_GRID_POWER_SENSOR,
    CONF_HOUSE_SENSOR,
    CONF_HUM_SENSOR,
    CONF_KNN_K,
    CONF_KNN_WEIGHT_ELEV,
    CONF_KNN_WEIGHT_HUM,
    CONF_KNN_WEIGHT_LUX,
    CONF_KNN_WEIGHT_TEMP,
    CONF_KNN_WINDOW_MAX,
    CONF_KNN_WINDOW_MIN,
    CONF_LUX_SENSOR,
    CONF_PV_SENSOR,
    CONF_RESERVE_W,
    CONF_SMOOTHING_WINDOW,
    CONF_TEMP_SENSOR,
    CONF_UNIT_POWER,
    CONF_UNIT_TEMP,
    CONF_UPDATE_INTERVAL,
    DEF_CAP_MAX_W,
    DEF_DEBUG_EXPECTED,
    DEF_DEGRADATION_PCT,
    DEF_KNN_K,
    DEF_KNN_WEIGHT_ELEV,
    DEF_KNN_WEIGHT_HUM,
    DEF_KNN_WEIGHT_LUX,
    DEF_KNN_WEIGHT_TEMP,
    DEF_KNN_WINDOW_MAX,
    DEF_KNN_WINDOW_MIN,
    DEF_RESERVE_W,
    DEF_SMOOTHING_WINDOW,
    DEF_UNIT_POWER,
    DEF_UNIT_TEMP,
    DEF_UPDATE_INTERVAL,
    DEFAULT_ENTRY_TITLE,
    DOMAIN,
    L_EXPECTED_SIMILAR,
    L_GRID_POWER_AUTO,
    L_PV_EFFECTIVE_CAP_NOW_W,
    L_SURPLUS_NET,
    L_SURPLUS_NET_RAW,
    L_SURPLUS_VIRTUAL,
)

# Valeurs par défaut centralisées
_EXPECTED_DEFAULT = "sensor.spvm_expected_similar"


def _entity_selector(domain: str | None = None) -> EntitySelector:
    """Create entity selector."""
    return EntitySelector(
        EntitySelectorConfig(domain=[domain] if domain else None, multiple=False)
    )


def _number_selector(
    mini: float,
    maxi: float,
    step: float,
    mode: NumberSelectorMode = NumberSelectorMode.BOX,
) -> NumberSelector:
    """Create number selector."""
    return NumberSelector(
        NumberSelectorConfig(min=mini, max=maxi, step=step, mode=mode)
    )


class SPVMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SPVM."""

    VERSION = CONF_ENTRY_VERSION

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Normalisation/validation (inclut défaut expected_sensor + bool debug)
            user_input = self._normalize_input(user_input)

            # Create entry
            await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_PV_SENSOR]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=DEFAULT_ENTRY_TITLE,
                data=user_input,
            )

        # Build schema (avec défauts visibles)
        schema = self._get_config_schema()

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={
                "created_entities": self._get_entities_description(),
            },
        )

    @staticmethod
    def _coerce_bool(value: Any, default: bool = False) -> bool:
        """Convertit proprement vers bool (gère str/bool/entité héritée)."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("1", "true", "on", "yes", "oui"):
                return True
            if s in ("0", "false", "off", "no", "non", ""):
                return False
            # ancien bug: une entité 'sensor.xxx' stockée par erreur -> considérer False
            if s.startswith("sensor."):
                return default
        return default

    @staticmethod
    def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
        """Normalize and validate user input."""
        # expected_sensor: injecte la valeur par défaut si vide/non défini
        if not user_input.get(CONF_EXPECTED_SENSOR):
            user_input[CONF_EXPECTED_SENSOR] = _EXPECTED_DEFAULT

        # debug_expected: doit être un booléen (pas une entité)
        user_input[CONF_DEBUG_EXPECTED] = SPVMConfigFlow._coerce_bool(
            user_input.get(CONF_DEBUG_EXPECTED, DEF_DEBUG_EXPECTED), DEF_DEBUG_EXPECTED
        )

        # Validate power unit
        if user_input.get(CONF_UNIT_POWER) not in ("W", "kW"):
            user_input[CONF_UNIT_POWER] = DEF_UNIT_POWER

        # Validate temperature unit
        if user_input.get(CONF_UNIT_TEMP) not in ("°C", "°F"):
            user_input[CONF_UNIT_TEMP] = DEF_UNIT_TEMP

        # Convert numeric values safely
        user_input[CONF_RESERVE_W] = int(
            float(user_input.get(CONF_RESERVE_W, DEF_RESERVE_W))
        )
        user_input[CONF_CAP_MAX_W] = int(
            float(user_input.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W))
        )
        user_input[CONF_DEGRADATION_PCT] = float(
            user_input.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)
        )
        user_input[CONF_KNN_K] = int(float(user_input.get(CONF_KNN_K, DEF_KNN_K)))
        user_input[CONF_UPDATE_INTERVAL] = int(
            float(user_input.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL))
        )
        user_input[CONF_SMOOTHING_WINDOW] = int(
            float(user_input.get(CONF_SMOOTHING_WINDOW, DEF_SMOOTHING_WINDOW))
        )

        return user_input

    @staticmethod
    def _get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        """Get configuration schema."""
        if defaults is None:
            defaults = {}

        # Valeurs par défaut visibles dans le formulaire
        expected_default = defaults.get(CONF_EXPECTED_SENSOR, _EXPECTED_DEFAULT)
        debug_default = SPVMConfigFlow._coerce_bool(
            defaults.get(CONF_DEBUG_EXPECTED, DEF_DEBUG_EXPECTED), DEF_DEBUG_EXPECTED
        )

        return vol.Schema(
            {
                # Required sensors
                vol.Required(
                    CONF_PV_SENSOR, default=defaults.get(CONF_PV_SENSOR, "")
                ): _entity_selector("sensor"),
                vol.Required(
                    CONF_HOUSE_SENSOR, default=defaults.get(CONF_HOUSE_SENSOR, "")
                ): _entity_selector("sensor"),
                # Optional sensors
                vol.Optional(
                    CONF_GRID_POWER_SENSOR,
                    default=defaults.get(CONF_GRID_POWER_SENSOR, ""),
                ): _entity_selector("sensor"),
                vol.Optional(
                    CONF_BATTERY_SENSOR,
                    default=defaults.get(CONF_BATTERY_SENSOR, ""),
                ): _entity_selector("sensor"),
                # expected_sensor optionnel + défaut interne
                vol.Optional(
                    CONF_EXPECTED_SENSOR,
                    default=expected_default,
                ): _entity_selector("sensor"),
                vol.Optional(
                    CONF_LUX_SENSOR, default=defaults.get(CONF_LUX_SENSOR, "")
                ): _entity_selector("sensor"),
                vol.Optional(
                    CONF_TEMP_SENSOR, default=defaults.get(CONF_TEMP_SENSOR, "")
                ): _entity_selector("sensor"),
                vol.Optional(
                    CONF_HUM_SENSOR, default=defaults.get(CONF_HUM_SENSOR, "")
                ): _entity_selector("sensor"),
                # System parameters
                vol.Optional(
                    CONF_RESERVE_W, default=defaults.get(CONF_RESERVE_W, DEF_RESERVE_W)
                ): _number_selector(0, 2000, 10),
                vol.Optional(
                    CONF_CAP_MAX_W, default=defaults.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W)
                ): _number_selector(0, 10000, 50),
                vol.Optional(
                    CONF_DEGRADATION_PCT,
                    default=defaults.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT),
                ): _number_selector(0, 100, 0.5),
                # k-NN parameters
                vol.Optional(
                    CONF_KNN_K, default=defaults.get(CONF_KNN_K, DEF_KNN_K)
                ): _number_selector(1, 20, 1),
                vol.Optional(
                    CONF_KNN_WINDOW_MIN,
                    default=defaults.get(CONF_KNN_WINDOW_MIN, DEF_KNN_WINDOW_MIN),
                ): _number_selector(10, 120, 5),
                vol.Optional(
                    CONF_KNN_WINDOW_MAX,
                    default=defaults.get(CONF_KNN_WINDOW_MAX, DEF_KNN_WINDOW_MAX),
                ): _number_selector(30, 240, 5),
                vol.Optional(
                    CONF_KNN_WEIGHT_LUX,
                    default=defaults.get(CONF_KNN_WEIGHT_LUX, DEF_KNN_WEIGHT_LUX),
                ): _number_selector(0, 1, 0.05),
                vol.Optional(
                    CONF_KNN_WEIGHT_TEMP,
                    default=defaults.get(CONF_KNN_WEIGHT_TEMP, DEF_KNN_WEIGHT_TEMP),
                ): _number_selector(0, 1, 0.05),
                vol.Optional(
                    CONF_KNN_WEIGHT_HUM,
                    default=defaults.get(CONF_KNN_WEIGHT_HUM, DEF_KNN_WEIGHT_HUM),
                ): _number_selector(0, 1, 0.05),
                vol.Optional(
                    CONF_KNN_WEIGHT_ELEV,
                    default=defaults.get(CONF_KNN_WEIGHT_ELEV, DEF_KNN_WEIGHT_ELEV),
                ): _number_selector(0, 1, 0.05),
                # Update & smoothing
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=defaults.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL),
                ): _number_selector(10, 300, 5),
                vol.Optional(
                    CONF_SMOOTHING_WINDOW,
                    default=defaults.get(CONF_SMOOTHING_WINDOW, DEF_SMOOTHING_WINDOW),
                ): _number_selector(10, 180, 5),
                # Units
                vol.Optional(
                    CONF_UNIT_POWER,
                    default=defaults.get(CONF_UNIT_POWER, DEF_UNIT_POWER),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value="W", label="W"),
                            SelectOptionDict(value="kW", label="kW"),
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(
                    CONF_UNIT_TEMP,
                    default=defaults.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value="°C", label="°C"),
                            SelectOptionDict(value="°F", label="°F"),
                        ],
                        mode="dropdown",
                    )
                ),
                # Debug (booléen, plus une entité)
                vol.Optional(
                    CONF_DEBUG_EXPECTED,
                    default=debug_default,
                ): bool,
            }
        )

    @staticmethod
    def _get_entities_description() -> str:
        """Get description of entities that will be created."""
        return f"""
Entities that will be created:
• sensor.{L_GRID_POWER_AUTO.lower().replace(' ', '_').replace('—', '')}
• sensor.{L_SURPLUS_VIRTUAL.lower().replace(' ', '_').replace('—', '')}
• sensor.{L_SURPLUS_NET_RAW.lower().replace(' ', '_').replace('—', '')}
• sensor.{L_SURPLUS_NET.lower().replace(' ', '_').replace('—', '')}
• sensor.{L_PV_EFFECTIVE_CAP_NOW_W.lower().replace(' ', '_').replace('—', '')}
• sensor.{L_EXPECTED_SIMILAR.lower().replace(' ', '_').replace('—', '')}

For Solar Optimizer, use: sensor.spvm_surplus_net
(150W Zendure reserve and 3kW cap already applied)
"""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SPVMOptionsFlowHandler(config_entry)


class SPVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SPVM."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Normalisation (inclut défaut expected_sensor + bool debug)
            user_input = SPVMConfigFlow._normalize_input(user_input)
            return self.async_create_entry(title="", data=user_input)

        # Merge data and options for defaults
        defaults = {**self.config_entry.data, **self.config_entry.options}

        # S'assure que le défaut attendu est visible dans le formulaire d'options
        if not defaults.get(CONF_EXPECTED_SENSOR):
            defaults[CONF_EXPECTED_SENSOR] = _EXPECTED_DEFAULT

        # Build schema with current values as defaults
        schema = SPVMConfigFlow._get_config_schema(defaults)

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "created_entities": SPVMConfigFlow._get_entities_description(),
            },
        )
