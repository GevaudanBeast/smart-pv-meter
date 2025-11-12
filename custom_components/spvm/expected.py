"""Expected production calculator using solar physics model (v0.6.0)."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const_v06 import (
    CONF_CLOUD_SENSOR,
    CONF_LUX_SENSOR,
    CONF_PANEL_AZIMUTH,
    CONF_PANEL_PEAK_POWER,
    CONF_PANEL_TILT,
    CONF_SITE_ALTITUDE,
    CONF_SITE_LATITUDE,
    CONF_SITE_LONGITUDE,
    CONF_SYSTEM_EFFICIENCY,
    CONF_TEMP_SENSOR,
    CONF_UNIT_TEMP,
    DEF_PANEL_AZIMUTH,
    DEF_PANEL_PEAK_POWER,
    DEF_PANEL_TILT,
    DEF_SITE_ALTITUDE,
    DEF_SITE_LATITUDE,
    DEF_SITE_LONGITUDE,
    DEF_SYSTEM_EFFICIENCY,
    DEF_UNIT_TEMP,
    KW_TO_W,
    TIMEZONE,
    UNIT_F,
)
from .helpers import fahrenheit_to_celsius, to_float
from .solar_model import SolarModel

_LOGGER = logging.getLogger(__name__)


class ExpectedProductionCalculator:
    """Calculate expected PV production using solar physics model."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize calculator."""
        self.hass = hass
        self.config = config
        
        # Extract solar model parameters
        latitude = config.get(CONF_SITE_LATITUDE, DEF_SITE_LATITUDE)
        longitude = config.get(CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE)
        
        # Initialize solar model
        self.solar_model = SolarModel(
            latitude=latitude,
            longitude=longitude,
            timezone=TIMEZONE,
        )
        
        _LOGGER.info(
            "Solar model initialized (lat=%.4f, lon=%.4f, tz=%s)",
            latitude,
            longitude,
            TIMEZONE,
        )

    async def async_calculate(self) -> dict[str, Any]:
        """Calculate expected production using solar model."""
        try:
            # Get current time
            now = dt_util.now()
            
            # Get weather conditions
            weather = self._get_weather_conditions()
            
            # Get panel configuration
            panel_config = self._get_panel_config()
            
            # Calculate using solar model
            result = await self.hass.async_add_executor_job(
                self._calculate_solar_production,
                now,
                panel_config,
                weather,
            )
            
            return result
            
        except Exception as err:
            _LOGGER.error("Error calculating expected production: %s", err)
            return self._get_empty_result()

    def _get_weather_conditions(self) -> dict[str, float | None]:
        """Get current weather conditions from sensors."""
        conditions = {
            "cloud_coverage": None,
            "temperature": None,
            "lux": None,
        }
        
        # Cloud coverage (0-100%)
        if self.config.get(CONF_CLOUD_SENSOR):
            cloud_state = self.hass.states.get(self.config[CONF_CLOUD_SENSOR])
            conditions["cloud_coverage"] = to_float(cloud_state, None)
        
        # Temperature (convert to °C if needed)
        if self.config.get(CONF_TEMP_SENSOR):
            temp_state = self.hass.states.get(self.config[CONF_TEMP_SENSOR])
            temp = to_float(temp_state, None)
            if temp is not None:
                unit_temp = self.config.get(CONF_UNIT_TEMP, DEF_UNIT_TEMP)
                if unit_temp == UNIT_F:
                    temp = fahrenheit_to_celsius(temp)
                conditions["temperature"] = temp
        
        # Lux (illuminance)
        if self.config.get(CONF_LUX_SENSOR):
            lux_state = self.hass.states.get(self.config[CONF_LUX_SENSOR])
            conditions["lux"] = to_float(lux_state, None)
        
        return conditions

    def _get_panel_config(self) -> dict[str, float]:
        """Get panel configuration from config."""
        return {
            "peak_power": self.config.get(CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER),
            "tilt": self.config.get(CONF_PANEL_TILT, DEF_PANEL_TILT),
            "azimuth": self.config.get(CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH),
            "altitude": self.config.get(CONF_SITE_ALTITUDE, DEF_SITE_ALTITUDE),
            "efficiency": self.config.get(
                CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY
            ),
        }

    def _calculate_solar_production(
        self,
        dt: datetime,
        panel_config: dict[str, float],
        weather: dict[str, float | None],
    ) -> dict[str, Any]:
        """Calculate production (runs in executor)."""
        # Get solar position
        solar_position = self.solar_model.calculate_solar_position(dt)
        
        # Check if sun is up
        if solar_position["elevation"] <= 0:
            return self._get_nighttime_result(solar_position)
        
        # Calculate production with weather adjustments
        production = self.solar_model.calculate_weather_adjusted_production(
            dt=dt,
            panel_peak_power=panel_config["peak_power"],
            panel_tilt=panel_config["tilt"],
            panel_azimuth=panel_config["azimuth"],
            altitude=panel_config["altitude"],
            system_efficiency=panel_config["efficiency"],
            cloud_coverage=weather["cloud_coverage"],
            temperature=weather["temperature"],
            lux=weather["lux"],
        )
        
        # Get sunrise/sunset
        sun_times = self.solar_model.get_sunrise_sunset(dt)
        
        # Build result
        return {
            "expected_w": production["adjusted_w"],
            "expected_kw": production["adjusted_w"] / KW_TO_W,
            "method": "solar_physics_model",
            "model_type": "clear_sky_with_weather_adjustments",
            # Solar position
            "solar_elevation": round(solar_position["elevation"], 2),
            "solar_azimuth": round(solar_position["azimuth"], 2),
            "solar_declination": round(solar_position["declination"], 2),
            # Production values
            "theoretical_w": production["theoretical_w"],
            "theoretical_kw": production["theoretical_w"] / KW_TO_W,
            # Adjustment factors
            "cloud_factor": round(production["adjustments"]["cloud_factor"], 3),
            "temperature_factor": round(
                production["adjustments"]["temperature_factor"], 3
            ),
            "lux_factor": round(production["adjustments"]["lux_factor"], 3),
            # Panel config
            "panel_tilt": panel_config["tilt"],
            "panel_azimuth": panel_config["azimuth"],
            "panel_peak_power": panel_config["peak_power"],
            # Sun times
            "sunrise": sun_times["sunrise"].isoformat(),
            "sunset": sun_times["sunset"].isoformat(),
            "solar_noon": sun_times["solar_noon"].isoformat(),
            # Weather sensors availability
            "cloud_sensor_available": weather["cloud_coverage"] is not None,
            "temp_sensor_available": weather["temperature"] is not None,
            "lux_sensor_available": weather["lux"] is not None,
        }

    def _get_nighttime_result(self, solar_position: dict) -> dict[str, Any]:
        """Get result for nighttime (sun below horizon)."""
        return {
            "expected_w": 0.0,
            "expected_kw": 0.0,
            "method": "solar_physics_model",
            "model_type": "nighttime",
            "solar_elevation": round(solar_position["elevation"], 2),
            "note": "Sun below horizon, no production expected",
        }

    def _get_empty_result(self) -> dict[str, Any]:
        """Get empty result on error."""
        return {
            "expected_w": 0.0,
            "expected_kw": 0.0,
            "method": "none",
            "error": "Calculation failed",
        }

    def reset_cache(self) -> None:
        """Reset cache (compatibility method, no cache in solar model)."""
        _LOGGER.debug("Solar model has no cache to reset")
