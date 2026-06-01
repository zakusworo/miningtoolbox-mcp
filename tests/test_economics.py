"""Tests for economics module."""
import math
import pytest
from miningtoolbox import economics as ec


class TestNPV:
    def test_npv_5yr_uniform(self):
        # 5 × $1000 at 10%, no initial investment
        npv = ec.npv(0.10, [1000, 1000, 1000, 1000, 1000], 0.0)
        expected = sum(1000 / (1.1 ** i) for i in range(1, 6))
        assert abs(npv - expected) < 0.01

    def test_npv_with_initial_investment(self):
        npv = ec.npv(0.10, [1000] * 5, 3000.0)
        expected = sum(1000 / (1.1 ** i) for i in range(1, 6)) - 3000
        assert abs(npv - expected) < 0.01

    def test_npv_negative_discount_rejected(self):
        with pytest.raises(ValueError):
            ec.npv(-0.05, [100, 100], 0.0)


class TestPayback:
    def test_simple_payback(self):
        # $5000 invest, $1500/yr → 3.33 yr
        assert ec.payback_period(5000, 1500) == 3.33

    def test_discounted_payback_longer(self):
        simple = ec.payback_period(5000, 1500)
        discounted = ec.payback_period(5000, 1500, discount_rate=0.10)
        assert discounted > simple

    def test_discounted_payback_never(self):
        # Discounted payback: small annual CF vs large initial — never recovers
        assert ec.payback_period(1_000_000, 1000, discount_rate=0.10) == float('inf')


class TestCutoffGrade:
    def test_au_cutoff_typical(self):
        # OPEX 85, gold 1950, recovery 92.5%, refining 50
        cutoff = ec.cutoff_grade(85, 1950, 92.5, 50)
        expected = (85 / ((1950 - 50) * 0.925)) * 31.1035
        assert abs(cutoff - expected) < 0.001

    def test_cutoff_rejects_zero_recovery(self):
        with pytest.raises(ValueError):
            ec.cutoff_grade(85, 1950, 0)

    def test_cutoff_rejects_negative_margin(self):
        with pytest.raises(ValueError):
            ec.cutoff_grade(85, 100, 92.5, 200)


class TestRevenue:
    def test_au_annual_revenue(self):
        # 2.8 Mt, 3.2 g/t, 92.5% recovery, $1950/oz
        rev = ec.revenue_per_year(2_800_000, 3.2, 92.5, 1950)
        expected = 2_800_000 * (3.2 / 31.1035) * 0.925 * 1950
        assert abs(rev - expected) < 0.5

    def test_recovery_bounds(self):
        with pytest.raises(ValueError):
            ec.revenue_per_year(1_000_000, 2.0, 150, 1500)
        with pytest.raises(ValueError):
            ec.revenue_per_year(1_000_000, 2.0, -5, 1500)


class TestMiningCost:
    def test_cost_per_tonne(self):
        # $100k labor + $200k equip + $50k consumables / 100kt = $3.5/t
        cost = ec.mining_cost_per_tonne(100_000, 200_000, 50_000, 100_000)
        assert cost == 3.5

    def test_zero_tonnes_rejected(self):
        with pytest.raises(ValueError):
            ec.mining_cost_per_tonne(100, 200, 300, 0)


class TestSensitivity:
    def test_sensitivity_npv_change(self):
        results = ec.sensitivity_npv(
            base_npv=1000.0,
            parameter_changes={
                "gold_price": (1900, 2000, 1100.0),
                "recovery": (0.90, 0.92, 1050.0),
            },
        )
        assert "gold_price" in results
        assert results["gold_price"]["npv_change"] == 100.0
        assert results["gold_price"]["percent_change"] == pytest.approx(5.26, rel=0.01)

    def test_tornado_ranking(self):
        sensitivities = ec.sensitivity_npv(
            base_npv=1000.0,
            parameter_changes={
                "a": (100, 110, 1200.0),    # npv change = 200
                "b": (50, 55, 1100.0),      # npv change = 100
                "c": (200, 220, 1500.0),    # npv change = 500
            },
        )
        ranked = ec.tornado_ranking(sensitivities)
        assert ranked[0][0] == "c"
        assert ranked[-1][0] == "b"


class TestMonteCarloRemoved:
    """The stub monte_carlo_npv_simulation was removed. Verify it is gone."""

    def test_monte_carlo_not_exposed(self):
        assert not hasattr(ec, "monte_carlo_npv_simulation"), (
            "monte_carlo_npv_simulation should be deleted (was a stub returning zeros)"
        )
