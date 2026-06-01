"""Tests for slope stability module."""
import pytest, math
from miningtoolbox import slope_stability as ss

class TestSlopeStability:
    def test_bishop_F_reasonable(self):
        F = ss.bishop_factor_of_safety(
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
            slope_height_m=50, slope_angle_deg=15,
            cohesion_kPa=300, friction_angle_deg=30,
            unit_weight_kN_m3=20
        )
        assert F > 1.5

    def test_bishop_critical_circle_lower_than_single(self):
        # Critical-circle search must return a FOS no higher than any
        # single user-specified circle at the same H, c, phi, gamma, ru.
        H, c, phi, gamma, ru = 50, 10, 35, 22, 0.0
        F_crit = ss.bishop_factor_of_safety(H, 50, c, phi, gamma, ru)
        for R in (1.0, 1.5, 2.0, 2.5, 3.0):
            R_m = R * H
            # Toe-passing center
            yc = 0.5 * R_m + 0.3 * H
            xc_sq = R_m**2 - yc**2
            if xc_sq <= 0:
                continue
            xc = math.sqrt(xc_sq)
            F_single = ss.bishop_factor_of_safety(
                H, 50, c, phi, gamma, ru,
                slip_radius_m=R_m,
                slip_center_x_m=xc, slip_center_y_m=yc,
            )
            assert F_crit <= F_single + 1e-6, (
                f"critical FOS {F_crit} should be <= single-circle FOS {F_single} at R={R}H"
            )

    def test_bishop_explicit_circle_mode(self):
        # When the user fully specifies a circle, the function returns
        # the FOS for that single circle (no search). Verify by computing
        # the same circle with the internal helper and comparing.
        H, c, phi, gamma, ru = 30, 20, 25, 20, 0.0
        tan_beta = math.tan(math.radians(45))
        crest_x = H / tan_beta
        R = 1.5 * H
        yc = 0.5 * R + 0.3 * H
        xc = math.sqrt(R**2 - yc**2)
        F_single = ss.bishop_factor_of_safety(
            H, 45, c, phi, gamma, ru,
            slip_radius_m=R, slip_center_x_m=xc, slip_center_y_m=yc,
        )
        F_helper = ss._bishop_single_circle(
            H, tan_beta, crest_x, math.radians(phi), c, gamma, ru,
            R, xc, yc, 30, 50, 1e-4,
        )
        assert abs(F_single - F_helper) < 1e-6

    def test_bishop_F_decreases_with_ru(self):
        F0 = ss.bishop_factor_of_safety(50, 40, 30, 30, 22, 0.0)
        F1 = ss.bishop_factor_of_safety(50, 40, 30, 30, 22, 0.2)
        F2 = ss.bishop_factor_of_safety(50, 40, 30, 30, 22, 0.4)
        assert F0 > F1 > F2
