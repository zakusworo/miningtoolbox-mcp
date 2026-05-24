"""Tests for blasting module."""
import pytest, math
from miningtoolbox import blasting as bl

class TestBlasting:
    def test_ppv_decreases_with_distance(self):
        ppv_near = bl.peak_particle_velocity(100, 50, site_factor_k=800)
        ppv_far = bl.peak_particle_velocity(500, 50, site_factor_k=800)
        assert ppv_far < ppv_near

    def test_ppv_increases_with_charge(self):
        ppv_small = bl.peak_particle_velocity(200, 25)
        ppv_large = bl.peak_particle_velocity(200, 100)
        assert ppv_large > ppv_small

    def test_assessment_safe(self):
        assess = bl.vibration_assessment(2.0, "residential")
        assert assess['status'] in ['acceptable', 'negligible']
        assert assess['exceedance_factor'] < 1.0

    def test_assessment_violation(self):
        assess = bl.vibration_assessment(15.0, "residential")
        assert 'violation' in assess['status'] or assess['status'] == 'caution'

    def test_overpressure_decreases_with_distance(self):
        op_near = bl.air_overpressure(200, 1000)
        op_far = bl.air_overpressure(800, 1000)
        assert op_far < op_near

    def test_blast_design_reasonable(self):
        design = bl.blast_design(bench_height_m=15, hole_diameter_mm=150)
        assert 3 < design['burden_m'] < 7
        assert design['spacing_m'] > design['burden_m']
        assert design['stemming_m'] > 0
        assert design['charge_kg'] > 0
        assert design['status'] == 'OK'

    def test_blast_design_custom(self):
        design = bl.blast_design(bench_height_m=12, burden_m=4.5, spacing_m=5.5,
                                  stemming_m=3.0, hole_diameter_mm=115)
        assert design['burden_m'] == 4.5
        assert design['spacing_m'] == 5.5
