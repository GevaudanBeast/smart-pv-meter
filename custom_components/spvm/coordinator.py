from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    # config keys
    CONF_PV_SENSOR, CONF_HOUSE_SENSOR, CONF_GRID_POWER_SENSOR, CONF_BATTERY_SENSOR,
    CONF_EXPECTED_SENSOR, CONF_RESERVE_W, CONF_CAP_MAX_W, CONF_HARD_CAP_W,
    CONF_DEGRADATION_PCT, CONF_UPDATE_INTERVAL, CONF_UNIT_POWER,
    # defaults
    DEF_RESERVE_W, DEF_CAP_MAX_W, DEF_HARD_CAP_W, DEF_DEGRADATION_PCT, DEF_UPDATE_INTERVAL, DEF_UNIT_POWER,
)
from .expected import ExpectedProductionCalculator, ExpectedInputs


def _state_as_float(hass: HomeAssistant, entity_id: str | None, default: float = 0.0) -> float:
    if not entity_id:
        return default
    st = hass.states.get(entity_id)
    if st is None or st.state in ("unknown", "unavailable", None):
        return default
    try:
        return float(st.state)
    except (ValueError, TypeError):
        return default


def _to_watts(value: float, unit_power: str) -> float:
    return value * 1000.0 if unit_power == "kW" else value


def _compute_effective_cap(entry: ConfigEntry) -> int:
    user_cap = int(entry.options.get(CONF_CAP_MAX_W, entry.data.get(CONF_CAP_MAX_W, DEF_CAP_MAX_W)))
    sys_cap = int(entry.options.get(CONF_HARD_CAP_W, entry.data.get(CONF_HARD_CAP_W, DEF_HARD_CAP_W)))
    return min(user_cap, sys_cap) if sys_cap > 0 else user_cap


class SPVMCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator principal SPVM (utilisé par la plateforme sensor)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._calc = ExpectedProductionCalculator(hass)
        self._cache_cleared_flag = False  # indicateur simple pour reset
        interval = int(entry.options.get(CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL)))
        super().__init__(hass, hass.logger, name=DOMAIN, update_interval=timedelta(seconds=interval))

    def reset_cache(self) -> None:
        """Reset any internal caches used by expected production."""
        self._cache_cleared_flag = True
        if hasattr(self._calc, "reset"):
            try:
                self._calc.reset()  # no-op si non implémenté
            except Exception:  # noqa: BLE001
                pass

    async def _async_update_data(self) -> dict[str, Any]:
        hass = self.hass
        data: dict[str, Any] = {}

        unit_power = self.entry.options.get(CONF_UNIT_POWER, self.entry.data.get(CONF_UNIT_POWER, DEF_UNIT_POWER))

        pv_eid = self.entry.data.get(CONF_PV_SENSOR)
        house_eid = self.entry.data.get(CONF_HOUSE_SENSOR)
        grid_eid = self.entry.data.get(CONF_GRID_POWER_SENSOR)
        batt_eid = self.entry.data.get(CONF_BATTERY_SENSOR)
        expected_eid = self.entry.data.get(CONF_EXPECTED_SENSOR)

        pv = _to_watts(_state_as_float(hass, pv_eid), unit_power)
        house = _to_watts(_state_as_float(hass, house_eid), unit_power)
        grid = _to_watts(_state_as_float(hass, grid_eid, 0.0), unit_power)
        batt = _to_watts(_state_as_float(hass, batt_eid, 0.0), unit_power)

        reserve = int(self.entry.options.get(CONF_RESERVE_W, self.entry.data.get(CONF_RESERVE_W, DEF_RESERVE_W)))
        reserve = max(reserve, 0)

        degradation_pct = float(self.entry.options.get(CONF_DEGRADATION_PCT, self.entry.data.get(CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)))
        cap_effective_now = int(_compute_effective_cap(self.entry) * (1.0 - max(0.0, degradation_pct) / 100.0))

        # Calculs principaux
        grid_power_auto = house - pv - batt
        export = max(-grid, 0.0)
        surplus_virtual = max(export, pv - house)
        surplus_net_raw = max(surplus_virtual - reserve, 0.0)
        surplus_net = surplus_net_raw

        # Production attendue (capteur externe prioritaire sinon fallback)
        expected_now = 0.0
        if expected_eid:
            expected_now = _to_watts(_state_as_float(hass, expected_eid, 0.0), unit_power)
        else:
            try:
                exp_inputs = ExpectedInputs(pv_entity=pv_eid)
                expected_now = float(self._calc.expected_now(exp_inputs))
            except RuntimeError as no_hist:
                self.logger.debug("SPVM expected: %s", no_hist)  # No historical data available
                expected_now = 0.0
            except ValueError as bad_arg:
                self.logger.warning("SPVM expected: %s", bad_arg)  # entity_id must be provided
                expected_now = 0.0
            except Exception as err:  # noqa: BLE001
                self.logger.exception("SPVM expected: unexpected error: %s", err)
                expected_now = 0.0

        data.update(
            pv=pv,
            house=house,
            grid=grid,
            batt=batt,
            reserve=reserve,
            grid_power_auto=grid_power_auto,
            surplus_virtual=surplus_virtual,
            surplus_net_raw=surplus_net_raw,
            surplus_net=surplus_net,
            cap_effective_now_w=cap_effective_now,
            expected=expected_now,
            cache_reset=self._cache_cleared_flag,
        )
        # on réarme le flag après un cycle
        self._cache_cleared_flag = False
        return data
