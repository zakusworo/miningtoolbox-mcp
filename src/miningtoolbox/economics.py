"""
Mine economics and financial analysis.

Based on:
- SME Handbook — Economics and Cost Estimating chapter
- Runge, I. (1998) — Mining Economics and Strategy
- Smith, L.D. (1997) — Strategies for Placing Cutoff Grades

Financial methods for mining project evaluation.
"""
import math

# -----------------------------------------------------------------------------
# Net Present Value (NPV) and Discounted Cash Flow
# -----------------------------------------------------------------------------

def npv(discount_rate: float, cash_flows: list, initial_investment: float = 0.0) -> float:
    """
    Calculate Net Present Value (NPV) for a mining project.

    NPV = sum(CF_t / (1 + r)^t) - Initial_Investment

    Args:
        discount_rate: Annual discount rate (e.g., 0.08 for 8%)
        cash_flows: List of annual cash flows (after-tax, positive = inflow)
        initial_investment: Upfront capital cost (positive value)

    Returns:
        NPV in same currency as cash flows
    """
    if discount_rate < 0:
        raise ValueError("Discount rate cannot be negative")

    present_value = sum(cf / ((1 + discount_rate) ** (i + 1))
                       for i, cf in enumerate(cash_flows))

    return round(present_value - initial_investment, 2)


def payback_period(initial_investment: float, annual_cash_flow: float,
                  discount_rate: float | None = None) -> float:
    """
    Calculate payback period — simple or discounted.

    Args:
        initial_investment: Upfront capital cost
        annual_cash_flow: Average annual cash inflow
        discount_rate: If provided, calculates discounted payback

    Returns:
        Payback period in years (float, e.g., 4.5 = 4.5 years)
    """
    if annual_cash_flow <= 0:
        return float('inf')

    if discount_rate is None or discount_rate == 0:
        # Simple payback
        return round(initial_investment / annual_cash_flow, 2)

    # Discounted payback — iterate until PV of cash flows = initial investment
    if discount_rate < 0:
        raise ValueError("Discount rate cannot be negative")

    cumulative_pv = 0.0
    year = 0
    while cumulative_pv < initial_investment and year < 100:
        year += 1
        pv_cf = annual_cash_flow / ((1 + discount_rate) ** year)
        cumulative_pv += pv_cf

    if cumulative_pv < initial_investment:
        return float('inf')  # Never pays back

    # Linear interpolation for partial year
    if year > 1:
        prev_cumulative = cumulative_pv - pv_cf
        fraction = (initial_investment - prev_cumulative) / pv_cf
    else:
        fraction = initial_investment / pv_cf

    return round((year - 1) + fraction, 2)


def equivalent_annual_cost(capex: float, opex_annual: float, discount_rate: float,
                          project_life_years: int) -> float:
    """
    Calculate Equivalent Annual Cost (EAC) — useful for equipment comparison.

    Converts upfront CAPEX to annual equivalent and adds OPEX.

    Args:
        capex: Capital expenditure (upfront)
        opex_annual: Annual operating cost
        discount_rate: Annual discount rate
        project_life_years: Project duration in years

    Returns:
        Equivalent annual cost
    """
    if discount_rate <= 0:
        raise ValueError("Discount rate must be positive")
    if project_life_years <= 0:
        raise ValueError("Project life must be positive")

    # Capital Recovery Factor: CRF = r(1+r)^n / ((1+r)^n - 1)
    r = discount_rate
    n = project_life_years
    crf = (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    annual_capex = capex * crf
    eac = annual_capex + opex_annual

    return round(eac, 2)


# -----------------------------------------------------------------------------
# Mining Cost and Revenue Calculations
# -----------------------------------------------------------------------------

def mining_cost_per_tonne(labor_cost: float, equipment_cost: float,
                         consumables_cost: float, tonnes: float) -> float:
    """
    Calculate total mining cost per tonne.

    Args:
        labor_cost: Total labor cost (currency)
        equipment_cost: Total equipment cost (fuel, maintenance, etc.)
        consumables_cost: Explosives, wear parts, etc.
        tonnes: Total tonnes moved

    Returns:
        Cost per tonne (currency/tonne)
    """
    if tonnes <= 0:
        raise ValueError("Tonnes must be positive")

    total_cost = labor_cost + equipment_cost + consumables_cost
    return round(total_cost / tonnes, 2)


def revenue_per_year(production_tonnes_per_year: float, grade_g_t: float,
                    recovery_percent: float, metal_price_per_oz: float) -> float:
    """
    Calculate annual revenue for precious metal mine.

    Args:
        production_tonnes_per_year: Annual ore production
        grade_g_t: Head grade in grams per tonne
        recovery_percent: Metallurgical recovery (0-100)
        metal_price_per_oz: Metal price per troy ounce (USD or other)

    Returns:
        Annual revenue (same currency as metal price)
    """
    if recovery_percent < 0 or recovery_percent > 100:
        raise ValueError("Recovery must be 0-100%")

    # Grams per tonne to ounces per tonne
    oz_per_tonne = grade_g_t / 31.1035  # 31.1035 g = 1 troy oz

    recovered_oz = production_tonnes_per_year * oz_per_tonne * (recovery_percent / 100)
    revenue = recovered_oz * metal_price_per_oz

    return round(revenue, 2)


def cutoff_grade(operating_cost_per_tonne: float, metal_price_per_oz: float,
                recovery_percent: float, selling_costs_per_oz: float = 0.0) -> float:
    """
    Calculate breakeven cutoff grade in g/t.

    Based on: Cutoff = (Operating_cost_per_tonne) / (Metal_price - Selling_costs) / Recovery

    Args:
        operating_cost_per_tonne: Total OPEX per tonne ore
        metal_price_per_oz: Metal price per troy ounce
        recovery_percent: Metallurgical recovery (0-100)
        selling_costs_per_oz: Refining, transport, royalties per oz

    Returns:
        Cutoff grade in g/t
    """
    if recovery_percent <= 0:
        raise ValueError("Recovery must be positive")
    if metal_price_per_oz <= selling_costs_per_oz:
        raise ValueError("Metal price must exceed selling costs")

    net_price = metal_price_per_oz - selling_costs_per_oz
    recovery = recovery_percent / 100

    # g/tonne = (cost/t) / ($/oz * recovery) * 31.1035 (g/oz)
    cutoff = (operating_cost_per_tonne / (net_price * recovery)) * 31.1035

    return round(cutoff, 3)


# -----------------------------------------------------------------------------
# Sensitivity Analysis
# -----------------------------------------------------------------------------

def sensitivity_npv(base_npv: float, parameter_changes: dict) -> dict:
    """
    Calculate NPV sensitivity to parameter changes.

    Args:
        base_npv: Base case NPV
        parameter_changes: Dict of {parameter_name: (base_value, new_value, npv_at_new_value)}

    Returns:
        Dict of sensitivity results with percent change
    """
    results = {}
    for param, (base, new, npv_new) in parameter_changes.items():
        pct_change = ((new - base) / base) * 100 if base != 0 else 0
        npv_change = npv_new - base_npv
        results[param] = {
            "base_value": base,
            "new_value": new,
            "percent_change": round(pct_change, 1),
            "npv_change": round(npv_change, 2),
            "sensitivity": round(npv_change / pct_change, 4) if pct_change != 0 else 0
        }
    return results


def tornado_ranking(sensitivities: dict) -> list:
    """
    Rank parameters by NPV impact (tornado chart order).

    Args:
        sensitivities: Output from sensitivity_npv()

    Returns:
        List of (parameter_name, absolute_npv_change) sorted by impact
    """
    ranked = [(param, abs(data["npv_change"]))
              for param, data in sensitivities.items()]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


# -----------------------------------------------------------------------------
# Risk and Uncertainty
# -----------------------------------------------------------------------------
# (Monte Carlo NPV simulation was removed: prior implementation was a stub
# that returned zeros. A proper implementation requires a project cash flow
# model. Until that exists, callers should use sensitivity_npv + tornado_ranking
# above for risk analysis.)


if __name__ == "__main__":
    # Demo: Gold mine pre-feasibility
    print("=" * 60)
    print("Mine Economics Analysis")
    print("=" * 60)

    # Project parameters
    capex = 50_000_000  # $50M initial
    annual_production = 2_800_000  # 2.8 Mt/year
    grade = 3.2  # g/t Au
    recovery = 92.5  # %
    gold_price = 1950  # $/oz
    opex_per_tonne = 85  # $/t
    mine_life = 8  # years

    print(f"\n[Project Parameters]")
    print(f"  CAPEX: ${capex/1e6:.1f}M")
    print(f"  Annual production: {annual_production/1e6:.1f} Mt")
    print(f"  Grade: {grade} g/t Au")
    print(f"  Recovery: {recovery}%")
    print(f"  Gold price: ${gold_price}/oz")
    print(f"  OPEX: ${opex_per_tonne}/t")

    # Annual revenue
    revenue = revenue_per_year(annual_production, grade, recovery, gold_price)
    annual_opex = opex_per_tonne * annual_production
    annual_cf = revenue - annual_opex

    print(f"\n[Annual Economics]")
    print(f"  Revenue: ${revenue/1e6:.1f}M/year")
    print(f"  OPEX: ${annual_opex/1e6:.1f}M/year")
    print(f"  Annual CF: ${annual_cf/1e6:.1f}M/year")

    # NPV
    cash_flows = [annual_cf] * mine_life
    npv_8 = npv(0.08, cash_flows, capex)
    print(f"\n[NPV Analysis @ 8% discount]")
    print(f"  NPV: ${npv_8/1e6:.1f}M")
    print(f"  Status: {'ECONOMIC' if npv_8 > 0 else 'MARGINAL' if npv_8 > -5e6 else 'UNECONOMIC'}")

    # Payback
    payback = payback_period(capex, annual_cf)
    print(f"\n[Payback Period]")
    print(f"  Simple payback: {payback:.1f} years")
    print(f"  Status: {'ACCEPTABLE' if payback < 5 else 'REVIEW' if payback < 8 else 'REJECT'}")

    # Cutoff grade
    cutoff = cutoff_grade(opex_per_tonne, gold_price, recovery, 50)
    print(f"\n[Cutoff Grade Analysis]")
    print(f"  Breakeven cutoff: {cutoff:.2f} g/t Au")
    print(f"  Current grade margin: {((grade/cutoff)-1)*100:.0f}% above cutoff")

    print("\n" + "=" * 60)
    print("Analysis complete.")
    print("=" * 60)
