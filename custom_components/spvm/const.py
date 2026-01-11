"""Constantes Smart PV Meter (SPVM) v0.7.3 + compat rétro."""
from __future__ import annotations
from typing import Final

# Domaine / titre
DOMAIN: Final = "spvm"
DEFAULT_ENTRY_TITLE: Final = "Smart PV Meter"

# Version interne du flow
CONF_ENTRY_VERSION: Final = 1

# Entités d'entrée (sensors)
CONF_PV_SENSOR: Final = "pv_sensor"                     # PV instantané (W ou kW)
CONF_HOUSE_SENSOR: Final = "house_sensor"               # Conso maison (W)
CONF_GRID_POWER_SENSOR: Final = "grid_power_sensor"     # Réseau (+import / -export)
CONF_BATTERY_SENSOR: Final = "battery_sensor"           # Batterie signée (+décharge / -charge)
CONF_LUX_SENSOR: Final = "lux_sensor"                   # Lux (optionnel)
CONF_TEMP_SENSOR: Final = "temp_sensor"                 # Température (°C, optionnel)
CONF_HUM_SENSOR: Final = "hum_sensor"                   # Humidité (%RH, optionnel)
CONF_CLOUD_SENSOR: Final = "cloud_sensor"               # Couverture nuageuse 0–100 % (optionnel)

# Unités
UNIT_W: Final = "W"
UNIT_KW: Final = "kW"
KW_TO_W: Final = 1000.0
UNIT_C: Final = "°C"
UNIT_F: Final = "°F"
UNIT_PERCENT: Final = "%"

CONF_UNIT_POWER: Final = "unit_power"                   # "W" | "kW" (legacy global)
CONF_UNIT_TEMP: Final = "unit_temp"                     # "°C" | "°F"
DEF_UNIT_POWER: Final = UNIT_W
DEF_UNIT_TEMP: Final = UNIT_C

# Unités par capteur (v0.6.3+)
CONF_UNIT_PV: Final = "unit_pv"                         # "W" | "kW"
CONF_UNIT_HOUSE: Final = "unit_house"                   # "W" | "kW"
CONF_UNIT_GRID: Final = "unit_grid"                     # "W" | "kW"
CONF_UNIT_BATTERY: Final = "unit_battery"               # "W" | "kW"
DEF_UNIT_PV: Final = UNIT_W
DEF_UNIT_HOUSE: Final = UNIT_W
DEF_UNIT_GRID: Final = UNIT_W
DEF_UNIT_BATTERY: Final = UNIT_W

# Réserve / plafonds / vieillissement
CONF_RESERVE_W: Final = "reserve_w"
DEF_RESERVE_W: Final = 150                              # Réserve Zendure

CONF_CAP_MAX_W: Final = "cap_max_w"
DEF_CAP_MAX_W: Final = 3000                             # Cap dur 3 kW

CONF_DEGRADATION_PCT: Final = "degradation_pct"
DEF_DEGRADATION_PCT: Final = 0.0

# Paramètres modèle solaire (physique)
CONF_PANEL_PEAK_POWER: Final = "panel_peak_w"           # Wc
CONF_PANEL_TILT: Final = "panel_tilt_deg"               # 0 (horizontal) .. 90 (vertical)
CONF_PANEL_AZIMUTH: Final = "panel_azimuth_deg"         # 0=N, 90=E, 180=S, 270=O

DEF_PANEL_PEAK_POWER: Final = 2800.0
DEF_PANEL_TILT: Final = 30.0
DEF_PANEL_AZIMUTH: Final = 180.0

CONF_SITE_LATITUDE: Final = "site_lat"
CONF_SITE_LONGITUDE: Final = "site_lon"
CONF_SITE_ALTITUDE: Final = "site_alt"                  # m

DEF_SITE_LATITUDE: Final = None
DEF_SITE_LONGITUDE: Final = None
DEF_SITE_ALTITUDE: Final = None

CONF_SYSTEM_EFFICIENCY: Final = "system_efficiency"     # 0.5 .. 1.0
DEF_SYSTEM_EFFICIENCY: Final = 0.85

# Correction Lux (v0.6.8+)
CONF_LUX_MIN_ELEVATION: Final = "lux_min_elevation_deg"    # Élévation min pour activer correction lux
DEF_LUX_MIN_ELEVATION: Final = 5.0                          # 5° par défaut
CONF_LUX_FLOOR_FACTOR: Final = "lux_floor_factor"          # Plancher minimum correction (0.01-0.5)
DEF_LUX_FLOOR_FACTOR: Final = 0.1                           # 10% minimum par défaut
CONF_LUX_MAX_CHANGE_PCT: Final = "lux_max_change_pct"      # Variation max tolérée entre 2 lectures (%)
DEF_LUX_MAX_CHANGE_PCT: Final = 100.0                       # 100% = doublement/division par 2 max

# Ombrage obstacles (arbres, bâtiments)
CONF_SHADING_WINTER_PCT: Final = "shading_winter_pct"      # Ombrage supplémentaire hiver (%)
DEF_SHADING_WINTER_PCT: Final = 0.0                         # Pas d'ombrage par défaut
CONF_SHADING_MONTH_START: Final = "shading_month_start"    # Mois début ombrage (1-12)
DEF_SHADING_MONTH_START: Final = 11                         # Novembre par défaut
CONF_SHADING_MONTH_END: Final = "shading_month_end"        # Mois fin ombrage (1-12)
DEF_SHADING_MONTH_END: Final = 2                            # Février par défaut

# Intervalle / lissage / debug
CONF_UPDATE_INTERVAL_SECONDS: Final = "update_interval_seconds"
DEF_UPDATE_INTERVAL: Final = 30

CONF_SMOOTHING_WINDOW_SECONDS: Final = "smoothing_window_seconds"
DEF_SMOOTHING_WINDOW: Final = 60

CONF_DEBUG_EXPECTED: Final = "debug_expected"
DEF_DEBUG_EXPECTED: Final = False

# ---- Compat rétro (anciens noms encore importés ailleurs) ----
CONF_UPDATE_INTERVAL: Final = CONF_UPDATE_INTERVAL_SECONDS
CONF_SMOOTHING_WINDOW: Final = CONF_SMOOTHING_WINDOW_SECONDS

# Noms d’entités créées
S_SPVM_EXPECTED_PRODUCTION: Final = "spvm_expected_production"
L_EXPECTED_PRODUCTION: Final = "SPVM – Production attendue"

S_SPVM_YIELD_RATIO: Final = "spvm_yield_ratio"
L_YIELD_RATIO: Final = "SPVM – Rendement (%)"

S_SPVM_SURPLUS_NET: Final = "spvm_surplus_net"
L_SURPLUS_NET: Final = "SPVM – Surplus net"

# Attributs
ATTR_MODEL_TYPE: Final = "model_type"
ATTR_SOURCE: Final = "source"
ATTR_DEGRADATION_PCT: Final = "degradation_pct"
ATTR_SYSTEM_EFFICIENCY: Final = "system_efficiency"
ATTR_SITE: Final = "site"
ATTR_PANEL: Final = "panel"
ATTR_NOTE: Final = "note"

NOTE_SOLAR_MODEL: Final = "physical_solar_model"
