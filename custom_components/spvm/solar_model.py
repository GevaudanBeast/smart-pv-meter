from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# =====================================================================
#  Solar geometry + clear-sky + panel incidence (no external deps)
#  - Sun position (elevation/azimuth) based on NOAA-like equations
#  - Air mass (Kasten & Young 1989)
#  - Clear-sky irradiance baseline (simple: extraterrestrial * transmittance)
#  - Cloud correction (Kasten-Czeplak-like: (1 - 0.75*C^3))
#  - Temperature derating (~ -0.5 % / °C above 25°C), optional
#  - Plane-of-array projection using incidence angle
# =====================================================================

SOLAR_CONSTANT = 1367.0  # W/m2 top-of-atmosphere


@dataclass
class SolarInputs:
    dt_utc: datetime
    lat_deg: float
    lon_deg: float
    altitude_m: float = 0.0

    panel_tilt_deg: float = 30.0         # 0=flat up, 90=vertical
    panel_azimuth_deg: float = 180.0     # 180=South

    panel_peak_w: float = 2800.0
    system_efficiency: float = 0.85      # 0..1

    cloud_pct: Optional[float] = None    # 0..100
    temp_c: Optional[float] = None       # °C
    lux: Optional[float] = None          # Luminosity (lux) for real-sky correction

    # Lux correction parameters (v0.6.9+)
    lux_min_elevation_deg: float = 5.0   # Minimum elevation to use lux correction
    lux_floor_factor: float = 0.1        # Floor factor to prevent complete zeroing

    # Seasonal shading (trees, buildings) (v0.6.9+)
    shading_winter_pct: float = 0.0      # Additional shading in winter (%)
    shading_month_start: int = 11        # Month when shading starts (1-12)
    shading_month_end: int = 2           # Month when shading ends (1-12)

    # Second array (optional) for multi-orientation installations (v0.7.4+)
    array2_peak_w: float = 0.0           # 0 = disabled
    array2_tilt_deg: float = 15.0        # Typical for pergola/flat roof
    array2_azimuth_deg: float = 180.0    # South by default

    # Open-Meteo real irradiance data (v0.7.5+) - replaces clear-sky model when available
    real_ghi_wm2: Optional[float] = None   # Real Global Horizontal Irradiance
    real_gti_wm2: Optional[float] = None   # Real Global Tilted Irradiance (array 1)
    real_gti2_wm2: Optional[float] = None  # Real Global Tilted Irradiance (array 2)


@dataclass
class SolarResult:
    elevation_deg: float
    azimuth_deg: float
    declination_deg: float
    incidence_deg: float
    ghi_clear_wm2: float
    poa_clear_wm2: float
    expected_clear_w: float
    expected_corrected_w: float
    lux_factor: Optional[float] = None  # Lux-based correction factor applied (0..1)
    # Multi-array support (v0.7.4+)
    array2_incidence_deg: Optional[float] = None
    array2_poa_clear_wm2: Optional[float] = None
    array2_expected_clear_w: Optional[float] = None
    array2_expected_corrected_w: Optional[float] = None
    # Open-Meteo real irradiance (v0.7.5+)
    using_real_irradiance: bool = False  # True if Open-Meteo data was used
    real_ghi_wm2: Optional[float] = None
    real_gti_wm2: Optional[float] = None


def _to_julian_day(dt: datetime) -> float:
    # Convert datetime UTC to Julian day
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + (dt.minute + dt.second / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + B - 1524.5
    return jd


def _sun_position(dt: datetime, lat_deg: float, lon_deg: float):
    # Returns (elevation_deg, azimuth_deg, declination_deg, hour_angle_deg)
    jd = _to_julian_day(dt)
    n = jd - 2451545.0  # days since J2000
    # Mean anomaly / L / ecliptic longitude
    g = math.radians((357.529 + 0.98560028 * n) % 360.0)
    q = (280.459 + 0.98564736 * n) % 360.0
    L = math.radians((q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360.0)
    # Obliquity
    e = math.radians(23.439 - 0.00000036 * n)
    # RA/Dec
    X = math.cos(L)
    Y = math.cos(e) * math.sin(L)
    Z = math.sin(e) * math.sin(L)
    RA = math.atan2(Y, X)  # radians
    dec = math.asin(Z)     # radians

    # Equation of time (approx)
    EoT = 4 * (q - math.degrees(RA))  # minutes

    # Solar time
    utc_hours = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    time_offset = EoT + 4 * lon_deg  # minutes
    tst = (utc_hours * 60.0 + time_offset) % 1440.0
    ha_deg = (tst / 4.0) - 180.0
    ha = math.radians(ha_deg)

    lat = math.radians(lat_deg)

    # Elevation
    sin_el = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(ha)
    sin_el = max(-1.0, min(1.0, sin_el))
    el = math.asin(sin_el)

    # Azimuth (0=N, 90=E)
    cos_az = (math.sin(dec) - math.sin(el) * math.sin(lat)) / (math.cos(el) * math.cos(lat) + 1e-9)
    cos_az = max(-1.0, min(1.0, cos_az))
    az = math.acos(cos_az)
    if math.sin(ha) > 0:
        az = 2 * math.pi - az

    return math.degrees(el), math.degrees(az), math.degrees(dec), ha_deg


def _air_mass(elevation_deg: float) -> float:
    # Kasten & Young 1989 air mass relative
    el = max(0.0, elevation_deg)
    if el <= 0.0:
        return float("inf")
    z = math.radians(90.0 - el)
    return 1.0 / (math.cos(z) + 0.50572 * (96.07995 - (90.0 - el)) ** -1.6364)


def _incidence_angle(elev_deg: float, az_deg: float, tilt_deg: float, panel_az_deg: float) -> float:
    # Angle entre la normale au panneau et le soleil
    # Vectorial method: cos(theta_i) = ...
    elev = math.radians(elev_deg)
    az = math.radians(az_deg)
    tilt = math.radians(tilt_deg)
    paz = math.radians(panel_az_deg)

    # Sun vector (horizontal coordinates)
    sx = math.cos(elev) * math.sin(az)   # East
    sy = math.cos(elev) * math.cos(az)   # North
    sz = math.sin(elev)                  # Up

    # Panel normal vector (tilt from horizontal, azimuth from North)
    nx = math.sin(tilt) * math.sin(paz)  # East
    ny = math.sin(tilt) * math.cos(paz)  # North
    nz = math.cos(tilt)                  # Up

    cos_t = max(0.0, min(1.0, sx * nx + sy * ny + sz * nz))
    return math.degrees(math.acos(cos_t))


def _clear_sky_ghi(elev_deg: float, altitude_m: float) -> float:
    # Very simple clear-sky: extraterrestrial * transmittance^airmass
    if elev_deg <= 0.0:
        return 0.0
    am = _air_mass(elev_deg)
    # Base atmospheric transmittance; slightly better at higher altitude
    tau = 0.75 + 2e-5 * altitude_m  # 0.75 @ ~sea level
    # Extraterrestrial normal irradiance with Earth orbit eccentricity (ignored here for simplicity)
    # G_on ~ 1367 W/m2
    ghi = SOLAR_CONSTANT * (tau ** am) * math.sin(math.radians(elev_deg))
    return max(0.0, ghi)


def _cloud_factor(cloud_pct: Optional[float]) -> float:
    if cloud_pct is None:
        return 1.0
    c = min(max(cloud_pct / 100.0, 0.0), 1.0)
    # Kasten-Czeplak-like attenuation on GHI
    return max(0.0, 1.0 - 0.75 * (c ** 3))


def _temperature_factor(temp_c: Optional[float]) -> float:
    if temp_c is None:
        return 1.0
    # Simple PV derating around 25°C: -0.5 % / °C above 25
    delta = float(temp_c) - 25.0
    if delta <= 0:
        return 1.0
    return max(0.5, 1.0 - 0.005 * delta)


def _lux_correction_factor(lux: Optional[float], elevation_deg: float,
                           min_elevation: float = 5.0, floor_factor: float = 0.1) -> Optional[float]:
    """
    Correction factor based on actual lux vs theoretical clear-sky lux.

    This provides a real-world correction when cloud_pct underestimates
    actual sky conditions (e.g., thick clouds vs thin clouds).

    Args:
        lux: Actual luminosity reading (lux)
        elevation_deg: Sun elevation angle (degrees)
        min_elevation: Minimum elevation to use correction (degrees)
        floor_factor: Minimum correction factor to prevent complete zeroing (0.01-0.5)

    Returns:
        float: Correction factor (floor_factor to 1.0), or None if lux not available
               or sun too low for reliable calculation.
    """
    if lux is None:
        return None

    # Skip correction when sun is too low (unreliable lux readings)
    if elevation_deg <= min_elevation:
        return None

    # Theoretical clear-sky lux approximation based on solar elevation
    # Full sun at zenith ≈ 100,000 lux, scales with sin(elevation)
    # At 22° elevation: ~37,000 lux theoretical max
    # Using conservative estimate: 80,000 * sin(elevation)
    theoretical_lux = 80000.0 * math.sin(math.radians(elevation_deg))

    if theoretical_lux < 100.0:
        return None

    # Calculate ratio of actual vs theoretical
    ratio = lux / theoretical_lux

    # Cap at 1.0 (can't produce more than clear-sky) and floor at user-defined minimum
    # The floor prevents complete zeroing which could cause instability
    factor = max(floor_factor, min(1.0, ratio))

    return factor


def _seasonal_shading_factor(dt: datetime, shading_pct: float,
                             month_start: int, month_end: int) -> float:
    """
    Seasonal shading correction for trees or buildings that cast shadows in winter.

    Args:
        dt: Current datetime
        shading_pct: Additional shading percentage (0-100%)
        month_start: Month when shading period starts (1-12, e.g., 11 for November)
        month_end: Month when shading period ends (1-12, e.g., 2 for February)

    Returns:
        float: Shading factor (0.0 to 1.0)
               1.0 = no shading, 0.5 = 50% shading, etc.

    Example:
        If shading_pct = 30% from November (11) to February (2):
        - In December: returns 0.7 (30% reduction)
        - In July: returns 1.0 (no reduction)
    """
    if shading_pct <= 0:
        return 1.0

    current_month = dt.month

    # Handle wrapping (e.g., November to February crosses year boundary)
    if month_start <= month_end:
        # No wrapping (e.g., May to September)
        in_shading_period = month_start <= current_month <= month_end
    else:
        # Wrapping (e.g., November to February)
        in_shading_period = current_month >= month_start or current_month <= month_end

    if in_shading_period:
        return max(0.0, 1.0 - (shading_pct / 100.0))
    else:
        return 1.0


def compute(inputs: SolarInputs) -> SolarResult:
    el_deg, az_deg, dec_deg, _ha = _sun_position(inputs.dt_utc, inputs.lat_deg, inputs.lon_deg)

    # --- Determine irradiance source: Open-Meteo real data or clear-sky model ---
    using_real_irradiance = inputs.real_ghi_wm2 is not None

    if using_real_irradiance:
        # Use real irradiance from Open-Meteo
        ghi = inputs.real_ghi_wm2
        # Use GTI if available, otherwise convert GHI to POA
        if inputs.real_gti_wm2 is not None:
            poa = inputs.real_gti_wm2
        else:
            # Approximate POA from GHI using incidence angle
            inc_deg = _incidence_angle(el_deg, az_deg, inputs.panel_tilt_deg, inputs.panel_azimuth_deg)
            cosi = max(0.0, math.cos(math.radians(inc_deg)))
            poa = ghi * (cosi / max(1e-6, math.sin(math.radians(el_deg)))) if el_deg > 0 else 0.0
    else:
        # Use clear-sky model (fallback)
        ghi = _clear_sky_ghi(el_deg, inputs.altitude_m)
        inc_deg = _incidence_angle(el_deg, az_deg, inputs.panel_tilt_deg, inputs.panel_azimuth_deg)
        cosi = max(0.0, math.cos(math.radians(inc_deg)))
        poa = ghi * (cosi / max(1e-6, math.sin(math.radians(el_deg)))) if el_deg > 0 else 0.0

    # --- Array 1 (primary) ---
    inc_deg = _incidence_angle(el_deg, az_deg, inputs.panel_tilt_deg, inputs.panel_azimuth_deg)
    poa_clear = max(0.0, poa)

    # Expected power before corrections
    expected_clear = poa_clear * inputs.system_efficiency * (inputs.panel_peak_w / 1000.0)

    # --- Array 2 (optional, for multi-orientation installations) ---
    array2_inc_deg: Optional[float] = None
    array2_poa_clear: Optional[float] = None
    array2_expected_clear: Optional[float] = None
    array2_expected_corr: Optional[float] = None

    if inputs.array2_peak_w > 0:
        array2_inc_deg = _incidence_angle(el_deg, az_deg, inputs.array2_tilt_deg, inputs.array2_azimuth_deg)

        if using_real_irradiance and inputs.real_gti2_wm2 is not None:
            # Use real GTI for array 2
            array2_poa_clear = inputs.real_gti2_wm2
        else:
            # Calculate from GHI
            cosi2 = max(0.0, math.cos(math.radians(array2_inc_deg)))
            array2_poa_clear = ghi * (cosi2 / max(1e-6, math.sin(math.radians(el_deg)))) if el_deg > 0 else 0.0

        array2_poa_clear = max(0.0, array2_poa_clear)
        array2_expected_clear = array2_poa_clear * inputs.system_efficiency * (inputs.array2_peak_w / 1000.0)

    # --- Corrections ---
    # When using real irradiance, cloud correction is already included in the data
    # Only apply temperature and shading corrections
    temp_factor = _temperature_factor(inputs.temp_c)

    shading_factor = _seasonal_shading_factor(
        inputs.dt_utc,
        inputs.shading_winter_pct,
        inputs.shading_month_start,
        inputs.shading_month_end
    )

    lux_factor: Optional[float] = None

    if using_real_irradiance:
        # Real irradiance already includes weather effects, only apply temp + shading
        expected_corr = expected_clear * temp_factor * shading_factor
    else:
        # Clear-sky model: apply cloud/lux correction
        cloud_temp_factor = _cloud_factor(inputs.cloud_pct) * temp_factor

        lux_factor = _lux_correction_factor(
            inputs.lux,
            el_deg,
            min_elevation=inputs.lux_min_elevation_deg,
            floor_factor=inputs.lux_floor_factor
        )

        if lux_factor is not None:
            expected_corr = expected_clear * lux_factor * temp_factor * shading_factor
        else:
            expected_corr = expected_clear * cloud_temp_factor * shading_factor

    # Apply corrections to Array 2
    if inputs.array2_peak_w > 0 and array2_expected_clear is not None:
        if using_real_irradiance:
            array2_expected_corr = array2_expected_clear * temp_factor * shading_factor
        elif lux_factor is not None:
            array2_expected_corr = array2_expected_clear * lux_factor * temp_factor * shading_factor
        else:
            array2_expected_corr = array2_expected_clear * _cloud_factor(inputs.cloud_pct) * temp_factor * shading_factor

        # Add Array 2 to totals
        expected_clear += array2_expected_clear
        expected_corr += array2_expected_corr
        poa_clear += array2_poa_clear  # Combined POA for reference

    return SolarResult(
        elevation_deg=el_deg,
        azimuth_deg=az_deg,
        declination_deg=dec_deg,
        incidence_deg=inc_deg,
        ghi_clear_wm2=ghi,
        poa_clear_wm2=poa_clear,
        expected_clear_w=max(0.0, expected_clear),
        expected_corrected_w=max(0.0, expected_corr),
        lux_factor=lux_factor,
        array2_incidence_deg=array2_inc_deg,
        array2_poa_clear_wm2=array2_poa_clear,
        array2_expected_clear_w=array2_expected_clear,
        array2_expected_corrected_w=array2_expected_corr,
        using_real_irradiance=using_real_irradiance,
        real_ghi_wm2=inputs.real_ghi_wm2,
        real_gti_wm2=inputs.real_gti_wm2,
    )
