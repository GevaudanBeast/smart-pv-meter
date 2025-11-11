"""Data update coordinator for SPVM expected production."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
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
    HISTORY_DAYS,
    KW_TO_W,
    TIMEZONE,
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Get configuration
            config = self._get_config()
            
            # Initialize calculator if needed
            if self._calculator is None:
                self._calculator = ExpectedProductionCalculator(
                    hass=self.hass,
                    config=config,
                )
            
            # Calculate expected production
            result = await self._calculator.async_calculate()
            
            self._last_calculation_time = dt_util.now()
            
            return result
            
        except Exception as err:
            _LOGGER.error("Error updating SPVM expected production: %s", err)
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
            _LOGGER.info("SPVM cache reset")

    @property
    def last_calculation_time(self) -> datetime | None:
        """Return last calculation time."""
        return self._last_calculation_time
