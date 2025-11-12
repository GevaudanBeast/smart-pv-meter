"""Solar astronomical model for PV production prediction (SPVM v0.6.0)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta
import logging
from typing import Any

import pytz

_LOGGER = logging.getLogger(__name__)


class SolarModel:
    """Physical solar model for PV production estimation."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Paris",
    ) -> None:
        """Initialize solar model.
        
        Args:
            latitude: Site latitude in degrees (-90 to 90)
            longitude: Site longitude in degrees (-180 to 180)
            timezone: Timezone string (e.g., 'Europe/Paris')
        """
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = pytz.timezone(timezone)
        
        # Constants
        self.SOLAR_CONSTANT = 1367  # W/m² (solar irradiance at top of atmosphere)
        self.EARTH_TILT = 23.44  # Earth's axial tilt in degrees
        
    def calculate_solar_position(self, dt: datetime) -> dict[str, float]:
        """Calculate sun position (elevation, azimuth) for given datetime.
        
        Args:
            dt: Datetime to calculate position for
            
        Returns:
            Dictionary with 'elevation' and 'azimuth' in degrees
        """
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)
        
        # Calculate day of year
        day_of_year = dt.timetuple().tm_yday
        
        # Solar declination (angle between sun and equatorial plane)
        declination = self._calculate_declination(day_of_year)
        
        # Hour angle (angular distance sun travels across sky)
        hour_angle = self._calculate_hour_angle(dt)
        
        # Solar elevation (altitude above horizon)
        elevation = self._calculate_elevation(
            self.latitude, declination, hour_angle
        )
        
        # Solar azimuth (compass direction)
        azimuth = self._calculate_azimuth(
            self.latitude, declination, hour_angle, elevation
        )
        
        return {
            "elevation": elevation,
            "azimuth": azimuth,
            "declination": declination,
            "hour_angle": hour_angle,
        }
    
    def calculate_clear_sky_irradiance(
        self, 
        dt: datetime,
        altitude: float = 0.0,
    ) -> float:
        """Calculate theoretical clear-sky irradiance.
        
        Args:
            dt: Datetime to calculate for
            altitude: Site altitude in meters above sea level
            
        Returns:
            Clear-sky irradiance in W/m²
        """
        solar_pos = self.calculate_solar_position(dt)
        elevation = solar_pos["elevation"]
        
        # No irradiance below horizon
        if elevation <= 0:
            return 0.0
        
        # Air mass coefficient (atmospheric absorption)
        air_mass = self._calculate_air_mass(elevation, altitude)
        
        # Clear-sky irradiance with atmospheric attenuation
        # Using simplified Kasten-Czeplak model
        irradiance = self.SOLAR_CONSTANT * math.sin(math.radians(elevation))
        irradiance *= (0.75 ** (air_mass ** 0.678))
        
        return max(0.0, irradiance)
    
    def calculate_theoretical_production(
        self,
        dt: datetime,
        panel_peak_power: float,
        panel_tilt: float = 30.0,
        panel_azimuth: float = 180.0,
        altitude: float = 0.0,
        system_efficiency: float = 0.85,
    ) -> float:
        """Calculate theoretical PV production.
        
        Args:
            dt: Datetime to calculate for
            panel_peak_power: Peak power in W
            panel_tilt: Panel tilt angle (0=horizontal, 90=vertical)
            panel_azimuth: Panel orientation (0=North, 90=East, 180=South, 270=West)
            altitude: Site altitude in meters
            system_efficiency: System losses (inverter, cables, etc.)
            
        Returns:
            Expected production in W
        """
        # Get solar position
        solar_pos = self.calculate_solar_position(dt)
        solar_elevation = solar_pos["elevation"]
        solar_azimuth = solar_pos["azimuth"]
        
        # No production below horizon
        if solar_elevation <= 0:
            return 0.0
        
        # Calculate angle of incidence (angle between sun rays and panel)
        aoi = self._calculate_angle_of_incidence(
            solar_elevation,
            solar_azimuth,
            panel_tilt,
            panel_azimuth,
        )
        
        # Cosine effect (projection of irradiance on panel)
        cosine_factor = max(0.0, math.cos(math.radians(aoi)))
        
        # Get clear-sky irradiance
        irradiance = self.calculate_clear_sky_irradiance(dt, altitude)
        
        # Calculate production
        # Formula: P = irradiance * cosine_factor * efficiency * (panel_power / 1000)
        # Division by 1000 because irradiance is in W/m² and panel rating is at 1000 W/m²
        production = (
            irradiance 
            * cosine_factor 
            * system_efficiency 
            * (panel_peak_power / 1000.0)
        )
        
        return max(0.0, production)
    
    def calculate_weather_adjusted_production(
        self,
        dt: datetime,
        panel_peak_power: float,
        panel_tilt: float = 30.0,
        panel_azimuth: float = 180.0,
        altitude: float = 0.0,
        system_efficiency: float = 0.85,
        cloud_coverage: float | None = None,
        temperature: float | None = None,
        lux: float | None = None,
    ) -> dict[str, float]:
        """Calculate production with weather adjustments.
        
        Args:
            dt: Datetime to calculate for
            panel_peak_power: Peak power in W
            panel_tilt: Panel tilt angle
            panel_azimuth: Panel orientation
            altitude: Site altitude in meters
            system_efficiency: System efficiency
            cloud_coverage: Cloud coverage 0-100% (optional)
            temperature: Ambient temperature in °C (optional)
            lux: Measured illuminance in lux (optional)
            
        Returns:
            Dictionary with production values and adjustment factors
        """
        # Base theoretical production
        theoretical = self.calculate_theoretical_production(
            dt,
            panel_peak_power,
            panel_tilt,
            panel_azimuth,
            altitude,
            system_efficiency,
        )
        
        adjusted = theoretical
        adjustments = {
            "cloud_factor": 1.0,
            "temperature_factor": 1.0,
            "lux_factor": 1.0,
        }
        
        # Cloud coverage adjustment (if available)
        if cloud_coverage is not None:
            cloud_factor = self._calculate_cloud_factor(cloud_coverage)
            adjusted *= cloud_factor
            adjustments["cloud_factor"] = cloud_factor
        
        # Temperature adjustment (if available)
        # PV panels lose efficiency at high temperatures
        if temperature is not None:
            temp_factor = self._calculate_temperature_factor(temperature)
            adjusted *= temp_factor
            adjustments["temperature_factor"] = temp_factor
        
        # Lux-based adjustment (if available)
        # Use measured lux to refine estimate
        if lux is not None:
            lux_factor = self._calculate_lux_factor(lux, dt)
            adjusted *= lux_factor
            adjustments["lux_factor"] = lux_factor
        
        return {
            "theoretical_w": theoretical,
            "adjusted_w": max(0.0, adjusted),
            "adjustments": adjustments,
        }
    
    def get_sunrise_sunset(self, dt: datetime) -> dict[str, datetime]:
        """Calculate sunrise and sunset times.
        
        Args:
            dt: Date to calculate for
            
        Returns:
            Dictionary with 'sunrise' and 'sunset' datetime objects
        """
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)
        
        # Set to noon for calculation
        noon = dt.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Calculate declination for this day
        day_of_year = dt.timetuple().tm_yday
        declination = self._calculate_declination(day_of_year)
        
        # Hour angle at sunrise/sunset (when elevation = 0)
        # cos(hour_angle) = -tan(latitude) * tan(declination)
        lat_rad = math.radians(self.latitude)
        dec_rad = math.radians(declination)
        
        try:
            cos_hour_angle = -math.tan(lat_rad) * math.tan(dec_rad)
            
            # Clamp to valid range
            cos_hour_angle = max(-1.0, min(1.0, cos_hour_angle))
            
            hour_angle_deg = math.degrees(math.acos(cos_hour_angle))
            
            # Convert hour angle to time offset from solar noon
            time_offset_hours = hour_angle_deg / 15.0  # 15° per hour
            
            # Calculate solar noon (account for longitude)
            solar_noon_offset = self.longitude / 15.0  # hours from UTC
            solar_noon = noon.replace(hour=12) + timedelta(hours=-solar_noon_offset)
            
            # Calculate sunrise and sunset
            sunrise = solar_noon - timedelta(hours=time_offset_hours)
            sunset = solar_noon + timedelta(hours=time_offset_hours)
            
        except (ValueError, ZeroDivisionError):
            # Polar day or polar night
            # Default to no sunrise/sunset
            sunrise = noon.replace(hour=6)
            sunset = noon.replace(hour=18)
        
        return {
            "sunrise": sunrise,
            "sunset": sunset,
            "solar_noon": solar_noon if 'solar_noon' in locals() else noon,
        }
    
    # Private helper methods
    
    def _calculate_declination(self, day_of_year: int) -> float:
        """Calculate solar declination angle."""
        # Cooper's equation
        angle = 2 * math.pi * (day_of_year - 81) / 365
        declination = self.EARTH_TILT * math.sin(angle)
        return declination
    
    def _calculate_hour_angle(self, dt: datetime) -> float:
        """Calculate hour angle (0° at solar noon)."""
        # Minutes since midnight
        minutes = dt.hour * 60 + dt.minute
        
        # Solar noon is at 12:00 + longitude correction
        solar_noon_minutes = 720 + (self.longitude * 4)  # 4 min per degree
        
        # Hour angle: 15° per hour from solar noon
        hour_angle = (minutes - solar_noon_minutes) * 0.25
        
        return hour_angle
    
    def _calculate_elevation(
        self, 
        latitude: float, 
        declination: float, 
        hour_angle: float
    ) -> float:
        """Calculate solar elevation angle."""
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        ha_rad = math.radians(hour_angle)
        
        sin_elevation = (
            math.sin(lat_rad) * math.sin(dec_rad) +
            math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
        )
        
        elevation = math.degrees(math.asin(max(-1.0, min(1.0, sin_elevation))))
        return elevation
    
    def _calculate_azimuth(
        self,
        latitude: float,
        declination: float,
        hour_angle: float,
        elevation: float,
    ) -> float:
        """Calculate solar azimuth angle."""
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        ha_rad = math.radians(hour_angle)
        elev_rad = math.radians(elevation)
        
        try:
            cos_azimuth = (
                (math.sin(dec_rad) - math.sin(lat_rad) * math.sin(elev_rad)) /
                (math.cos(lat_rad) * math.cos(elev_rad))
            )
            
            cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
            azimuth = math.degrees(math.acos(cos_azimuth))
            
            # Adjust for afternoon (hour_angle > 0)
            if hour_angle > 0:
                azimuth = 360 - azimuth
                
        except (ValueError, ZeroDivisionError):
            azimuth = 0.0
        
        return azimuth
    
    def _calculate_air_mass(self, elevation: float, altitude: float) -> float:
        """Calculate air mass coefficient."""
        if elevation <= 0:
            return 100.0  # Large value for below horizon
        
        # Kasten-Young formula
        zenith = 90 - elevation
        zenith_rad = math.radians(zenith)
        
        # Air mass at sea level
        am = 1.0 / (
            math.cos(zenith_rad) + 
            0.50572 * ((96.07995 - zenith) ** -1.6364)
        )
        
        # Altitude correction
        pressure_ratio = math.exp(-altitude / 8400)  # 8400m scale height
        am *= pressure_ratio
        
        return max(1.0, am)
    
    def _calculate_angle_of_incidence(
        self,
        solar_elevation: float,
        solar_azimuth: float,
        panel_tilt: float,
        panel_azimuth: float,
    ) -> float:
        """Calculate angle between sun rays and panel normal."""
        # Convert to radians
        elev_rad = math.radians(solar_elevation)
        sun_az_rad = math.radians(solar_azimuth)
        tilt_rad = math.radians(panel_tilt)
        panel_az_rad = math.radians(panel_azimuth)
        
        # Angle of incidence formula
        cos_aoi = (
            math.sin(elev_rad) * math.cos(tilt_rad) +
            math.cos(elev_rad) * math.sin(tilt_rad) *
            math.cos(sun_az_rad - panel_az_rad)
        )
        
        cos_aoi = max(-1.0, min(1.0, cos_aoi))
        aoi = math.degrees(math.acos(cos_aoi))
        
        return aoi
    
    def _calculate_cloud_factor(self, cloud_coverage: float) -> float:
        """Calculate production reduction factor from cloud coverage.
        
        Args:
            cloud_coverage: Cloud coverage percentage (0-100)
            
        Returns:
            Reduction factor (0.0 to 1.0)
        """
        # Clamp to valid range
        coverage = max(0.0, min(100.0, cloud_coverage))
        
        # Non-linear relationship: some clouds = slight reduction, full clouds = major reduction
        # Using exponential decay model
        factor = math.exp(-coverage / 40.0)  # 40% = half production
        
        return max(0.1, factor)  # Minimum 10% even with full clouds
    
    def _calculate_temperature_factor(self, temperature: float) -> float:
        """Calculate efficiency reduction from temperature.
        
        Args:
            temperature: Ambient temperature in °C
            
        Returns:
            Efficiency factor (0.0 to 1.0)
        """
        # PV panels lose ~0.4% efficiency per °C above 25°C
        reference_temp = 25.0
        temp_coefficient = -0.004  # -0.4% per °C
        
        temp_diff = temperature - reference_temp
        factor = 1.0 + (temp_coefficient * temp_diff)
        
        # Clamp to reasonable range
        return max(0.5, min(1.1, factor))
    
    def _calculate_lux_factor(self, lux: float, dt: datetime) -> float:
        """Calculate adjustment factor from measured lux.
        
        Args:
            lux: Measured illuminance in lux
            dt: Current datetime
            
        Returns:
            Adjustment factor (0.0 to 1.5)
        """
        # Get theoretical clear-sky lux for comparison
        solar_pos = self.calculate_solar_position(dt)
        elevation = solar_pos["elevation"]
        
        if elevation <= 0:
            return 0.0
        
        # Approximate clear-sky lux from elevation
        # At zenith: ~120,000 lux
        max_lux = 120000.0
        theoretical_lux = max_lux * math.sin(math.radians(elevation))
        
        if theoretical_lux < 1000:
            return 1.0  # Too dark to compare accurately
        
        # Ratio of measured to theoretical
        lux_ratio = lux / theoretical_lux
        
        # Clamp to reasonable range
        return max(0.0, min(1.5, lux_ratio))
