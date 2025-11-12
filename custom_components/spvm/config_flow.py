"""Config flow for Smart PV Meter integration v0.6.0 - Solar Model."""
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

from .const_v06 import (
    # Sensor configs
    CONF_BATTERY_SENSOR,
    CONF_CLOUD_SENSOR,
    CONF_GRID_POWER_SENSOR,
    CONF_HOUSE_SENSOR,
    CONF_HUM_SENSOR,
    CONF_LUX_SENSOR,
    CONF_PV_SENSOR,
    CONF_TEMP_SENSOR,
    # System parameters
    CONF_CAP_MAX_W,
    CONF_DEGRADATION_PCT,
    CONF_RESERVE_W,
    CONF_SMOOTHING_WINDOW,
    CONF_UNIT_POWER,
    CONF_UNIT_TEMP,
    CONF_UPDATE_INTERVAL,
    # Solar model parameters
    CONF_PANEL_AZIMUTH,
    CONF_PANEL_PEAK_POWER,
    CONF_PANEL_TILT,
    CONF_SITE_ALTITUDE,
    CONF_SITE_LATITUDE,
    CONF_SITE_LONGITUDE,
    CONF_SYSTEM_EFFICIENCY,
    # Debug
    CONF_DEBUG_EXPECTED,
    # Defaults
    DEF_CAP_MAX_W,
    DEF_DEBUG_EXPECTED,
    DEF_DEGRADATION_PCT,
    DEF_PANEL_AZIMUTH,
    DEF_PANEL_PEAK_POWER,
    DEF_PANEL_TILT,
    DEF_RESERVE_W,
    DEF_SITE_ALTITUDE,
    DEF_SITE_LATITUDE,
    DEF_SITE_LONGITUDE,
    DEF_SMOOTHING_WINDOW,
    DEF_SYSTEM_EFFICIENCY,
    DEF_UNIT_POWER,
    DEF_UNIT_TEMP,
    DEF_UPDATE_INTERVAL,
    # Other
    CONF_ENTRY_VERSION,
    DEFAULT_ENTRY_TITLE,
    DOMAIN,
    # Sensor IDs for description
    L_GRID_POWER_AUTO,
    L_SURPLUS_NET,
    L_SURPLUS_NET_RAW,
    L_SURPLUS_VIRTUAL,
    L_PV_EFFECTIVE_CAP_NOW_W,
    L_EXPECTED_PRODUCTION,
)


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
    """Handle a config flow for SPVM v0.6.0."""

    VERSION = CONF_ENTRY_VERSION

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Normalize input
            user_input = self._normalize_input(user_input)

            # Create entry
            await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_PV_SENSOR]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=DEFAULT_ENTRY_TITLE,
                data=user_input,
            )

        # Build schema
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
        """Convert to bool properly."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("1", "true", "on", "yes", "oui"):
                return True
            if s in ("0", "false", "off", "no", "non", ""):
                return False
            if s.startswith("sensor."):
                return default
        return default

    @staticmethod
    def _normalize_input(user_input: dict[str, Any]) -> dict[str, Any]:
        """Normalize and validate user input."""
        
        # Debug flag
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
        user_input[CONF_UPDATE_INTERVAL] = int(
            float(user_input.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL))
        )
        user_input[CONF_SMOOTHING_WINDOW] = int(
            float(user_input.get(CONF_SMOOTHING_WINDOW, DEF_SMOOTHING_WINDOW))
        )
        
        # Solar model parameters
        user_input[CONF_PANEL_PEAK_POWER] = int(
            float(user_input.get(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER))
        )
        user_input[CONF_PANEL_TILT] = float(
            user_input.get(CONF_PANEL_TILT, DEF_PANEL_TILT)
        )
        user_input[CONF_PANEL_AZIMUTH] = float(
            user_input.get(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH)
        )
        user_input[CONF_SITE_LATITUDE] = float(
            user_input.get(CONF_SITE_LATITUDE, DEF_SITE_LATITUDE)
        )
        user_input[CONF_SITE_LONGITUDE] = float(
            user_input.get(CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE)
        )
        user_input[CONF_SITE_ALTITUDE] = float(
            user_input.get(CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE)
        )
        user_input[CONF_SYSTEM_EFFICIENCY] = float(
            user_input.get(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY)
        )

        return user_input

    @staticmethod
    def _get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        """Get configuration schema."""
        if defaults is None:
            defaults = {}

        debug_default = SPVMConfigFlow._coerce_bool(
            defaults.get(CONF_DEBUG_EXPECTED, DEF_DEBUG_EXPECTED), DEF_DEBUG_EXPECTED
        )

        return vol.Schema(
            {
                # ========== Required sensors ==========
                vol.Required(
                    CONF_PV_SENSOR, default=defaults.get(CONF_PV_SENSOR, "")
                ): _entity_selector("sensor"),
                vol.Required(
                    CONF_HOUSE_SENSOR, default=defaults.get(CONF_HOUSE_SENSOR, "")
                ): _entity_selector("sensor"),
                
                # ========== Optional sensors ==========
                vol.Optional(
                    CONF_GRID_POWER_SENSOR,
                    default=defaults.get(CONF_GRID_POWER_SENSOR, ""),
                ): _entity_selector("sensor"),
                vol.Optional(
                    CONF_BATTERY_SENSOR,
                    default=defaults.get(CONF_BATTERY_SENSOR, ""),
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
                vol.Optional(
                    CONF_CLOUD_SENSOR, default=defaults.get(CONF_CLOUD_SENSOR, "")
                ): _entity_selector("sensor"),
                
                # ========== System parameters ==========
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
                
                # ========== Solar model parameters ==========
                vol.Optional(
                    CONF_PANEL_PEAK_POWER,
                    default=defaults.get(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER),
                ): _number_selector(100, 20000, 50),
                vol.Optional(
                    CONF_PANEL_TILT,
                    default=defaults.get(CONF_PANEL_TILT, DEF_PANEL_TILT),
                ): _number_selector(0, 90, 1),
                vol.Optional(
                    CONF_PANEL_AZIMUTH,
                    default=defaults.get(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH),
                ): _number_selector(0, 360, 5),
                vol.Optional(
                    CONF_SITE_LATITUDE,
                    default=defaults.get(CONF_SITE_LATITUDE, DEF_SITE_LATITUDE),
                ): _number_selector(-90, 90, 0.0001),
                vol.Optional(
                    CONF_SITE_LONGITUDE,
                    default=defaults.get(CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE),
                ): _number_selector(-180, 180, 0.0001),
                vol.Optional(
                    CONF_SITE_ALTITUDE,
                    default=defaults.get(CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE),
                ): _number_selector(0, 5000, 10),
                vol.Optional(
                    CONF_SYSTEM_EFFICIENCY,
                    default=defaults.get(CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY),
                ): _number_selector(0.5, 1.0, 0.01),
                
                # ========== Update & smoothing ==========
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=defaults.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL),
                ): _number_selector(10, 300, 5),
                vol.Optional(
                    CONF_SMOOTHING_WINDOW,
                    default=defaults.get(CONF_SMOOTHING_WINDOW, DEF_SMOOTHING_WINDOW),
                ): _number_selector(10, 180, 5),
                
                # ========== Units ==========
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
                
                # ========== Debug ==========
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
• sensor.{L_GRID_POWER_AUTO.lower().replace(' ', '_').replace('-', '')}
• sensor.{L_SURPLUS_VIRTUAL.lower().replace(' ', '_').replace('-', '')}
• sensor.{L_SURPLUS_NET_RAW.lower().replace(' ', '_').replace('-', '')}
• sensor.{L_SURPLUS_NET.lower().replace(' ', '_').replace('-', '')}
• sensor.{L_PV_EFFECTIVE_CAP_NOW_W.lower().replace(' ', '_').replace('-', '')}
• sensor.{L_EXPECTED_PRODUCTION.lower().replace(' ', '_').replace('-', '')}

For Solar Optimizer, use: sensor.spvm_surplus_net
(150W Zendure reserve and 3kW cap already applied)

v0.6.0: Uses solar physics model instead of k-NN
"""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SPVMOptionsFlowHandler(config_entry)


class SPVMOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SPVM v0.6.0."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Normalize input
            user_input = SPVMConfigFlow._normalize_input(user_input)
            return self.async_create_entry(title="", data=user_input)

        # Merge data and options for defaults
        defaults = {**self.config_entry.data, **self.config_entry.options}

        # Build schema with current values as defaults
        schema = SPVMConfigFlow._get_config_schema(defaults)

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "created_entities": SPVMConfigFlow._get_entities_description(),
            },
        )
