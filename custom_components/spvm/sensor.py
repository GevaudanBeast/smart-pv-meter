"""Capteurs SPVM."""
from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN, NAME, MANUFACTURER, HARD_CAP_W,
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_RESERVE_W, CONF_UNIT_POWER, CONF_CAP_MAX_W, CONF_DEGRADATION_PCT,
    CONF_SMOOTHING_WINDOW, CONF_DEBUG_EXPECTED,
    DEF_RESERVE_W, DEF_UNIT_POWER, DEF_CAP_MAX_W, DEF_DEGRADATION_PCT, DEF_SMOOTHING_WINDOW,
    UNIT_W, UNIT_KW,
    S_SPVM_SURPLUS_VIRTUAL, S_SPVM_SURPLUS_NET_RAW, S_SPVM_SURPLUS_NET,
    S_SPVM_GRID_POWER_AUTO, S_SPVM_EXPECTED_SIMILAR, S_SPVM_PV_EFFECTIVE_CAP_NOW_W, S_SPVM_EXPECTED_DEBUG,
    L_SURPLUS_VIRTUAL, L_SURPLUS_NET_RAW, L_SURPLUS_NET, L_GRID_POWER_AUTO,
    L_EXPECTED_SIMILAR, L_PV_EFFECTIVE_CAP_NOW_W, L_EXPECTED_DEBUG,
    ATTR_SOURCE, ATTR_PV_W, ATTR_PV_KW, ATTR_HOUSE_W, ATTR_BATTERY_W, ATTR_GRID_W,
    ATTR_RESERVE_W, ATTR_CAP_MAX_W, ATTR_CAP_LIMIT_W, ATTR_DEGRADATION_PCT,
    ATTR_NOTE, ATTR_SMOOTHED, ATTR_WINDOW_S,
    SOURCE_GRID_AUTO, SOURCE_SURPLUS_VIRTUAL, SOURCE_SURPLUS_NET,
    NOTE_RESERVE, NOTE_CAP, NOTE_HARD_CAP,
)
from .coordinator import SPVMCoordinator
from .helpers import (
    state_to_float, convert_to_w, clamp, rolling_average,
    merge_config_options, format_timestamp
)

_LOGGER = logging.getLogger(__name__)


class BaseSPVMSensor(SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, object_id: str, name: str,
                 unit: str | None = None, device_class: SensorDeviceClass | None = None,
                 state_class: SensorStateClass | None = None):
        self.entry = entry
        self._object_id = slugify(object_id)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}:{entry.entry_id}:{self._object_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": MANUFACTURER,
            "model": "SPVM Sensor Suite",
        }


class ComputedPowerSensor(BaseSPVMSensor):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, object_id: str, name: str, deps: list[str]):
        super().__init__(entry, object_id, name, UNIT_W, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT)
        self.hass = hass
        self._deps = deps
        self.config = merge_config_options(entry.data, entry.options)

    async def async_added_to_hass(self) -> None:
        if self._deps:
            async_track_state_change_event(self.hass, self._deps, self._handle_change)
        self._recompute()

    @callback
    def _handle_change(self, event) -> None:
        self._recompute()

    def _recompute(self) -> None:
        value, attrs = self._compute()
        self._attr_native_value = value
        self._attr_extra_state_attributes = attrs
        self.async_write_ha_state()

    def _compute(self) -> tuple[float | None, dict[str, Any]]:
        return None, {}


class GridPowerAutoSensor(ComputedPowerSensor):
    def _compute(self) -> tuple[float, dict[str, Any]]:
        pv_entity = self.config.get(CONF_PV_SENSOR)
        house_entity = self.config.get(CONF_HOUSE_SENSOR)
        batt_entity = self.config.get(CONF_BATTERY_SENSOR)
        unit_power = self.config.get(CONF_UNIT_POWER, DEF_UNIT_POWER)

        pv_raw = state_to_float(self.hass.states.get(pv_entity))
        pv_w = convert_to_w(pv_raw, unit_power)
        house_w = state_to_float(self.hass.states.get(house_entity))
        batt_w = state_to_float(self.hass.states.get(batt_entity)) if batt_entity else 0.0
        grid_w = house_w - pv_w - batt_w

        attrs = {
            ATTR_SOURCE: SOURCE_GRID_AUTO,
            ATTR_PV_W: round(pv_w, 3),
            ATTR_HOUSE_W: round(house_w, 3),
            ATTR_BATTERY_W: round(batt_w, 3),
            ATTR_GRID_W: round(grid_w, 3),
        }
        if unit_power == UNIT_KW:
            attrs[ATTR_PV_KW] = round(pv_w / 1000.0, 6)
        return round(grid_w, 3), attrs


class SurplusVirtualSensor(ComputedPowerSensor):
    def _compute(self) -> tuple[float, dict[str, Any]]:
        pv_entity = self.config.get(CONF_PV_SENSOR)
        house_entity = self.config.get(CONF_HOUSE_SENSOR)
        grid_entity = self.config.get(CONF_GRID_POWER_SENSOR)
        unit_power = self.config.get(CONF_UNIT_POWER, DEF_UNIT_POWER)

        pv_raw = state_to_float(self.hass.states.get(pv_entity))
        pv_w = convert_to_w(pv_raw, unit_power)
        house_w = state_to_float(self.hass.states.get(house_entity))

        if grid_entity:
            grid_w = state_to_float(self.hass.states.get(grid_entity))
            export = max(-grid_w, 0.0)
        else:
            export = 0.0
            grid_w = 0.0

        surplus = max(export, pv_w - house_w)

        attrs = {
            ATTR_SOURCE: SOURCE_SURPLUS_VIRTUAL,
            ATTR_PV_W: round(pv_w, 3),
            ATTR_HOUSE_W: round(house_w, 3),
            ATTR_GRID_W: round(grid_w, 3),
        }
        return round(max(surplus, 0.0), 3), attrs


class SurplusNetRawSensor(ComputedPowerSensor):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, surplus_sensor: SurplusVirtualSensor):
        # Listen to surplus_virtual sensor changes
        surplus_entity_id = f"sensor.{S_SPVM_SURPLUS_VIRTUAL}"
        super().__init__(hass, entry, S_SPVM_SURPLUS_NET_RAW, L_SURPLUS_NET_RAW, [surplus_entity_id])
        self.surplus_sensor = surplus_sensor

    def _compute(self) -> tuple[float, dict[str, Any]]:
        surplus_v, _ = self.surplus_sensor._compute()
        reserve_w = int(self.config.get(CONF_RESERVE_W, DEF_RESERVE_W))
        net_raw = max(surplus_v - reserve_w, 0.0)
        return round(net_raw, 3), {ATTR_SOURCE: SOURCE_SURPLUS_NET, ATTR_RESERVE_W: reserve_w, ATTR_NOTE: NOTE_RESERVE}


class SurplusNetSensor(ComputedPowerSensor):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, raw_sensor: SurplusNetRawSensor):
        # Listen to surplus_net_raw sensor changes
        raw_entity_id = f"sensor.{S_SPVM_SURPLUS_NET_RAW}"
        super().__init__(hass, entry, S_SPVM_SURPLUS_NET, L_SURPLUS_NET, [raw_entity_id])
        self.raw_sensor = raw_sensor
        self._history: deque[float] = deque(maxlen=20)

    def _compute(self) -> tuple[float, dict[str, Any]]:
        net_raw, _ = self.raw_sensor._compute()
        cap_max_w = int(self.config.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W))
        smoothing_window = int(self.config.get(CONF_SMOOTHING_WINDOW, DEF_SMOOTHING_WINDOW))
        net_capped = min(net_raw, min(cap_max_w, HARD_CAP_W))
        self._history.append(net_capped)
        window_size = max(1, smoothing_window // 15)
        net_smoothed = rolling_average(list(self._history), window_size)
        net_final = max(net_smoothed, 0.0)
        reserve_w = int(self.config.get(CONF_RESERVE_W, DEF_RESERVE_W))
        return round(net_final, 3), {
            ATTR_SOURCE: SOURCE_SURPLUS_NET,
            ATTR_RESERVE_W: reserve_w,
            ATTR_CAP_MAX_W: cap_max_w,
            ATTR_CAP_LIMIT_W: HARD_CAP_W,
            ATTR_SMOOTHED: True,
            ATTR_WINDOW_S: smoothing_window,
            ATTR_NOTE: f"{NOTE_RESERVE}; {NOTE_CAP}; {NOTE_HARD_CAP}",
        }


class PVEffectiveCapSensor(BaseSPVMSensor):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(entry, S_SPVM_PV_EFFECTIVE_CAP_NOW_W, L_PV_EFFECTIVE_CAP_NOW_W,
                         UNIT_W, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT)
        self.hass = hass
        self.config = merge_config_options(entry.data, entry.options)

    async def async_added_to_hass(self) -> None:
        self._recompute()

    def _recompute(self) -> None:
        cap_max_w = int(self.config.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W))
        degradation_pct = float(self.config.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT))
        effective = cap_max_w * (1.0 - degradation_pct / 100.0)
        effective = clamp(effective, 0, HARD_CAP_W)
        self._attr_native_value = round(effective, 3)
        self._attr_extra_state_attributes = {
            ATTR_CAP_MAX_W: cap_max_w,
            ATTR_DEGRADATION_PCT: degradation_pct,
            ATTR_CAP_LIMIT_W: HARD_CAP_W,
        }
        self.async_write_ha_state()


class ExpectedSimilarSensor(CoordinatorEntity, BaseSPVMSensor):
    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry):
        CoordinatorEntity.__init__(self, coordinator)
        BaseSPVMSensor.__init__(self, entry, S_SPVM_EXPECTED_SIMILAR, L_EXPECTED_SIMILAR,
                                 UNIT_KW, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT)

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("expected_kw")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        debug_info = self.coordinator.data.get("debug_info", {})
        knn_config = self.coordinator.data.get("knn_config", {})
        return {
            ATTR_SOURCE: "k-NN prediction",
            "expected_w": self.coordinator.data.get("expected_w"),
            "method": debug_info.get("method"),
            "neighbors": debug_info.get("neighbors"),
            "samples_total": debug_info.get("samples_total"),
            "k": knn_config.get("k"),
            "window_min_minutes": knn_config.get("window_min"),
            "window_max_minutes": knn_config.get("window_max"),
            "weights": knn_config.get("weights"),
            "last_update": format_timestamp(datetime.now()),
        }


class ExpectedDebugSensor(CoordinatorEntity, BaseSPVMSensor):
    def __init__(self, coordinator: SPVMCoordinator, entry: ConfigEntry):
        CoordinatorEntity.__init__(self, coordinator)
        BaseSPVMSensor.__init__(self, entry, S_SPVM_EXPECTED_DEBUG, L_EXPECTED_DEBUG)

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "N/A"
        return json.dumps(self.coordinator.data.get("debug_info", {}), indent=2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return {"full_data": self.coordinator.data, "last_update": format_timestamp(datetime.now())}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = merge_config_options(entry.data, entry.options)
    pv_entity = config.get(CONF_PV_SENSOR)
    house_entity = config.get(CONF_HOUSE_SENSOR)
    grid_entity = config.get(CONF_GRID_POWER_SENSOR)
    batt_entity = config.get(CONF_BATTERY_SENSOR)
    debug_enabled = config.get(CONF_DEBUG_EXPECTED, False)

    entities: list[SensorEntity] = []
    deps_grid = [e for e in [pv_entity, house_entity, batt_entity] if e]
    entities.append(GridPowerAutoSensor(hass, entry, S_SPVM_GRID_POWER_AUTO, L_GRID_POWER_AUTO, deps_grid))
    deps_surplus = [e for e in [pv_entity, house_entity, grid_entity] if e]
    surplus_sensor = SurplusVirtualSensor(hass, entry, S_SPVM_SURPLUS_VIRTUAL, L_SURPLUS_VIRTUAL, deps_surplus)
    entities.append(surplus_sensor)
    raw_sensor = SurplusNetRawSensor(hass, entry, surplus_sensor)
    entities.append(raw_sensor)
    entities.append(SurplusNetSensor(hass, entry, raw_sensor))
    entities.append(PVEffectiveCapSensor(hass, entry))
    entities.append(ExpectedSimilarSensor(coordinator, entry))
    if debug_enabled:
        entities.append(ExpectedDebugSensor(coordinator, entry))
    async_add_entities(entities)
