"""Data update coordinator for SPVM expected production (v0.6.0 - Solar Model)."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const_v06 import (
    CONF_UPDATE_INTERVAL,
    DEF_UPDATE_INTERVAL,
    DOMAIN,
)
from .expected_v06 import ExpectedProductionCalculator

_LOGGER = logging.getLogger(__name__)


class SPVMCoordinator(DataUpdateCoordinator):
    """SPVM data coordinator for expected production calculation (Solar Model)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self._calculator: ExpectedProductionCalculator | None = None
        
        # Get update interval from config
        update_interval = timedelta(
            seconds=entry.data.get(CONF_UPDATE_INTERVAL, DEF_UPDATE_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=update_interval,
        )
        
        _LOGGER.info(
            "SPVM Coordinator initialized with solar model (update_interval=%ss)",
            update_interval.total_seconds(),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data - calculate expected production."""
        try:
            # Get configuration
            config = self._get_config()
            
            # Initialize calculator if needed
            if self._calculator is None:
                _LOGGER.info("Initializing solar production calculator")
                self._calculator = ExpectedProductionCalculator(
                    hass=self.hass,
                    config=config,
                )
            
            # Calculate expected production using solar model
            result = await self._calculator.async_calculate()
            
            return result
            
        except Exception as err:
            _LOGGER.error("Error updating SPVM expected production: %s", err)
            raise UpdateFailed(f"Error updating SPVM data: {err}") from err

    def _get_config(self) -> dict[str, Any]:
        """Get configuration from entry."""
        # Merge data and options
        data = {**self.entry.data, **self.entry.options}
        return data

    def reset_cache(self) -> None:
        """Reset calculator cache (compatibility method)."""
        if self._calculator:
            self._calculator.reset_cache()
            _LOGGER.info("SPVM cache reset (solar model has no cache)")
