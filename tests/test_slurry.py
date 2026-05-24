"""Tests for slurry module (NO IAPWS)."""
import pytest
from miningtoolbox import slurry

class TestSlurry:
    def test_slurry_density_increases_with_solids(self):
        rho_0 = slurry.slurry_density(1000, 2800, 0.0)
        rho_30 = slurry.slurry_density(1000, 2800, 0.30)
        rho_50 = slurry.slurry_density(1000, 2800, 0.50)
        assert rho_0 == 1000.0
        assert rho_30 > 1100
        assert rho_50 > rho_30
        assert rho_50 < 2800

    def test_bingham_viscosity_increases_with_concentration(self):
        b1 = slurry.slurry_viscosity_bingham(0.001, 0.20, 0.5, 2800)
        b2 = slurry.slurry_viscosity_bingham(0.001, 0.40, 0.5, 2800)
        assert b2['plastic_viscosity_Pas'] > b1['plastic_viscosity_Pas']

    def test_pipeline_pressure_positive(self):
        dp = slurry.slurry_pressure_drop_bingham(0.5, 0.3, 1000, 1200, 0.5, 0.005)
        assert dp > 0

    def test_settling_velocity_decreases_with_concentration(self):
        v1 = slurry.hindered_settling_velocity(0.5, 2800, 1000, 0.001, 0.10)
        v2 = slurry.hindered_settling_velocity(0.5, 2800, 1000, 0.001, 0.30)
        assert v2 < v1
