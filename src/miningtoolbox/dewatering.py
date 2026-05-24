"""
Mine dewatering and groundwater control.

Based on:
- SME Handbook — Mine Dewatering chapter
- McPherson — Subsurface Ventilation & Environmental Engineering
- Hartman & Mutmansky — Introductory Mining Engineering

Pump NPSH calculations use basic fluid mechanics.
NO IAPWS standard needed — water properties at typical mine temperatures
(5-35 C) can be approximated from standard tables or simplified formulas.
"""
import math

# ---------------------------------------------------------------------------
# Simple water properties (NOT IAPWS — simplified for mine engineering)
# ---------------------------------------------------------------------------

def water_density_approx(T_C: float) -> float:
    """
    Approximate water density for mine dewatering (5-50 C).
    
    Uses a simple linear approximation adequate for NPSH and pump sizing.
    For exact design, use standard water property tables (NOT IAPWS required).
    
    Args:
        T_C: Water temperature, C
    
    Returns:
        Density, kg/m3
    """
    # ρ ≈ 1000 - 0.4*(T - 25) for 5-50 C range
    rho = 1000.0 - 0.4 * (T_C - 25.0)
    return round(max(980.0, min(1010.0, rho)), 2)


def vapor_pressure_approx(T_C: float) -> float:
    """
    Approximate water vapor pressure for NPSH calculation.
    
    Tetens equation (simpler than IAPWS, adequate for mine dewatering).
    
    Args:
        T_C: Temperature, C
    
    Returns:
        Vapor pressure, kPa
    """
    # Tetens: e_sat = 0.6108 * exp(17.27*T / (T + 237.3))
    e = 0.61078 * math.exp(17.27 * T_C / (T_C + 237.3))
    return round(e, 3)


# ---------------------------------------------------------------------------
# Pump NPSH and hydraulic calculations
# ---------------------------------------------------------------------------

def npsh_available(
    atmospheric_pressure_kPa: float,
    water_level_below_pump_m: float,
    suction_losses_kPa: float,
    T_water_C: float
) -> dict:
    """
    Net Positive Suction Head Available (NPSHa) for mine dewatering pump.
    
    NPSHa = (P_atm/ρg + h_suction) - (P_vapor/ρg + h_losses)
    
    Args:
        atmospheric_pressure_kPa: Surface pressure
        water_level_below_pump_m: Static suction lift (positive = below pump)
        suction_losses_kPa: Friction + entrance losses
        T_water_C: Water temperature
    
    Returns:
        dict with NPSH_m, NPSH_kPa, status
    """
    rho = water_density_approx(T_water_C)
    P_vapor = vapor_pressure_approx(T_water_C)
    g = 9.81
    
    # Atmospheric head
    h_atm = atmospheric_pressure_kPa * 1000 / (rho * g)
    
    # Static suction head (negative if below pump)
    h_static = -water_level_below_pump_m
    
    # Vapor pressure head
    h_vapor = P_vapor * 1000 / (rho * g)
    
    # Loss head
    h_loss = suction_losses_kPa * 1000 / (rho * g)
    
    NPSH_m = h_atm + h_static - h_vapor - h_loss
    NPSH_kPa = NPSH_m * rho * g / 1000
    
    if NPSH_m > 3.0:
        status = "SAFE"
    elif NPSH_m > 1.5:
        status = "MARGINAL — monitor pump performance"
    else:
        status = "DANGER — cavitation likely"
    
    return {
        "NPSH_m": round(NPSH_m, 2),
        "NPSH_kPa": round(NPSH_kPa, 2),
        "water_density_kg_m3": rho,
        "vapor_pressure_kPa": P_vapor,
        "status": status
    }


def pump_power(Q_m3h: float, head_m: float, rho_kg_m3: float, efficiency: float = 0.70) -> float:
    """
    Shaft power for mine dewatering pump.
    
    P = ρ × g × Q × H / η
    
    Args:
        Q_m3h: Flow rate, m³/h
        head_m: Total dynamic head, m
        rho_kg_m3: Fluid density, kg/m³
        efficiency: Pump efficiency 0-1
    
    Returns:
        Power, kW
    """
    if efficiency <= 0:
        return float('inf')
    Q_m3s = Q_m3h / 3600.0
    P = rho_kg_m3 * 9.81 * Q_m3s * head_m / efficiency / 1000
    return round(P, 2)


# ---------------------------------------------------------------------------
# Inflow estimation (empirical)
# ---------------------------------------------------------------------------

def groundwater_inflow_empirical(
    permeability_m_d: float,
    aquifer_thickness_m: float,
    drawdown_m: float,
    influence_radius_m: float,
    pit_area_m2: float | None = None
) -> float:
    """
    Estimate mine groundwater inflow using Theim equation (simplified).
    
    Q = 2π * k * b * (h0 - hw) / ln(R/r0)
    
    Args:
        permeability_m_d: Hydraulic conductivity, m/day
        aquifer_thickness_m: Aquifer thickness, m
        drawdown_m: Water level drawdown, m
        influence_radius_m: Radius of influence, m
        pit_area_m2: Pit area (for r0 = sqrt(A/π)), optional
    
    Returns:
        Inflow rate, m³/day
    """
    if pit_area_m2:
        r0 = math.sqrt(pit_area_m2 / math.pi)
    else:
        r0 = 100.0  # default 100 m radius
    
    if r0 <= 0 or influence_radius_m <= r0:
        return 0.0
    
    Q = 2 * math.pi * permeability_m_d * aquifer_thickness_m * drawdown_m / math.log(influence_radius_m / r0)
    return round(Q, 1)


if __name__ == "__main__":
    # Demo: Deep mine sump pump
    print("Deep Mine Dewatering Analysis")
    print("=" * 50)
    
    T_water = 28
    print(f"Water at {T_water}C: density={water_density_approx(T_water)} kg/m3, vapor={vapor_pressure_approx(T_water)} kPa")
    
    # NPSH
    npsh = npsh_available(101.325, 5.0, 15.0, T_water)
    print(f"\nNPSH Analysis:")
    print(f"  NPSH available: {npsh['NPSH_m']:.1f} m ({npsh['status']})")
    
    # Pump sizing
    Q = 500  # m3/h
    H = 350  # m
    P = pump_power(Q, H, npsh['water_density_kg_m3'])
    print(f"\nPump Sizing:")
    print(f"  Flow: {Q} m3/h, Head: {H} m")
    print(f"  Shaft power: {P:.1f} kW ({P/0.746:.0f} HP)")
    
    # Groundwater inflow
    inflow = groundwater_inflow_empirical(2.5, 50, 80, 2000, 50000)
    print(f"\nGroundwater Inflow:")
    print(f"  Estimated: {inflow:.0f} m3/day")
    
    print("\nNOTE: Water properties use simplified empirical approximations.")
    print("NO IAPWS standard is needed for typical mine dewatering.")
