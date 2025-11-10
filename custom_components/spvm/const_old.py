"""Constants for the Smart PV Meter (SPVM) integration."""
from __future__ import annotations

from typing import Final

# ========== Integration info ==========
DOMAIN: Final = "spvm"
NAME: Final = "Smart PV Meter"
MANUFACTURER: Final = "GevaudanBeast"
ISSUE_URL: Final = "https://github.com/GevaudanBeast/smart-pv-meter/issues"
INTEGRATION_VERSION: Final = "0.5.0"

# ========== Configuration keys ==========
# Entity selectors
CONF_PV_SENSOR: Final = "pv_sensor"
CONF_HOUSE_SENSOR: Final = "house_sensor"
CONF_GRID_POWER_SENSOR: Final = "grid_power_sensor"
CONF_BATTERY_SENSOR: Final = "battery_sensor"
CONF_LUX_SENSOR: Final = "lux_sensor"
CONF_TEMP_SENSOR: Final = "temp_sensor"
CONF_HUM_SENSOR: Final = "hum_sensor"

# System parameters
CONF_RESERVE_W: Final = "reserve_w"
CONF_UNIT_POWER: Final = "unit_power"
CONF_UNIT_TEMP: Final = "unit_temp"
CONF_CAP_MAX_W: Final = "cap_max_w"
CONF_DEGRADATION_PCT: Final = "degradation_pct"

# k-NN parameters
CONF_KNN_K: Final = "knn_k"
CONF_KNN_WINDOW_MIN: Final = "knn_window_min"
CONF_KNN_WINDOW_MAX: Final = "knn_window_max"
CONF_KNN_WEIGHT_LUX: Final = "knn_weight_lux"
CONF_KNN_WEIGHT_TEMP: Final = "knn_weight_temp"
CONF_KNN_WEIGHT_HUM: Final = "knn_weight_hum"
CONF_KNN_WEIGHT_ELEV: Final = "knn_weight_elev"

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

DEF_KNN_K: Final = 5
DEF_KNN_WINDOW_MIN: Final = 30
DEF_KNN_WINDOW_MAX: Final = 90
DEF_KNN_WEIGHT_LUX: Final = 0.4
DEF_KNN_WEIGHT_TEMP: Final = 0.2
DEF_KNN_WEIGHT_HUM: Final = 0.1
DEF_KNN_WEIGHT_ELEV: Final = 0.3

DEF_UPDATE_INTERVAL: Final = 60  # seconds
DEF_SMOOTHING_WINDOW: Final = 45  # seconds
DEF_DEBUG_EXPECTED: Final = False

# Config entry version
CONF_ENTRY_VERSION: Final = 1
DEFAULT_ENTRY_TITLE: Final = "SPVM - Smart PV Meter"

# ========== Sensor entity IDs ==========
S_SPVM_GRID_POWER_AUTO: Final = "spvm_grid_power_auto"
S_SPVM_SURPLUS_VIRTUAL: Final = "spvm_surplus_virtual"
S_SPVM_SURPLUS_NET_RAW: Final = "spvm_surplus_net_raw"
S_SPVM_SURPLUS_NET: Final = "spvm_surplus_net"
S_SPVM_PV_EFFECTIVE_CAP_NOW_W: Final = "spvm_pv_effective_cap_now_w"
S_SPVM_EXPECTED_SIMILAR: Final = "spvm_expected_similar"
S_SPVM_EXPECTED_DEBUG: Final = "spvm_expected_debug"

# ========== Sensor labels ==========
L_GRID_POWER_AUTO: Final = "SPVM - Grid Power Auto"
L_SURPLUS_VIRTUAL: Final = "SPVM - Surplus Virtual"
L_SURPLUS_NET_RAW: Final = "SPVM - Surplus Net Raw"
L_SURPLUS_NET: Final = "SPVM - Surplus Net"
L_PV_EFFECTIVE_CAP_NOW_W: Final = "SPVM - PV Effective Capacity"
L_EXPECTED_SIMILAR: Final = "SPVM - Expected Production (Similar Days)"
L_EXPECTED_DEBUG: Final = "SPVM - Expected Debug Info"

# ========== Units ==========
UNIT_W: Final = "W"
UNIT_KW: Final = "kW"
UNIT_C: Final = "°C"
UNIT_F: Final = "°F"
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

# k-NN specific attributes
ATTR_METHOD: Final = "method"
ATTR_NEIGHBORS: Final = "neighbors"
ATTR_WEIGHTS: Final = "weights"
ATTR_SAMPLES_TOTAL: Final = "samples_total"
ATTR_WINDOW_MIN: Final = "window_min"
ATTR_WINDOW_MAX: Final = "window_max"
ATTR_TIMEZONE: Final = "timezone"
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_ELEV_FILTER: Final = "elev_filter"
ATTR_K: Final = "k"
ATTR_DEBUG_VALUES: Final = "debug_values"

# ========== Source strings ==========
SOURCE_GRID_AUTO: Final = "computed(house-pv-batt)"
SOURCE_SURPLUS_VIRTUAL: Final = "max(export, pv-house)"
SOURCE_SURPLUS_NET: Final = "surplus_virtual - reserve_w (capped)"

# ========== Notes ==========
NOTE_RESERVE: Final = "Zendure reserve applied"
NOTE_CAP: Final = "System cap applied"
NOTE_UNITS: Final = "Unit conversion applied (kWâ†’W)"
NOTE_CAP_LIMIT: Final = "3 kW hard limit applied"
NOTE_HARD_CAP: Final = "3 kW hard limit applied"

# ========== History & timezone ==========
HISTORY_DAYS: Final = 1095  # 3 years for better seasonal comparison
TIMEZONE: Final = "Europe/Paris"
