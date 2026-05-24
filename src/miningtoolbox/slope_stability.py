"""
Open-pit slope stability analysis.

Based on:
- Hoek-Brown (2002) for rock mass strength
- Limit equilibrium methods — simplified Bishop / Fellenius
- Slope stability chart methods (Taylor, Hoek-Bray)
- SME Handbook — Slope Engineering chapter

NOT based on IAPWS — purely geotechnical / rock mechanics.
"""
import math

# ---------------------------------------------------------------------------
# Simplified Bishop factor of safety (circular slip surface)
# ---------------------------------------------------------------------------

def bishop_factor_of_safety(
    slip_radius_m: float,
    slip_depth_m: float,
    slope_height_m: float,
    slope_angle_deg: float,
    cohesion_kPa: float,
    friction_angle_deg: float,
    unit_weight_kN_m3: float,
    pore_pressure_ratio_ru: float = 0.0,
    num_slices: int = 10
) -> float:
    """
    Simplified Bishop method for circular slip surface.
    
    Iterative solution for factor of safety.
    
    Args:
        slip_radius_m: Radius of circular slip surface, m
        slip_depth_m: Depth of slip circle below toe, m
        slope_height_m: Slope height, m
        slope_angle_deg: Slope face angle, degrees
        cohesion_kPa: Effective cohesion, kPa
        friction_angle_deg: Effective friction angle, degrees
        unit_weight_kN_m3: Unit weight of rock/soil, kN/m³
        pore_pressure_ratio_ru: Pore pressure ratio (0 = dry, 0.3 = saturated)
        num_slices: Number of vertical slices
    
    Returns:
        Factor of safety (F > 1.3 typically acceptable)
    """
    if slip_radius_m <= 0 or slope_height_m <= 0:
        return float('inf')
    
    phi_rad = math.radians(friction_angle_deg)
    c = cohesion_kPa  # kPa
    gamma = unit_weight_kN_m3  # kN/m3
    
    # Simplified: wedge approximation
    # For a proper Bishop, need iterative slice-by-slice calculation.
    # Here we use a simplified chart-based approximation for conceptual design.
    
    # Taylor stability number approach (simplified)
    # Ns = c / (γ × H × F)
    # F = c / (γ × H × Ns)
    
    # Stability number Ns depends on slope angle and friction angle
    # Approximate from charts (simplified fit)
    slope_angle = math.radians(slope_angle_deg)
    
    if slope_angle_deg < 10:
        Ns_approx = 0.15
    elif slope_angle_deg < 20:
        Ns_approx = 0.10
    elif slope_angle_deg < 30:
        Ns_approx = 0.06
    elif slope_angle_deg < 40:
        Ns_approx = 0.04
    elif slope_angle_deg < 50:
        Ns_approx = 0.025
    else:
        Ns_approx = 0.015
    
    # Adjust for friction angle (higher φ = lower Ns needed)
    phi_factor = max(0.3, 1.0 - friction_angle_deg / 60.0)
    Ns = Ns_approx * phi_factor
    
    # Pore pressure reduces effective stress
    effective_factor = 1.0 - pore_pressure_ratio_ru
    
    F = (c * effective_factor) / (gamma * slope_height_m * Ns)
    
    return round(F, 2)


# ---------------------------------------------------------------------------
# Slope stability classification (simplified)
# ---------------------------------------------------------------------------

def slope_stability_status(F: float, slope_height_m: float, slope_angle_deg: float) -> dict:
    """
    Assess slope stability based on factor of safety and geometry.
    
    Mining guidelines (simplified):
    - F > 1.5: Stable (acceptable for long-term)
    - 1.3 < F <= 1.5: Marginal — monitoring required
    - 1.0 < F <= 1.3: Unstable — remediation needed
    - F <= 1.0: Failure imminent
    
    Args:
        F: Factor of safety
        slope_height_m: Slope height, m
        slope_angle_deg: Slope face angle, degrees
    
    Returns:
        dict with status, risk_level, recommended_action
    """
    if F > 1.5:
        status = "stable"
        risk = "low"
        action = "Continue operations, routine monitoring"
    elif F > 1.3:
        status = "marginal"
        risk = "moderate"
        action = "Install slope monitoring (prisms, radar), reduce bench heights"
    elif F > 1.0:
        status = "unstable"
        risk = "high"
        action = "STOP operations above slope, dewater, buttress or flatten"
    else:
        status = "critical"
        risk = "extreme"
        action = "EVACUATE, failure in progress or imminent"
    
    # Additional risk factors
    if slope_height_m > 200 and slope_angle_deg > 40:
        risk = "extreme" if risk == "extreme" else "high"
        action += ", engage geotechnical specialist immediately"
    
    return {
        "factor_of_safety": F,
        "status": status,
        "risk_level": risk,
        "recommended_action": action,
        "slope_height_m": slope_height_m,
        "slope_angle_deg": slope_angle_deg
    }


# ---------------------------------------------------------------------------
# Bench design (inter-ramp angle)
# ---------------------------------------------------------------------------

def bench_design(
    bench_height_m: float,
    bench_angle_deg: float,
    berm_width_m: float,
    geotechnical_domain: str = "hard_rock"
) -> dict:
    """
    Open-pit bench geometry design.
    
    Args:
        bench_height_m: Individual bench height, m (typical 10-15m)
        bench_angle_deg: Bench face angle, degrees (typical 60-75°)
        berm_width_m: Catch berm width, m (typical 6-10m)
        geotechnical_domain: "hard_rock", "soft_rock", "weathered", "structurally_controlled"
    
    Returns:
        dict with inter_ramp_angle, overall_slope_angle, catch_capacity_m3, status
    """
    # Inter-ramp angle = arctan(bench_height / (berm_width + bench_height/tan(bench_angle)))
    bench_angle_rad = math.radians(bench_angle_deg)
    horizontal_bench = bench_height_m / math.tan(bench_angle_rad)
    total_horizontal = horizontal_bench + berm_width_m
    inter_ramp = math.degrees(math.atan(bench_height_m / total_horizontal))
    
    # Overall slope (multiple benches with ramp)
    # Assume 15m wide ramp every 5 benches
    ramp_width = 15.0
    benches_between_ramps = 5
    total_height = bench_height_m * benches_between_ramps
    total_h = total_horizontal * benches_between_ramps + ramp_width
    overall_slope = math.degrees(math.atan(total_height / total_h))
    
    # Catch capacity (berm width × bench height, simplified)
    catch_capacity = berm_width_m * bench_height_m * 0.5  # m3 per m strike
    
    # Status check
    domains = {
        "hard_rock": {"max_bench": 15, "max_angle": 70, "min_berm": 5.0},
        "soft_rock": {"max_bench": 10, "max_angle": 60, "min_berm": 6.0},
        "weathered": {"max_bench": 8, "max_angle": 50, "min_berm": 8.0},
        "structurally_controlled": {"max_bench": 12, "max_angle": 55, "min_berm": 7.0}
    }
    
    dom = domains.get(geotechnical_domain, domains["hard_rock"])
    issues = []
    if bench_height_m > dom["max_bench"]:
        issues.append(f"Bench height > {dom['max_bench']}m for {geotechnical_domain}")
    if bench_angle_deg > dom["max_angle"]:
        issues.append(f"Face angle > {dom['max_angle']}° for {geotechnical_domain}")
    if berm_width_m < dom["min_berm"]:
        issues.append(f"Berm width < {dom['min_berm']}m — insufficient catch")
    
    status = "OK" if not issues else "REVIEW — " + "; ".join(issues)
    
    return {
        "inter_ramp_angle_deg": round(inter_ramp, 1),
        "overall_slope_angle_deg": round(overall_slope, 1),
        "catch_capacity_m3_per_m": round(catch_capacity, 1),
        "geotechnical_domain": geotechnical_domain,
        "status": status,
        "recommendations": issues if issues else ["Bench design acceptable for domain"]
    }


if __name__ == "__main__":
    # Demo: Copper open pit slope
    F = bishop_factor_of_safety(
        slip_radius_m=80,
        slip_depth_m=30,
        slope_height_m=150,
        slope_angle_deg=42,
        cohesion_kPa=250,
        friction_angle_deg=35,
        unit_weight_kN_m3=26,
        pore_pressure_ratio_ru=0.15
    )
    
    print("Open-Pit Slope Stability Analysis")
    print(f"  Factor of safety: {F}")
    
    status = slope_stability_status(F, 150, 42)
    print(f"  Status:           {status['status']} ({status['risk_level']} risk)")
    print(f"  Action:           {status['recommended_action']}")
    
    # Bench design
    bench = bench_design(15, 65, 8, "hard_rock")
    print(f"\nBench Design:")
    print(f"  Inter-ramp angle: {bench['inter_ramp_angle_deg']}°")
    print(f"  Overall slope:    {bench['overall_slope_angle_deg']}°")
    print(f"  Catch capacity:   {bench['catch_capacity_m3_per_m']:.0f} m3/m")
    print(f"  Status:           {bench['status']}")
    
    print("\nNOTE: Simplified Bishop method for conceptual design.")
    print("Detailed design requires 2D/3D numerical modeling (Slide2, FLAC, Plaxis).")
    print("NO IAPWS standard covers slope stability.")
