"""Calcul interne de la production attendue (modèle solaire simple) v0.6.0."""
from __future__ import annotations
from datetime import datetime
from math import cos, sin, radians

from homeassistant.core import HomeAssistant

from .const import (
    CONF_PANEL_PEAK_POWER, CONF_PANEL_TILT, CONF_PANEL_AZIMUTH,
    CONF_SITE_LATITUDE, CONF_SITE_LONGITUDE, CONF_SYSTEM_EFFICIENCY,
    CONF_DEGRADATION_PCT,
    DEF_PANEL_PEAK_POWER, DEF_PANEL_TILT, DEF_PANEL_AZIMUTH,
    DEF_SITE_LATITUDE, DEF_SITE_LONGITUDE,
    DEF_SYSTEM_EFFICIENCY, DEF_DEGRADATION_PCT,
    KW_TO_W,
)

def _get(cfg: dict, key: str, default):
    return cfg.get(key, default)

def compute_expected_w(hass: HomeAssistant, cfg: dict, now: datetime) -> float:
    """Renvoie une estimation grossière en W (clear-sky, azimut/tilt/lat).
    Objectif: fournir une base stable et autonome (sans data externe).
    """
    peak_w = float(_get(cfg, CONF_PANEL_PEAK_POWER, DEF_PANEL_PEAK_POWER))
    tilt = float(_get(cfg, CONF_PANEL_TILT, DEF_PANEL_TILT))
    az = float(_get(cfg, CONF_PANEL_AZIMUTH, DEF_PANEL_AZIMUTH))
    lat = float(_get(cfg, CONF_SITE_LATITUDE, DEF_SITE_LATITUDE))
    lon = float(_get(cfg, CONF_SITE_LONGITUDE, DEF_SITE_LONGITUDE))
    eff = float(_get(cfg, CONF_SYSTEM_EFFICIENCY, DEF_SYSTEM_EFFICIENCY))
    degr = float(_get(cfg, CONF_DEGRADATION_PCT, DEF_DEGRADATION_PCT)) / 100.0

    # Très simplifié: élévation solaire approchée par l'heure locale (pas de lib externe).
    # Hypothèse: production ~ cos(angle_incidence) * peak * eff * (1 - degr)
    hour = now.hour + now.minute / 60.0
    # "arc" diurne basique: 8h-18h productif, peak vers 13h
    if hour < 8 or hour > 18:
        return 0.0

    # Profil horaire (cloche) d'amplitude 1
    # pic à 13h, décroissance vers 8h et 18h
    dist = abs(hour - 13.0)
    shape = max(0.0, 1.0 - (dist / 5.0))  # 13h =>1.0 ; 8h/18h =>0.0

    # Orientation: pénalité si azimut ≠ sud (180°); tilt modère la pente.
    az_penalty = max(0.0, cos(radians(abs(180.0 - az))) )  # 180° => 1.0 ; 90°/270° => 0
    tilt_factor = max(0.3, cos(radians(abs(30.0 - tilt))) )  # max vers ~30°, borne min 0.3

    # Latitude: légère atténuation générique (Marseille ~43° => ~0.85)
    lat_factor = max(0.6, cos(radians(abs(lat - 30.0))) )

    # Dégradation annuelle (statique, faute d'info d'année d'installation)
    health = 1.0 - degr

    expected = peak_w * eff * shape * az_penalty * tilt_factor * lat_factor * health
    return max(0.0, float(expected))
