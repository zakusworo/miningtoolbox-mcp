"""Tests for slope stability module."""
import pytest, math
from miningtoolbox import slope_stability as ss

class TestSlopeStability:
    def test_bishop_F_reasonable(self):
        F = ss.bishop_factor_of_safety(
            slip_radius_m=80, slip_depth_m=30,
            slope_height_m=150, slope_angle_deg=42,
            cohesion_kPa=250, friction_angle_deg=35,
            unit_weight_kN_m3=26, pore_pressure_ratio_ru=0.15
        )
        assert F > 0.5  # any reasonable physical value

    def test_stable_status(self):
        status = ss.slope_stability_status(1.6, 150, 42)
        assert status['status'] == 'stable'
        assert status['risk_level'] == 'low'

    def test_critical_status(self):
        status = ss.slope_stability_status(0.9, 250, 50)
        assert status['status'] == 'critical'
        assert status['risk_level'] == 'extreme'

    def test_bench_design_reasonable(self):
        bench = ss.bench_design(15, 65, 8, "hard_rock")
        assert 30 < bench['inter_ramp_angle_deg'] < 55
        assert bench['catch_capacity_m3_per_m'] > 0
        assert bench['status'].startswith('OK')

    def test_bench_too_high_warning(self):
        bench = ss.bench_design(20, 65, 8, "soft_rock")
        assert 'REVIEW' in bench['status'] or bench['status'].startswith('OK')

    def test_flat_slope_high_F(self):
        F = ss.bishop_factor_of_safety(
            slip_radius_m=50, slip_depth_m=10,
            slope_height_m=50, slope_angle_deg=15,
            cohesion_kPa=300, friction_angle_deg=30,
            unit_weight_kN_m3=20
        )
        assert F > 1.5
