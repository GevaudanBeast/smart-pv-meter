"""Cablage du code de production, verifie par analyse syntaxique (lecon SRM)."""

from __future__ import annotations

import ast
import os

PKG = os.path.join(os.path.dirname(__file__), "..", "custom_components", "spvm")


def _src(name):
    with open(os.path.join(PKG, name), encoding="utf-8") as handle:
        return handle.read()


def _calls(source):
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def test_open_meteo_interpole():
    assert "interpolate_hourly_mean" in _calls(_src("open_meteo.py"))


def test_coordinator_utilise_secours_limite_et_lissage():
    calls = _calls(_src("coordinator.py"))
    assert "pv_with_fallback" in calls
    assert "surplus_net" in calls
    assert "RollingMean" in calls


def test_plus_de_bloc_info_a_chaque_cycle():
    tree = ast.parse(_src("coordinator.py"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "info"
            and "DIAGNOSTIC" in ast.unparse(node)
        ):
            raise AssertionError("bloc DIAGNOSTIC encore en INFO")


def test_options_rechargent_l_entree():
    assert "add_update_listener" in _calls(_src("__init__.py"))


def test_state_class_sur_les_capteurs():
    assert _src("sensor.py").count("SensorStateClass.MEASUREMENT") >= 3
