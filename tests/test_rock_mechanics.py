"""Tests for rock mechanics module."""
import pytest, math
from miningtoolbox import rock_mechanics as rm

class TestRockMechanics:
    def test_rqd_basic(self):
        pieces = [15, 8, 22, 5, 30, 12, 18, 7, 25, 10]
        rqd = rm.rqd_from_core_recovery(pieces)
        assert 70 < rqd < 90

    def test_hoek_brown_granite(self):
        params = rm.hoek_brown_parameters(gsi=65, mi=25, D=0.5)
        assert params['mb'] > 0
        assert params['s'] > 0
        assert 0.49 < params['a'] < 0.51  # continuous Hoek-Brown 2002
        assert params['E_rm_MPa'] > 1000

    def test_hoek_brown_failure(self):
        params = rm.hoek_brown_parameters(60, 20, 0.0)
        sigma1 = rm.hoek_brown_strength(5.0, params['mb'], params['s'], params['a'], 100.0)
        assert sigma1 > 5.0

    def test_mohr_coulomb_conversion(self):
        params = rm.hoek_brown_parameters(75, 25, 0.0)  # good quality rock, undisturbed
        mc = rm.mohr_coulomb_from_hoek_brown(params['mb'], params['s'], params['a'], 150.0, 15.0)
        assert 20 < mc['friction_angle_deg'] < 60  # strong intact rock can reach ~55°
        assert mc['cohesion_MPa'] > 0

    def test_invalid_gsi_raises(self):
        with pytest.raises(ValueError):
            rm.hoek_brown_parameters(110, 20)

class TestRQD:
    def test_perfect_core(self):
        assert rm.rqd_from_core_recovery([20, 20, 20]) == 100.0

    def test_broken_core(self):
        assert rm.rqd_from_core_recovery([5, 3, 8, 2, 4]) < 50.0
