"""Coordinator SPVM v0.6.0 (autonome).
- Lit la config d'entrée
- Calcule la production attendue interne (expected.py)
"""
from __future__ import annotations
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL_SECONDS,
    DEF_UPDATE_INTERVAL,
)
from .expected import compute_expected_w

class SPVMCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass = hass
        self.entry = entry
        interval = float(entry.options.get(CONF_UPDATE_INTERVAL_SECONDS, entry.data.get(CONF_UPDATE_INTERVAL_SECONDS, DEF_UPDATE_INTERVAL)))
        super().__init__(
            hass,
            logger=hass.logger.getChild(DOMAIN),
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=max(10, int(interval))),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            now = self.hass.now()
            cfg = {**self.entry.data, **self.entry.options}
            expected_w = compute_expected_w(self.hass, cfg, now)
            return {"expected_w": expected_w, "ts": now.isoformat()}
        except Exception as err:
            raise UpdateFailed(str(err)) from err
