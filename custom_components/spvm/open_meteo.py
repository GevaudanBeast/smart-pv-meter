"""Open-Meteo API client for real solar irradiance data.

This module fetches real GHI, DNI, DHI and GTI (tilted irradiance) data
from the Open-Meteo API, replacing the theoretical clear-sky model
with actual measured/forecasted irradiance values.

API Documentation: https://open-meteo.com/en/docs
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import asyncio

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Open-Meteo API endpoint
API_URL = "https://api.open-meteo.com/v1/forecast"

# Cache duration in seconds (avoid hammering the API)
CACHE_DURATION_S = 300  # 5 minutes


@dataclass
class SolarIrradiance:
    """Solar irradiance data from Open-Meteo."""

    timestamp: datetime
    ghi_wm2: float              # Global Horizontal Irradiance
    dni_wm2: Optional[float]    # Direct Normal Irradiance
    dhi_wm2: Optional[float]    # Diffuse Horizontal Irradiance
    gti_wm2: Optional[float]    # Global Tilted Irradiance (POA for array 1)
    gti2_wm2: Optional[float]   # Global Tilted Irradiance (POA for array 2)
    cloud_cover_pct: Optional[float]  # Cloud cover percentage
    temperature_c: Optional[float]    # Temperature at 2m


class OpenMeteoClient:
    """Async client for Open-Meteo solar radiation API."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        panel_tilt: float = 30.0,
        panel_azimuth: float = 180.0,
        array2_tilt: Optional[float] = None,
        array2_azimuth: Optional[float] = None,
    ):
        """Initialize the Open-Meteo client.

        Args:
            latitude: Site latitude in degrees
            longitude: Site longitude in degrees
            panel_tilt: Main array tilt angle (0-90 degrees)
            panel_azimuth: Main array azimuth (0=North, 90=East, 180=South, 270=West)
            array2_tilt: Second array tilt (optional)
            array2_azimuth: Second array azimuth (optional)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.panel_tilt = panel_tilt
        # Convert from SPVM convention (180=South) to Open-Meteo convention (0=South)
        self.panel_azimuth_om = panel_azimuth - 180.0

        self.array2_tilt = array2_tilt
        self.array2_azimuth_om = (array2_azimuth - 180.0) if array2_azimuth else None

        # Cache
        self._cache: Optional[dict] = None
        self._cache_time: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None

    def _convert_azimuth_to_open_meteo(self, azimuth_spvm: float) -> float:
        """Convert SPVM azimuth (180=South) to Open-Meteo convention (0=South).

        SPVM: 0=North, 90=East, 180=South, 270=West
        Open-Meteo: 0=South, -90=East, 90=West, ±180=North
        """
        # SPVM 180 (South) -> OM 0
        # SPVM 90 (East) -> OM -90
        # SPVM 270 (West) -> OM 90
        # SPVM 0 (North) -> OM 180
        om_az = azimuth_spvm - 180.0
        if om_az > 180:
            om_az -= 360
        elif om_az < -180:
            om_az += 360
        return om_az

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None or self._cache_time is None:
            return False
        age = (datetime.now(timezone.utc) - self._cache_time).total_seconds()
        return age < CACHE_DURATION_S

    async def fetch_current(self) -> Optional[SolarIrradiance]:
        """Fetch current solar irradiance data.

        Returns:
            SolarIrradiance object with current data, or None if fetch fails.
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                return self._parse_current_from_cache()

            session = await self._ensure_session()

            # Build hourly parameters
            hourly_params = [
                "shortwave_radiation",      # GHI
                "direct_normal_irradiance", # DNI
                "diffuse_radiation",        # DHI
                "cloud_cover",
                "temperature_2m",
            ]

            # Build URL
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "hourly": ",".join(hourly_params),
                "forecast_days": 1,
                "timezone": "UTC",
            }

            # Add GTI for main array
            tilt_params = {
                "tilt": self.panel_tilt,
                "azimuth": self._convert_azimuth_to_open_meteo(
                    self.panel_azimuth_om + 180.0  # Convert back for the function
                ),
            }

            # Request with GTI
            # Note: Open-Meteo uses tilt and azimuth query params for GTI
            url = f"{API_URL}?latitude={self.latitude}&longitude={self.longitude}"
            url += f"&hourly={','.join(hourly_params)},global_tilted_irradiance"
            url += f"&tilt={self.panel_tilt}&azimuth={self.panel_azimuth_om}"
            url += "&forecast_days=1&timezone=UTC"

            _LOGGER.debug(f"Open-Meteo request: {url}")

            async with session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(f"Open-Meteo API error: {response.status}")
                    return None

                data = await response.json()
                self._cache = data
                self._cache_time = datetime.now(timezone.utc)

                _LOGGER.debug(f"Open-Meteo response received, caching for {CACHE_DURATION_S}s")

                return self._parse_current_from_cache()

        except asyncio.TimeoutError:
            _LOGGER.warning("Open-Meteo API timeout")
            return None
        except aiohttp.ClientError as e:
            _LOGGER.warning(f"Open-Meteo API connection error: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"Open-Meteo API unexpected error: {e}", exc_info=True)
            return None

    def _parse_current_from_cache(self) -> Optional[SolarIrradiance]:
        """Parse current hour data from cached response."""
        if not self._cache:
            return None

        try:
            hourly = self._cache.get("hourly", {})
            times = hourly.get("time", [])

            if not times:
                return None

            # Find current hour index
            now = datetime.now(timezone.utc)
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            current_hour_str = current_hour.strftime("%Y-%m-%dT%H:%M")

            try:
                idx = times.index(current_hour_str)
            except ValueError:
                # If exact hour not found, use first available
                idx = 0
                _LOGGER.debug(f"Current hour {current_hour_str} not in response, using index 0")

            # Extract values
            ghi = hourly.get("shortwave_radiation", [None])[idx]
            dni = hourly.get("direct_normal_irradiance", [None])[idx]
            dhi = hourly.get("diffuse_radiation", [None])[idx]
            gti = hourly.get("global_tilted_irradiance", [None])[idx]
            cloud = hourly.get("cloud_cover", [None])[idx]
            temp = hourly.get("temperature_2m", [None])[idx]

            if ghi is None:
                _LOGGER.warning("Open-Meteo returned no GHI data")
                return None

            return SolarIrradiance(
                timestamp=current_hour,
                ghi_wm2=float(ghi),
                dni_wm2=float(dni) if dni is not None else None,
                dhi_wm2=float(dhi) if dhi is not None else None,
                gti_wm2=float(gti) if gti is not None else None,
                gti2_wm2=None,  # Would need second API call for different tilt
                cloud_cover_pct=float(cloud) if cloud is not None else None,
                temperature_c=float(temp) if temp is not None else None,
            )

        except Exception as e:
            _LOGGER.error(f"Error parsing Open-Meteo response: {e}", exc_info=True)
            return None

    async def fetch_forecast(self, hours: int = 24) -> list[SolarIrradiance]:
        """Fetch solar irradiance forecast.

        Args:
            hours: Number of hours to forecast (max 168 = 7 days)

        Returns:
            List of SolarIrradiance objects for each forecast hour.
        """
        # For future implementation - prévisions J+1 / J+7
        # This would enable predictive Solar Optimizer scheduling
        raise NotImplementedError("Forecast not yet implemented")


async def test_open_meteo():
    """Test function for Open-Meteo client."""
    client = OpenMeteoClient(
        latitude=43.45,   # La Destrousse area
        longitude=5.61,
        panel_tilt=30.0,
        panel_azimuth=180.0,
    )

    try:
        data = await client.fetch_current()
        if data:
            print(f"Open-Meteo Solar Data:")
            print(f"  GHI: {data.ghi_wm2:.1f} W/m²")
            print(f"  DNI: {data.dni_wm2:.1f} W/m²" if data.dni_wm2 else "  DNI: N/A")
            print(f"  DHI: {data.dhi_wm2:.1f} W/m²" if data.dhi_wm2 else "  DHI: N/A")
            print(f"  GTI (POA): {data.gti_wm2:.1f} W/m²" if data.gti_wm2 else "  GTI: N/A")
            print(f"  Cloud: {data.cloud_cover_pct:.0f}%" if data.cloud_cover_pct else "  Cloud: N/A")
            print(f"  Temp: {data.temperature_c:.1f}°C" if data.temperature_c else "  Temp: N/A")
        else:
            print("Failed to fetch data")
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_open_meteo())
