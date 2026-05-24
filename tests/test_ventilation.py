"""Tests for ventilation module."""
import pytest
from miningtoolbox import ventilation as vent

class TestVentilation:
    def test_saturation_vapor_pressure_at_25c(self):
        e = vent.saturation_vapor_pressure_ashrae(25)
        assert 3.0 < e < 3.2

    def test_psychrometric_complete(self):
        psych = vent.psychrometric_properties(30, 0.6)
        assert psych['humidity_ratio_kg_kg'] > 0.01
        assert psych['enthalpy_kJ_kg'] > 50
        assert psych['wet_bulb_C'] < 30
        assert psych['density_kg_m3'] > 1.0

    def test_friction_pressure_positive(self):
        dp = vent.friction_pressure_drop(20, 1000, 3.0, 1.15)
        assert dp > 0

    def test_fan_power_positive(self):
        P = vent.fan_power(20, 1500)
        assert P > 0

    def test_heat_stress_safe_zone(self):
        hsi = vent.heat_stress_index(25, 20)
        assert hsi['classification'] == 'safe'

    def test_heat_stress_danger_zone(self):
        hsi = vent.heat_stress_index(38, 35)
        assert hsi['classification'] in ['danger', 'emergency_stop']
