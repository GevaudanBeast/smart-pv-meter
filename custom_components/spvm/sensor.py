from __future__ import annotations

from typing import Any, Optional, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    # expected
    S_SPVM_EXPECTED_PRODUCTION, L_EXPECTED_PRODUCTION, UNIT_W,
    # yield
    S_SPVM_YIELD_RATIO, L_YIELD_RATIO, UNIT_PERCENT,
    # surplus
    S_SPVM_SURPLUS_NET, L_SURPLUS_NET,
)
from .coordinator import SPVMCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SPVMExpectedProduction(coordinator, entry),
        SPVMYieldRatio(coordinator, entry),
        SPVMSurplusNet(coordinator, entry),
    ])


class _Base(CoordinatorEntity[SPVMCoordinator], SensorEntity):
    _attr_has_entity_name = False  # Noms courts: sensor.spvm_xxx

    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry, unique_suffix: str, name: str, entity_id_suffix: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-{unique_suffix}"
        self._attr_name = name
        # Suggestion d'entity_id court
        self._attr_suggested_object_id = f"spvm_{entity_id_suffix}"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart PV Meter",
            "manufacturer": "SPVM",
            "model": "Physical Solar Model v0.6.3",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        d = self.coordinator.data
        if not d:
            return None
        return dict(d.attrs)


class SPVMExpectedProduction(_Base):
    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, S_SPVM_EXPECTED_PRODUCTION, L_EXPECTED_PRODUCTION, "expected_production")
        self._attr_native_unit_of_measurement = UNIT_W
        self._attr_device_class = "power"

    @property
    def native_value(self) -> float | None:
        d = self.coordinator.data
        if not d:
            return None
        return round(float(d.expected_w), 1)


class SPVMYieldRatio(_Base):
    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, S_SPVM_YIELD_RATIO, L_YIELD_RATIO, "yield_ratio")
        self._attr_native_unit_of_measurement = UNIT_PERCENT

    @property
    def native_value(self) -> float | None:
        d = self.coordinator.data
        if not d or d.yield_ratio_pct is None:
            return None
        return round(float(d.yield_ratio_pct), 1)


class SPVMSurplusNet(_Base):
    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, S_SPVM_SURPLUS_NET, L_SURPLUS_NET, "surplus_net")
        self._attr_native_unit_of_measurement = UNIT_W
        self._attr_device_class = "power"

    @property
    def native_value(self) -> float | None:
        d = self.coordinator.data
        if not d or d.surplus_net_w is None:
            return None
        return round(float(d.surplus_net_w), 1)
