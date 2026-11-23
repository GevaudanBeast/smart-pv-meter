"""Tests des calculs purs de SPVM v0.7.8.

Constats du 22/11/2026 : production attendue en marches horaires, pic en
retard d'environ 2 h ; derniere valeur PV reutilisee sans limite de duree ;
lissage configure mais jamais applique.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "spvm"))

from calc import (  # noqa: E402
    PV_FALLBACK_MAX_AGE_S,
    RollingMean,
    interpolate_hourly_mean,
    pv_with_fallback,
    surplus_net,
)

UTC = timezone.utc
TIMES = ["2026-11-22T11:00", "2026-11-22T12:00", "2026-11-22T13:00"]
VALUES = [100.0, 300.0, 500.0]


def _t(h, m=0):
    return datetime(2026, 11, 22, h, m, tzinfo=UTC)


def test_valeur_horaire_est_la_moyenne_de_l_heure_precedente():
    """La valeur etiquetee 12:00 decrit 11:00-12:00 : elle vaut a 11:30."""
    assert interpolate_hourly_mean(TIMES, VALUES, _t(11, 30)) == 300.0


def test_interpolation_entre_deux_milieux_d_heure():
    # 12:00 est a mi-chemin entre 11:30 (300) et 12:30 (500)
    assert interpolate_hourly_mean(TIMES, VALUES, _t(12, 0)) == 400.0


def test_plus_de_marche_a_l_heure_pile():
    avant = interpolate_hourly_mean(TIMES, VALUES, _t(11, 59))
    apres = interpolate_hourly_mean(TIMES, VALUES, _t(12, 1))
    assert abs(apres - avant) < 10.0


def test_l_ancien_code_prenait_l_heure_precedente():
    """Reproduit le bug : a 12:10 l'ancien code lisait l'etiquette 12:00."""
    ancien = VALUES[TIMES.index("2026-11-22T12:00")]
    nouveau = interpolate_hourly_mean(TIMES, VALUES, _t(12, 10))
    assert ancien == 300.0 and nouveau > 400.0


def test_bornes_et_valeurs_absentes():
    assert interpolate_hourly_mean(TIMES, VALUES, _t(9, 0)) == 100.0
    assert interpolate_hourly_mean(TIMES, VALUES, _t(15, 0)) == 500.0
    assert interpolate_hourly_mean([], [], _t(12)) is None
    assert interpolate_hourly_mean(TIMES, [100.0, None, 500.0], _t(12)) == 400.0


def test_pv_valeur_fraiche():
    assert pv_with_fallback(1200.0, None, None, _t(12)) == (1200.0, False)


def test_pv_secours_limite_dans_le_temps():
    now = _t(12)
    recent = now - timedelta(seconds=PV_FALLBACK_MAX_AGE_S - 10)
    ancien = now - timedelta(seconds=PV_FALLBACK_MAX_AGE_S + 10)
    assert pv_with_fallback(None, 900.0, recent, now) == (900.0, True)
    assert pv_with_fallback(None, 900.0, ancien, now) == (None, True)
    assert pv_with_fallback(None, None, None, now) == (None, True)


def test_moyenne_glissante():
    rm = RollingMean(60)
    rm.add(_t(12, 0), 0.0)
    rm.add(_t(12, 0) + timedelta(seconds=30), 400.0)
    assert rm.mean() == 200.0
    rm.add(_t(12, 2), 100.0)  # les valeurs de plus de 60 s sortent
    assert rm.mean() == 100.0


def test_moyenne_glissante_fenetre_nulle():
    rm = RollingMean(0)
    rm.add(_t(12), 10.0)
    rm.add(_t(12, 1), 30.0)
    assert rm.mean() == 30.0


def test_surplus_inchange_en_v078():
    assert surplus_net(2000.0, 1800.0, -500.0, 150.0) == 350.0
    assert surplus_net(2000.0, 1800.0, None, 150.0) == 50.0
    assert surplus_net(100.0, 900.0, 300.0, 150.0) == 0.0
