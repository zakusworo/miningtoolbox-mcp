"""
Mine ventilation engineering.

Based on:
- McPherson — Subsurface Ventilation Engineering (1993)
- Hartman & Mutmansky — Introductory Mining Engineering
- NIOSH Mine Ventilation publications
- ASHRAE Fundamentals (psychrometric basis, not IAPWS-specific)

NOT based on IAPWS — psychrometric calculations use empirical formulas
or ASHRAE equations for humid air, NOT the virial IAPWS G11-15 formulation.
"""
import math

# ---------------------------------------------------------------------------
# Psychrometric basics for mine ventilation
# ---------------------------------------------------------------------------

def saturation_vapor_pressure_ashrae(T_C: float) -> float:
    """
    Saturation vapor pressure using ASHRAE formulation.
    Simpler than IAPWS G11-15, widely used in HVAC/mining.
    
    Args:
        T_C: Temperature in Celsius
    
    Returns:
        Saturation vapor pressure in kPa
    """
    # ASHRAE simplified: Tetens-type equation
    # Valid 0 to 50 C
    if T_C < -10 or T_C > 60:
        return float('nan')
    
    # Tetens equation (kPa)
    e_sat = 0.61078 * math.exp(17.27 * T_C / (T_C + 237.3))
    return round(e_sat, 3)


def wet_bulb_temperature(T_dry: float, RH: float, P: float = 101.325) -> float:
    """
    Wet-bulb temperature from dry-bulb and relative humidity.
    Uses Stull (2011) empirical formula — accurate to ±0.5 C.
    
    Args:
        T_dry: Dry-bulb temperature, C
        RH: Relative humidity 0-1
        P: Total pressure, kPa (default 101.325)
    
    Returns:
        Wet-bulb temperature, C
    """
    # Stull formula for wet-bulb
    e = RH * saturation_vapor_pressure_ashrae(T_dry)
    
    # Iterative solution (simplified)
    # Start with guess
    Tw = T_dry * math.atan(0.151977 * ((RH * 100 + 8.313659) ** 0.5))
    Tw += math.atan(T_dry + RH * 100) - math.atan(RH * 100 - 1.676331)
    Tw += 0.00391838 * ((RH * 100) ** 1.5) * math.atan(0.023101 * RH * 100)
    Tw -= 4.686035
    
    return round(Tw, 1)


def psychrometric_properties(T_C: float, RH: float, P_kPa: float = 101.325) -> dict:
    """
    Complete psychrometric state for mine ventilation design.
    
    Args:
        T_C: Dry-bulb temperature, C
        RH: Relative humidity 0-1
        P_kPa: Total pressure, kPa
    
    Returns:
        dict with humidity_ratio, enthalpy, wet_bulb, density
    """
    e_sat = saturation_vapor_pressure_ashrae(T_C)
    e = RH * e_sat
    
    # Humidity ratio (kg water / kg dry air)
    W = 0.621945 * e / (P_kPa - e)
    
    # Enthalpy (kJ/kg dry air) — approximate
    h = 1.006 * T_C + W * (2501 + 1.86 * T_C)
    
    # Wet-bulb (empirical)
    Tw = wet_bulb_temperature(T_C, RH, P_kPa)
    
    # Density (kg/m3)
    R_da = 0.287058  # kJ/kg·K for dry air
    T_K = T_C + 273.15
    rho = P_kPa / (R_da * T_K * (1 + 1.6078 * W))
    
    return {
        "T_dry_C": T_C,
        "RH": round(RH, 3),
        "vapor_pressure_kPa": round(e, 3),
        "saturation_vapor_pressure_kPa": round(e_sat, 3),
        "humidity_ratio_kg_kg": round(W, 5),
        "enthalpy_kJ_kg": round(h, 2),
        "wet_bulb_C": Tw,
        "density_kg_m3": round(rho, 3)
    }


# ---------------------------------------------------------------------------
# Ventilation network fundamentals
# ---------------------------------------------------------------------------

def friction_pressure_drop(
    Q_m3s: float,
    L_m: float,
    D_m: float,
    rho_kg_m3: float,
    friction_factor: float = 0.02
) -> float:
    """
    Pressure drop in a mine airway (Darcy-Weisbach).
    
    ΔP = f * (L/D) * (ρ * v² / 2)
    
    Args:
        Q_m3s: Airflow rate, m³/s
        L_m: Duct length, m
        D_m: Hydraulic diameter, m
        rho_kg_m3: Air density, kg/m³
        friction_factor: Darcy friction factor (0.01-0.04 typical)
    
    Returns:
        Pressure drop, Pa
    """
    if D_m <= 0:
        return float('inf')
    
    v = Q_m3s / (math.pi * (D_m / 2) ** 2)  # velocity m/s
    delta_P = friction_factor * (L_m / D_m) * (rho_kg_m3 * v ** 2 / 2)
    return round(delta_P, 1)


def fan_power(Q_m3s: float, delta_P_Pa: float, efficiency: float = 0.65) -> float:
    """
    Fan shaft power for mine ventilation.
    
    P = Q × ΔP / η
    
    Args:
        Q_m3s: Airflow, m³/s
        delta_P_Pa: Total pressure rise, Pa
        efficiency: Fan efficiency 0-1
    
    Returns:
        Power, kW
    """
    if efficiency <= 0:
        return float('inf')
    P_kW = Q_m3s * delta_P_Pa / efficiency / 1000
    return round(P_kW, 2)


def heat_load_from_machinery(
    diesel_kW: float,
    electric_kW: float,
    load_factor: float = 0.75,
    efficiency_diesel: float = 0.35
) -> float:
    """
    Heat rejected into mine air from machinery.
    
    Diesel: ~1/3 shaft power, ~1/3 exhaust, ~1/3 coolant/radiation
    Electric: ~10% losses as heat
    
    Args:
        diesel_kW: Total diesel engine rated power
        electric_kW: Total electric motor rated power
        load_factor: Operating load factor 0-1
        efficiency_diesel: Diesel thermal efficiency
    
    Returns:
        Heat load to mine air, kW
    """
    # Diesel: all energy eventually becomes heat in the mine
    heat_diesel = diesel_kW * load_factor * (1.0 - efficiency_diesel) + diesel_kW * load_factor * efficiency_diesel * 0.5
    # Electric motor losses + machinery friction
    heat_electric = electric_kW * load_factor * 0.10
    
    return round(heat_diesel + heat_electric, 1)


# ---------------------------------------------------------------------------
# Heat stress index
# ---------------------------------------------------------------------------

def heat_stress_index(T_dry: float, Tw: float, WBGT: float | None = None) -> dict:
    """
    Mine heat stress assessment per NIOSH / ACGIH guidelines.
    
    Uses WBGT (Wet-Bulb Globe Temperature) or estimated from Tw.
    
    Args:
        T_dry: Dry-bulb temperature, C
        Tw: Wet-bulb temperature, C
        WBGT: Optional measured WBGT, C
    
    Returns:
        dict with classification, work/rest ratio, max_continuous_hours
    """
    if WBGT is None:
        # Approximate WBGT = 0.7*Tw + 0.3*T_dry (indoor/underground, no solar)
        wbgt = 0.7 * Tw + 0.3 * T_dry
    else:
        wbgt = WBGT
    
    # ACGIH TLV for acclimatized workers
    if wbgt <= 26.0:
        classification = "safe"
        work_rest = "continuous"
        max_hours = 8.0
    elif wbgt <= 28.0:
        classification = "caution"
        work_rest = "75:25"
        max_hours = 4.0
    elif wbgt <= 30.0:
        classification = "extreme_caution"
        work_rest = "50:50"
        max_hours = 2.0
    elif wbgt <= 32.0:
        classification = "danger"
        work_rest = "25:75"
        max_hours = 1.0
    else:
        classification = "emergency_stop"
        work_rest = "0:100"
        max_hours = 0.0
    
    return {
        "WBGT_C": round(wbgt, 1),
        "classification": classification,
        "work_rest_ratio": work_rest,
        "max_continuous_hours": max_hours,
        "action": "Continue work" if classification == "safe" else "Provide cooling/shade/hydration"
    }


if __name__ == "__main__":
    # Demo: Deep mine ventilation at 35 C, 90% RH
    T = 35.0
    RH = 0.90
    
    psych = psychrometric_properties(T, RH)
    print(f"Deep mine psychrometrics: T={T}C, RH={RH*100:.0f}%")
    print(f"  Wet-bulb:          {psych['wet_bulb_C']:.1f} C")
    print(f"  Humidity ratio:    {psych['humidity_ratio_kg_kg']:.4f} kg/kg")
    print(f"  Enthalpy:          {psych['enthalpy_kJ_kg']:.1f} kJ/kg")
    print(f"  Density:           {psych['density_kg_m3']:.3f} kg/m3")
    
    # Heat stress
    hsi = heat_stress_index(T, psych['wet_bulb_C'])
    print(f"\nHeat Stress:")
    print(f"  WBGT:              {hsi['WBGT_C']:.1f} C")
    print(f"  Classification:    {hsi['classification']}")
    print(f"  Work/rest:         {hsi['work_rest_ratio']}")
    
    # Ventilation sizing
    Q = 40  # m3/s for large drift
    L = 2000  # m
    D = 3.5  # m diameter
    rho = psych['density_kg_m3']
    dp = friction_pressure_drop(Q, L, D, rho)
    power = fan_power(Q, dp)
    
    print(f"\nVentilation:")
    print(f"  Airway:            {L}m × D={D}m")
    print(f"  Flow:              {Q} m3/s")
    print(f"  Pressure drop:     {dp:.0f} Pa")
    print(f"  Fan power:         {power:.1f} kW")
    
    print("\nNOTE: Psychrometrics use ASHRAE / empirical formulas.")
    print("NO IAPWS standard covers mine ventilation or heat stress.")
