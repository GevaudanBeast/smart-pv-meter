from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    S_SPVM_EXPECTED_PRODUCTION,
    L_EXPECTED_PRODUCTION,
    UNIT_W, UNIT_KW, KW_TO_W,
    CONF_UNIT_POWER,
)
from .coordinator import SPVMCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SPVMExpectedProduction(coordinator, entry)])


class SPVMExpectedProduction(CoordinatorEntity[SPVMCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-{S_SPVM_EXPECTED_PRODUCTION}"
        self._attr_name = L_EXPECTED_PRODUCTION
        # Always store/display in W to keep math consistent
        self._attr_native_unit_of_measurement = UNIT_W
        self._attr_device_class = "power"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart PV Meter",
            "manufacturer": "SPVM",
            "model": "Internal Solar Model v0.6.0",
        }

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if not data:
            return None
        return round(float(data.expected_w), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if not data:
            return None
        return dict(data.attrs)
