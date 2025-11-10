"""Tests pour les conversions d'unités."""
import pytest
from custom_components.spvm.helpers import convert_to_w, safe_float, clamp, rolling_average
from custom_components.spvm.const import UNIT_KW, UNIT_W, HARD_CAP_W

def test_convert_to_w():
    assert convert_to_w(1.5, UNIT_KW) == 1500.0
    assert convert_to_w(1500, UNIT_W) == 1500.0

def test_safe_float():
    assert safe_float("123.45") == 123.45
    assert safe_float(None) == 0.0
    assert safe_float("invalid", 10.0) == 10.0

def test_clamp():
    assert clamp(50, 0, 100) == 50
    assert clamp(-10, 0, 100) == 0
    assert clamp(150, 0, 100) == 100

def test_rolling_average():
    values = [10, 20, 30, 40, 50]
    assert rolling_average(values, 3) == 40.0

def test_reserve_application():
    surplus_virtual = 200
    reserve = 150
    surplus_net_raw = max(surplus_virtual - reserve, 0)
    assert surplus_net_raw == 50

def test_hard_cap():
    assert HARD_CAP_W == 3000
    net_raw = 3500
    net_capped = min(net_raw, HARD_CAP_W)
    assert net_capped == 3000
