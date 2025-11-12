"""Constants for the Smart PV Meter (SPVM) integration v0.6.0."""
from __future__ import annotations

from typing import Final

# ========== Integration info ==========
DOMAIN: Final = "spvm"
NAME: Final = "Smart PV Meter"
MANUFACTURER: Final = "GevaudanBeast"
ISSUE_URL: Final = "https://github.com/GevaudanBeast/smart-pv-meter/issues"
INTEGRATION_VERSION: Final = "0.6.0"

# ========== Configuration keys ==========
# Entity selectors
CONF_PV_SENSOR: Final = "pv_sensor"
CONF_HOUSE_SENSOR: Final = "house_sensor"
CONF_GRID_POWER_SENSOR: Final = "grid_power_sensor"
CONF_BATTERY_SENSOR: Final = "battery_sensor"
CONF_LUX_SENSOR: Final = "lux_sensor"
CONF_TEMP_SENSOR: Final = "temp_sensor"
CONF_HUM_SENSOR: Final = "hum_sensor"
CONF_CLOUD_SENSOR: Final = "cloud_sensor"  # NEW: Cloud coverage sensor

# System parameters
CONF_RESERVE_W: Final = "reserve_w"
CONF_UNIT_POWER: Final = "unit_power"
CONF_UNIT_TEMP: Final = "unit_temp"
CONF_CAP_MAX_W: Final = "cap_max_w"
CONF_DEGRADATION_PCT: Final = "degradation_pct"

# Solar model parameters (NEW)
CONF_PANEL_PEAK_POWER: Final = "panel_peak_power"
CONF_PANEL_TILT: Final = "panel_tilt"
CONF_PANEL_AZIMUTH: Final = "panel_azimuth"
CONF_SITE_LATITUDE: Final = "site_latitude"
CONF_SITE_LONGITUDE: Final = "site_longitude"
CONF_SITE_ALTITUDE: Final = "site_altitude"
CONF_SYSTEM_EFFICIENCY: Final = "system_efficiency"

# Update & smoothing
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_SMOOTHING_WINDOW: Final = "smoothing_window"

# Debug
CONF_DEBUG_EXPECTED: Final = "debug_expected"

# ========== Default values ==========
DEF_RESERVE_W: Final = 150
DEF_UNIT_POWER: Final = "W"
DEF_UNIT_TEMP: Final = "°C"
DEF_CAP_MAX_W: Final = 3000
DEF_DEGRADATION_PCT: Final = 0.0
DEF_CAP_LIMIT_W: Final = 3000  # Hard limit
HARD_CAP_W: Final = 3000  # Hard cap constant for sensor.py

# Solar model defaults (NEW)
DEF_PANEL_PEAK_POWER: Final = 3000  # 3 kWp
DEF_PANEL_TILT: Final = 30.0  # degrees
DEF_PANEL_AZIMUTH: Final = 180.0  # South
DEF_SITE_LATITUDE: Final = 43.5297  # Aix-en-Provence
DEF_SITE_LONGITUDE: Final = 5.4474  # Aix-en-Provence
DEF_SITE_ALTITUDE: Final = 200.0  # meters
DEF_SYSTEM_EFFICIENCY: Final = 0.85  # 85% (inverter + cables + dust)

DEF_UPDATE_INTERVAL: Final = 60  # seconds
DEF_SMOOTHING_WINDOW: Final = 45  # seconds
DEF_DEBUG_EXPECTED: Final = False

# Config entry version
CONF_ENTRY_VERSION: Final = 2  # BUMPED for v0.6.0 (breaking changes)
DEFAULT_ENTRY_TITLE: Final = "SPVM - Smart PV Meter"

# ========== Sensor entity IDs ==========
S_SPVM_GRID_POWER_AUTO: Final = "spvm_grid_power_auto"
S_SPVM_SURPLUS_VIRTUAL: Final = "spvm_surplus_virtual"
S_SPVM_SURPLUS_NET_RAW: Final = "spvm_surplus_net_raw"
S_SPVM_SURPLUS_NET: Final = "spvm_surplus_net"
S_SPVM_PV_EFFECTIVE_CAP_NOW_W: Final = "spvm_pv_effective_cap_now_w"
S_SPVM_EXPECTED_PRODUCTION: Final = "spvm_expected_production"  # RENAMED from expected_similar
S_SPVM_EXPECTED_DEBUG: Final = "spvm_expected_debug"

# ========== Sensor labels ==========
L_GRID_POWER_AUTO: Final = "SPVM - Grid Power Auto"
L_SURPLUS_VIRTUAL: Final = "SPVM - Surplus Virtual"
L_SURPLUS_NET_RAW: Final = "SPVM - Surplus Net Raw"
L_SURPLUS_NET: Final = "SPVM - Surplus Net"
L_PV_EFFECTIVE_CAP_NOW_W: Final = "SPVM - PV Effective Capacity"
L_EXPECTED_PRODUCTION: Final = "SPVM - Expected Production (Solar Model)"  # RENAMED
L_EXPECTED_DEBUG: Final = "SPVM - Expected Debug Info"

# ========== Units ==========
UNIT_W: Final = "W"
UNIT_KW: Final = "kW"
UNIT_C: Final = "°C"
UNIT_F: Final = "°F"
UNIT_DEG: Final = "°"  # NEW: degrees for angles
UNIT_M: Final = "m"  # NEW: meters for altitude
KW_TO_W: Final = 1000.0

# ========== Attributes ==========
ATTR_SOURCE: Final = "source"
ATTR_PV_W: Final = "pv_w"
ATTR_PV_KW: Final = "pv_kw"
ATTR_HOUSE_W: Final = "house_w"
ATTR_BATTERY_W: Final = "battery_w"
ATTR_GRID_W: Final = "grid_w"
ATTR_EXPECTED_W: Final = "expected_w"
ATTR_EXPECTED_KW: Final = "expected_kw"
ATTR_RESERVE_W: Final = "reserve_w"
ATTR_CAP_MAX_W: Final = "cap_max_w"
ATTR_CAP_LIMIT_W: Final = "cap_limit_w"
ATTR_DEGRADATION_PCT: Final = "degradation_pct"
ATTR_UNIT_POWER: Final = "unit_power"
ATTR_UNIT_TEMP: Final = "unit_temp"
ATTR_NOTE: Final = "note"
ATTR_SMOOTHED: Final = "smoothed"
ATTR_WINDOW_S: Final = "window_s"

# Solar model attributes (NEW)
ATTR_MODEL_TYPE: Final = "model_type"
ATTR_SOLAR_ELEVATION: Final = "solar_elevation"
ATTR_SOLAR_AZIMUTH: Final = "solar_azimuth"
ATTR_CLEAR_SKY_IRRADIANCE: Final = "clear_sky_irradiance"
ATTR_THEORETICAL_W: Final = "theoretical_w"
ATTR_CLOUD_FACTOR: Final = "cloud_factor"
ATTR_TEMP_FACTOR: Final = "temperature_factor"
ATTR_LUX_FACTOR: Final = "lux_factor"
ATTR_PANEL_TILT: Final = "panel_tilt"
ATTR_PANEL_AZIMUTH: Final = "panel_azimuth"
ATTR_SUNRISE: Final = "sunrise"
ATTR_SUNSET: Final = "sunset"
ATTR_LAST_UPDATE: Final = "last_update"

# ========== Source strings ==========
SOURCE_GRID_AUTO: Final = "computed(house-pv-batt)"
SOURCE_SURPLUS_VIRTUAL: Final = "max(export, pv-house)"
SOURCE_SURPLUS_NET: Final = "surplus_virtual - reserve_w (capped)"
SOURCE_SOLAR_MODEL: Final = "solar_physics_model"  # NEW

# ========== Notes ==========
NOTE_RESERVE: Final = "Zendure reserve applied"
NOTE_CAP: Final = "System cap applied"
NOTE_UNITS: Final = "Unit conversion applied (kW→W)"
NOTE_CAP_LIMIT: Final = "3 kW hard limit applied"
NOTE_HARD_CAP: Final = "3 kW hard limit applied"
NOTE_SOLAR_MODEL: Final = "Based on solar physics model"  # NEW
NOTE_WEATHER_ADJUSTED: Final = "Weather adjustments applied"  # NEW

# ========== History & timezone ==========
HISTORY_DAYS: Final = 30  # REDUCED: Only for fallback averaging now
TIMEZONE: Final = "Europe/Paris"

# ========== Solar model constants ==========
SOLAR_CONSTANT: Final = 1367  # W/m² at top of atmosphere
EARTH_TILT: Final = 23.44  # degrees
REFERENCE_TEMP: Final = 25.0  # °C for panel efficiency
TEMP_COEFFICIENT: Final = -0.004  # -0.4% per °C
