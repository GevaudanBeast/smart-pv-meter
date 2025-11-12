"""Constantes Smart PV Meter (SPVM) v0.6.0 (autonome)."""
from __future__ import annotations
from typing import Final

# ===== Domaine / métadonnées =====
DOMAIN: Final = "spvm"
DEFAULT_ENTRY_TITLE: Final = "Smart PV Meter"

# Version interne du flow (incrémenter si le schéma change)
CONF_ENTRY_VERSION: Final = 1

# ===== Clés d’entités d’entrée (sensors) =====
CONF_PV_SENSOR: Final = "pv_sensor"                     # Production PV instantanée (W ou kW suivant unité)
CONF_HOUSE_SENSOR: Final = "house_sensor"               # Consommation maison (W)
CONF_GRID_POWER_SENSOR: Final = "grid_power_sensor"     # Réseau (+import / -export), optionnel
CONF_BATTERY_SENSOR: Final = "battery_sensor"           # Batterie signée (+décharge / -charge), optionnel
CONF_LUX_SENSOR: Final = "lux_sensor"                   # Luminosité, optionnel
CONF_TEMP_SENSOR: Final = "temp_sensor"                 # Température, optionnel
CONF_HUM_SENSOR: Final = "hum_sensor"                   # Humidité, optionnel

# ===== Unités =====
UNIT_W: Final = "W"
UNIT_KW: Final = "kW"
KW_TO_W: Final = 1000.0
UNIT_C: Final = "°C"
UNIT_F: Final = "°F"

CONF_UNIT_POWER: Final = "unit_power"                   # "W" ou "kW"
CONF_UNIT_TEMP: Final = "unit_temp"                     # "°C" ou "°F"
DEF_UNIT_POWER: Final = UNIT_W
DEF_UNIT_TEMP: Final = UNIT_C

# ===== Réserve / plafonds / vieillissement =====
CONF_RESERVE_W: Final = "reserve_w"
DEF_RESERVE_W: Final = 150                              # Réserve Zendure (mémoire projet)

CONF_CAP_MAX_W: Final = "cap_max_w"
DEF_CAP_MAX_W: Final = 3000                             # Cap dur 3 kW (mémoire projet)

CONF_DEGRADATION_PCT: Final = "degradation_pct"         # Vieillissement panneaux en %
DEF_DEGRADATION_PCT: Final = 0.0

# ===== Modèle solaire interne (paramètres) =====
CONF_PANEL_PEAK_POWER: Final = "panel_peak_w"           # Puissance crête (W)
CONF_PANEL_TILT: Final = "panel_tilt_deg"               # Inclinaison (°)
CONF_PANEL_AZIMUTH: Final = "panel_azimuth_deg"         # Azimut (°; 180 = plein Sud)

DEF_PANEL_PEAK_POWER: Final = 2800.0
DEF_PANEL_TILT: Final = 30.0
DEF_PANEL_AZIMUTH: Final = 180.0

CONF_SITE_LATITUDE: Final = "site_lat"
CONF_SITE_LONGITUDE: Final = "site_lon"
CONF_SITE_ALTITUDE: Final = "site_alt"

# Valeurs par défaut neutres (laisser HA fournir lat/lon si non spécifié)
DEF_SITE_LATITUDE: Final = None
DEF_SITE_LONGITUDE: Final = None
DEF_SITE_ALTITUDE: Final = None

CONF_SYSTEM_EFFICIENCY: Final = "system_efficiency"     # Rendement global (0–1)
DEF_SYSTEM_EFFICIENCY: Final = 0.85

# ===== Intervalle de mise à jour / lissage / debug =====
# Nouveau nom (v0.6.0)
CONF_UPDATE_INTERVAL_SECONDS: Final = "update_interval_seconds"
DEF_UPDATE_INTERVAL: Final = 30                         # s

CONF_SMOOTHING_WINDOW_SECONDS: Final = "smoothing_window_seconds"
DEF_SMOOTHING_WINDOW: Final = 60                        # s

CONF_DEBUG_EXPECTED: Final = "debug_expected"
DEF_DEBUG_EXPECTED: Final = False

# ---- Compatibilité rétro (ne pas supprimer) ----
# Certains anciens modules importent encore ces noms :
CONF_UPDATE_INTERVAL: Final = CONF_UPDATE_INTERVAL_SECONDS
CONF_SMOOTHING_WINDOW: Final = CONF_SMOOTHING_WINDOW_SECONDS

# ===== Noms d’entités créées =====
S_SPVM_EXPECTED_PRODUCTION: Final = "spvm_expected_production"
L_EXPECTED_PRODUCTION: Final = "SPVM – Production attendue"

# ===== Attributs =====
ATTR_MODEL_TYPE: Final = "model_type"
ATTR_SOURCE: Final = "source"
ATTR_DEGRADATION_PCT: Final = "degradation_pct"
ATTR_SYSTEM_EFFICIENCY: Final = "system_efficiency"
ATTR_SITE: Final = "site"
ATTR_PANEL: Final = "panel"
ATTR_NOTE: Final = "note"

# Notes
NOTE_SOLAR_MODEL: Final = "internal_solar_model"
