"""Data update coordinator for SPVM expected production."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
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
    CONF_TEMP_SENSOR,
    CONF_UNIT_POWER,
    CONF_UPDATE_INTERVAL,
    DEF_KNN_K,
    DEF_KNN_WEIGHT_ELEV,
    DEF_KNN_WEIGHT_HUM,
    DEF_KNN_WEIGHT_LUX,
    DEF_KNN_WEIGHT_TEMP,
    DEF_KNN_WINDOW_MAX,
    DEF_KNN_WINDOW_MIN,
    DEF_UNIT_POWER,
    DEF_UPDATE_INTERVAL,
    DOMAIN,
)
from .expected import ExpectedProductionCalculator

_LOGGER = logging.getLogger(__name__)


class SPVMCoordinator(DataUpdateCoordinator):
    """SPVM data coordinator for expected production calculation."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self._calculator: ExpectedProductionCalculator | None = None
        self._last_calculation_time: datetime | None = None
        
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
        
        _LOGGER.debug(
            "Coordinator initialized with update_interval=%s",
            update_interval
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        _LOGGER.info("-" * 40)
        _LOGGER.info("Coordinator update starting...")
        
        try:
            # Get configuration
            config = self._get_config()
            _LOGGER.debug(
                "Config sensors: pv=%s, lux=%s, temp=%s, hum=%s",
                config.get("pv_sensor"),
                config.get("lux_sensor"),
                config.get("temp_sensor"),
                config.get("hum_sensor"),
            )
            
            # Initialize calculator if needed
            if self._calculator is None:
                _LOGGER.info("Initializing ExpectedProductionCalculator...")
                self._calculator = ExpectedProductionCalculator(
                    hass=self.hass,
                    config=config,
                )
                _LOGGER.info("Calculator initialized")
            
            # Calculate expected production
            _LOGGER.info("Calculating expected production...")
            calc_start = time.time()
            
            result = await self._calculator.async_calculate()
            
            calc_elapsed = time.time() - calc_start
            _LOGGER.info(
                "Calculation completed in %.2fs: method=%s, expected=%.1fW, samples=%s",
                calc_elapsed,
                result.get("method", "unknown"),
                result.get("expected_w", 0),
                result.get("samples", "N/A"),
            )
            
            self._last_calculation_time = dt_util.now()
            _LOGGER.info("-" * 40)
            
            return result
            
        except Exception as err:
            _LOGGER.error(
                "Error updating SPVM expected production: %s",
                err,
                exc_info=True
            )
            _LOGGER.info("-" * 40)
            raise UpdateFailed(f"Error updating SPVM data: {err}") from err

    def _get_config(self) -> dict[str, Any]:
        """Get configuration from entry."""
        data = {**self.entry.data, **self.entry.options}
        
        return {
            "pv_sensor": data.get(CONF_PV_SENSOR),
            "lux_sensor": data.get(CONF_LUX_SENSOR),
            "temp_sensor": data.get(CONF_TEMP_SENSOR),
            "hum_sensor": data.get(CONF_HUM_SENSOR),
            "unit_power": data.get(CONF_UNIT_POWER, DEF_UNIT_POWER),
            "k": data.get(CONF_KNN_K, DEF_KNN_K),
            "window_min": data.get(CONF_KNN_WINDOW_MIN, DEF_KNN_WINDOW_MIN),
            "window_max": data.get(CONF_KNN_WINDOW_MAX, DEF_KNN_WINDOW_MAX),
            "weight_lux": data.get(CONF_KNN_WEIGHT_LUX, DEF_KNN_WEIGHT_LUX),
            "weight_temp": data.get(CONF_KNN_WEIGHT_TEMP, DEF_KNN_WEIGHT_TEMP),
            "weight_hum": data.get(CONF_KNN_WEIGHT_HUM, DEF_KNN_WEIGHT_HUM),
            "weight_elev": data.get(CONF_KNN_WEIGHT_ELEV, DEF_KNN_WEIGHT_ELEV),
        }

    def reset_cache(self) -> None:
        """Reset calculator cache."""
        if self._calculator:
            self._calculator.reset_cache()
            _LOGGER.info("SPVM calculator cache reset")
        else:
            _LOGGER.warning("Cannot reset cache: calculator not initialized")

    @property
    def last_calculation_time(self) -> datetime | None:
        """Return last calculation time."""
        return self._last_calculation_time
    
    @property
    def cache_size(self) -> int:
        """Return cache size safely (for diagnostics)."""
        try:
            if self._calculator and hasattr(self._calculator, "_cache"):
                return len(self._calculator._cache)
        except Exception as err:
            _LOGGER.debug("Could not get cache size: %s", err)
        return 0
    
    @property
    def calculator(self) -> ExpectedProductionCalculator | None:
        """Return calculator instance (for diagnostics)."""
        return self._calculator
