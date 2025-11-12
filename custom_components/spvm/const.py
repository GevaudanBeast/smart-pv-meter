"""Constantes Smart PV Meter (SPVM) v0.6.0 (autonome, sans expected externe)."""
from __future__ import annotations
from typing import Final

# Domaine / métadonnées
DOMAIN: Final = "spvm"
DEFAULT_ENTRY_TITLE: Final = "Smart PV Meter"

# Version interne du flow/entrée (incrémenter si schéma change)
CONF_ENTRY_VERSION: Final = 1

# ==== Clés d'entités (sensors) ====
CONF_PV_SENSOR: Final = "pv_sensor"                     # prod PV instantanée (kW ou W selon unité choisie)
CONF_HOUSE_SENSOR: Final = "house_sensor"               # conso maison instantanée (W)
CONF_GRID_POWER_SENSOR: Final = "grid_power_sensor"     # puissance réseau (+import/-export) optionnelle
CONF_BATTERY_SENSOR: Final = "battery_sensor"           # puissance batterie signée (+décharge/-charge) optionnelle
# (SUPPRIMÉ) CONF_EXPECTED_SENSOR
CONF_LUX_SENSOR: Final = "lux_sensor"                   # luminosité (optionnel)
CONF_TEMP_SENSOR: Final = "temp_sensor"                 # température (optionnel)
CONF_HUM_SENSOR: Final = "hum_sensor"                   # humidité (optionnel)
CONF_CLOUD_SENSOR: Final = "cloud_sensor"               # nébulosité (optionnel)

# ==== Paramètres système / unités ====
CONF_RESERVE_W: Final = "reserve_w"                     # réserve fixe pour batterie Zendure
CONF_UNIT_POWER: Final = "unit_power"                   # "W" ou "kW"
CONF_UNIT_TEMP: Final = "unit_temp"                     # "°C" ou "°F"
CONF_CAP_MAX_W: Final = "cap_max_w"                     # plafonnement système (ex. 3000 W)
CONF_DEGRADATION_PCT: Final = "degradation_pct"         # usure annuelle des panneaux (%)

# ==== Paramètres modèle solaire ====
CONF_PANEL_PEAK_POWER: Final = "panel_peak_power"       # Wc total
CONF_PANEL_TILT: Final = "panel_tilt"                   # inclinaison (°)
CONF_PANEL_AZIMUTH: Final = "panel_azimuth"             # 180 = plein sud (°)
CONF_SITE_LATITUDE: Final = "site_latitude"             # lat
CONF_SITE_LONGITUDE: Final = "site_longitude"           # lon
CONF_SITE_ALTITUDE: Final = "site_altitude"             # m
CONF_SYSTEM_EFFICIENCY: Final = "system_efficiency"     # rendement global (0.5–1.0)

# ==== Fréquence / lissage / debug ====
CONF_UPDATE_INTERVAL_SECONDS: Final = "update_interval_seconds"
CONF_SMOOTHING_WINDOW_SECONDS: Final = "smoothing_window_seconds"
CONF_DEBUG_EXPECTED: Final = "debug_expected"

# ==== Valeurs par défaut (adaptées à ton contexte) ====
# Rappel: réserve Zendure = 150 W et cap réseau = 3000 W.
DEF_RESERVE_W: Final = 150.0
DEF_UNIT_POWER: Final = "W"
DEF_UNIT_TEMP: Final = "°C"
DEF_CAP_MAX_W: Final = 3000.0
DEF_DEGRADATION_PCT: Final = 0.5  # %/an

# Modèle solaire (valeurs initiales génériques)
DEF_PANEL_PEAK_POWER: Final = 3000.0
DEF_PANEL_TILT: Final = 30.0
DEF_PANEL_AZIMUTH: Final = 180.0
DEF_SITE_LATITUDE: Final = 43.3
DEF_SITE_LONGITUDE: Final = 5.4
DEF_SITE_ALTITUDE: Final = 50.0
DEF_SYSTEM_EFFICIENCY: Final = 0.85

# Cadence & lissage
DEF_UPDATE_INTERVAL: Final = 30.0   # s
DEF_SMOOTHING_WINDOW: Final = 30.0  # s
DEF_DEBUG_EXPECTED: Final = False

# ==== Unités / conversions ====
UNIT_W: Final = "W"
UNIT_KW: Final = "kW"
UNIT_C: Final = "°C"
UNIT_F: Final = "°F"
KW_TO_W: Final = 1000.0

# ==== Noms/Libellés (ex. pour sensor expected) ====
S_SPVM_EXPECTED_PRODUCTION: Final = "spvm_expected_production"
L_EXPECTED_PRODUCTION: Final = "SPVM – Production attendue"

# ==== Attributs courants ====
ATTR_MODEL_TYPE: Final = "model_type"
ATTR_SOURCE: Final = "source"
ATTR_DEGRADATION_PCT: Final = "degradation_pct"
ATTR_SYSTEM_EFFICIENCY: Final = "system_efficiency"
ATTR_SITE: Final = "site"
ATTR_PANEL: Final = "panel"
ATTR_NOTE: Final = "note"

# Notes éventuelles
NOTE_SOLAR_MODEL: Final = "internal_solar_model"
