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
    EoT = 4 * math.degrees(q - math.degrees(RA))  # minutes

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


def compute(inputs: SolarInputs) -> SolarResult:
    el_deg, az_deg, dec_deg, _ha = _sun_position(inputs.dt_utc, inputs.lat_deg, inputs.lon_deg)
    inc_deg = _incidence_angle(el_deg, az_deg, inputs.panel_tilt_deg, inputs.panel_azimuth_deg)

    ghi_clear = _clear_sky_ghi(el_deg, inputs.altitude_m)
    # Plane-of-array projection: POA ~ GHI * cos(inc)
    cosi = max(0.0, math.cos(math.radians(inc_deg)))
    poa_clear = ghi_clear * (cosi / max(1e-6, math.sin(math.radians(el_deg)))) if el_deg > 0 else 0.0
    poa_clear = max(0.0, poa_clear)

    # Expected power (clear sky) before corrections
    expected_clear = poa_clear * inputs.system_efficiency * (inputs.panel_peak_w / 1000.0)  # W/m2 * eff * kWc
    # Cloud + Temperature corrections
    expected_corr = expected_clear * _cloud_factor(inputs.cloud_pct) * _temperature_factor(inputs.temp_c)

    return SolarResult(
        elevation_deg=el_deg,
        azimuth_deg=az_deg,
        declination_deg=dec_deg,
        incidence_deg=inc_deg,
        ghi_clear_wm2=ghi_clear,
        poa_clear_wm2=poa_clear,
        expected_clear_w=max(0.0, expected_clear),
        expected_corrected_w=max(0.0, expected_corr),
    )
