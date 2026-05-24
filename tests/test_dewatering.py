"""Tests for dewatering module (NO IAPWS)."""
import pytest
from miningtoolbox import dewatering as dw

class TestDewatering:
    def test_water_density_around_1000(self):
        assert 990 < dw.water_density_approx(25) < 1010

    def test_vapor_pressure_at_25c(self):
        e = dw.vapor_pressure_approx(25)
        assert 3.0 < e < 3.2

    def test_npsh_safe(self):
        npsh = dw.npsh_available(101.325, 3.0, 10.0, 20)
        assert npsh['NPSH_m'] > 3.0
        assert npsh['status'] == 'SAFE'

    def test_npsh_danger(self):
        npsh = dw.npsh_available(80.0, 8.0, 30.0, 45)  # high altitude, hot, deep
        assert npsh['status'].startswith('DANGER') or npsh['status'].startswith('MARGINAL')

    def test_pump_power_positive(self):
        P = dw.pump_power(500, 300, 1000)
        assert P > 100

    def test_inflow_positive(self):
        Q = dw.groundwater_inflow_empirical(1.0, 30, 50, 1000, 20000)
        assert Q > 0
