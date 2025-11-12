"""Plateforme sensor SPVM v0.6.0 (autonome).
Expose au minimum: sensor.spvm_expected_production
"""
from __future__ import annotations
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN, DEFAULT_ENTRY_TITLE,
    UNIT_W, UNIT_KW, KW_TO_W,
    S_SPVM_EXPECTED_PRODUCTION, L_EXPECTED_PRODUCTION,
    ATTR_MODEL_TYPE, ATTR_SOURCE, ATTR_DEGRADATION_PCT, ATTR_SYSTEM_EFFICIENCY, ATTR_SITE, ATTR_PANEL, ATTR_NOTE,
    NOTE_SOLAR_MODEL,
    # config keys
    CONF_UNIT_POWER,
    CONF_DEGRADATION_PCT, CONF_SYSTEM_EFFICIENCY,
    CONF_SITE_LATITUDE, CONF_SITE_LONGITUDE, CONF_SITE_ALTITUDE,
    CONF_PANEL_PEAK_POWER, CONF_PANEL_TILT, CONF_PANEL_AZIMUTH,
)
from .coordinator import SPVMCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = SPVMCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([SpvmExpectedProduction(hass, entry, coordinator)], True)

class SpvmExpectedProduction(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = L_EXPECTED_PRODUCTION
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator: SPVMCoordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{S_SPVM_EXPECTED_PRODUCTION}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEFAULT_ENTRY_TITLE,
            manufacturer="SPVM",
            model="v0.6.0",
        )

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        val_w = float(data.get("expected_w", 0.0))
        unit_power = (self.entry.options.get(CONF_UNIT_POWER) or self.entry.data.get(CONF_UNIT_POWER) or UNIT_W)
        if unit_power == UNIT_KW:
            return round(val_w / KW_TO_W, 3)
        return round(val_w, 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.entry.data
        o = self.entry.options
        cfg = lambda k, dv=None: o.get(k, d.get(k, dv))
        return {
            ATTR_MODEL_TYPE: "internal_solar",
            ATTR_SOURCE: NOTE_SOLAR_MODEL,
            ATTR_DEGRADATION_PCT: cfg(CONF_DEGRADATION_PCT),
            ATTR_SYSTEM_EFFICIENCY: cfg(CONF_SYSTEM_EFFICIENCY),
            ATTR_SITE: {
                "lat": cfg(CONF_SITE_LATITUDE),
                "lon": cfg(CONF_SITE_LONGITUDE),
                "alt": cfg(CONF_SITE_ALTITUDE),
            },
            ATTR_PANEL: {
                "peak_w": cfg(CONF_PANEL_PEAK_POWER),
                "tilt_deg": cfg(CONF_PANEL_TILT),
                "azimuth_deg": cfg(CONF_PANEL_AZIMUTH),
            },
            ATTR_NOTE: NOTE_SOLAR_MODEL,
        }

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
