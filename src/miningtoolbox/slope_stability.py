"""
Open-pit slope stability analysis.

Based on:
- Hoek-Brown (2002) for rock mass strength
- Limit equilibrium methods — simplified Bishop / Fellenius
- Slope stability chart methods (Taylor, Hoek-Bray)
- SME Handbook — Slope Engineering chapter

Geotechnical and rock mechanics methods.
"""
import math

# ---------------------------------------------------------------------------
# Simplified Bishop factor of safety (circular slip surface)
# ---------------------------------------------------------------------------

def _bishop_single_circle(
    H: float,
    tan_beta: float,
    crest_x: float,
    phi: float,
    c: float,
    gamma: float,
    ru: float,
    R: float,
    xc: float,
    yc: float,
    num_slices: int,
    max_iter: int,
    tol: float,
) -> float:
    """Bishop FOS for one specified slip circle. Returns inf if no valid slices."""
    # Adjust R so circle passes through the toe (0,0)
    toe_dist = math.sqrt(xc**2 + yc**2)
    if toe_dist <= 0:
        return float('inf')
    if abs(toe_dist - R) / toe_dist > 0.01:
        R = toe_dist

    # Exit through the slope face or the crest
    crest_disc = R**2 - (H - yc)**2
    if crest_disc >= 0:
        x_exit_crest = xc + math.sqrt(crest_disc)
    else:
        x_exit_crest = float('inf')

    A = 1 + tan_beta**2
    B = -2 * (xc + yc * tan_beta)
    # Quadratic: A x^2 + B x + (xc^2+yc^2-R^2) = 0
    # Since the circle passes through the toe, C=0, so roots are x=0 and x=-B/A.
    x_exit_slope = B / (-A) if A > 0 else float('inf')

    if x_exit_slope > 0 and x_exit_slope <= crest_x:
        x_exit = x_exit_slope
    elif x_exit_crest > crest_x:
        x_exit = x_exit_crest
    else:
        x_exit = crest_x

    if x_exit <= 1e-6:
        return float('inf')

    dx = x_exit / num_slices
    slices = []

    for i in range(num_slices):
        x_left = i * dx
        x_right = (i + 1) * dx
        x_mid = (x_left + x_right) / 2

        if x_mid <= crest_x:
            y_ground = x_mid * tan_beta
        else:
            y_ground = H

        disc = R**2 - (x_mid - xc)**2
        if disc <= 0:
            continue
        sqrt_disc = math.sqrt(disc)
        y_upper = yc + sqrt_disc
        y_lower = yc - sqrt_disc

        if y_upper <= y_ground + 1e-9:
            y_slip = y_upper
        else:
            y_slip = y_lower

        h = y_ground - y_slip
        if h <= 0:
            continue

        if abs(y_slip - yc) > 1e-9:
            dy_dx = -(x_mid - xc) / (y_slip - yc)
        else:
            dy_dx = 0.0
        alpha = math.atan(dy_dx)

        W = gamma * h * dx
        l = dx / math.cos(alpha)

        slices.append({
            'x_mid': x_mid, 'dx': dx, 'h': h, 'alpha': alpha,
            'W': W, 'l': l
        })

    if not slices:
        return float('inf')

    F = 1.0

    for _ in range(max_iter):
        numerator = 0.0
        denominator = 0.0

        for s in slices:
            W = s['W']
            alpha = s['alpha']
            b = s['dx']

            u = ru * gamma * s['h']

            m_alpha = math.cos(alpha) + math.sin(alpha) * math.tan(phi) / F

            if m_alpha <= 0:
                continue

            numerator += (c * b + (W - u * b) * math.tan(phi)) / m_alpha
            denominator += W * math.sin(alpha)

        if abs(denominator) < 1e-12:
            return float('inf')

        F_new = numerator / denominator

        if F_new <= 0:
            return float('inf')

        if abs(F_new - F) < tol:
            return round(F_new, 3)

        F = F_new

    return round(F, 3)


def bishop_factor_of_safety(
    slope_height_m: float,
    slope_angle_deg: float,
    cohesion_kPa: float,
    friction_angle_deg: float,
    unit_weight_kN_m3: float,
    pore_pressure_ratio_ru: float = 0.0,
    slip_radius_m: float | None = None,
    slip_center_x_m: float | None = None,
    slip_center_y_m: float | None = None,
    num_slices: int = 30,
    max_iter: int = 50,
    tol: float = 1e-4
) -> float:
    """
    Bishop simplified method for circular slip surface.

    Iterative slice-based solution. The slip circle passes through the
    toe (0,0) and exits at the slope face or crest.

    If the user supplies slip_radius_m, slip_center_x_m, and slip_center_y_m,
    the FOS for that single circle is returned. Otherwise a critical-circle
    search sweeps a grid of (R, xc, yc) candidates and returns the minimum
    FOS, which is the standard Bishop interpretation for slope design.

    Args:
        slope_height_m: Slope height, m
        slope_angle_deg: Slope face angle, degrees
        cohesion_kPa: Effective cohesion, kPa
        friction_angle_deg: Effective friction angle, degrees
        unit_weight_kN_m3: Unit weight of rock/soil, kN/m³
        pore_pressure_ratio_ru: Pore pressure ratio (0 = dry, 0.3 = saturated)
        slip_radius_m: Radius of circular slip surface, m (default: critical search)
        slip_center_x_m: X-coordinate of slip circle center (default: critical search)
        slip_center_y_m: Y-coordinate of slip circle center (default: critical search)
        num_slices: Number of vertical slices
        max_iter: Maximum Bishop iterations
        tol: Convergence tolerance for F

    Returns:
        Factor of safety (F > 1.3 typically acceptable)
    """
    H = slope_height_m
    beta = math.radians(slope_angle_deg)
    phi = math.radians(friction_angle_deg)
    c = cohesion_kPa
    gamma = unit_weight_kN_m3
    ru = pore_pressure_ratio_ru

    if H <= 0:
        return float('inf')
    if beta <= 0:
        return float('inf')

    tan_beta = math.tan(beta)
    crest_x = H / tan_beta if tan_beta > 0 else float('inf')

    # If the user fully specifies a circle, evaluate that one circle only.
    user_circle = (
        slip_radius_m is not None
        and slip_center_x_m is not None
        and slip_center_y_m is not None
    )
    if user_circle:
        return _bishop_single_circle(
            H, tan_beta, crest_x, phi, c, gamma, ru,
            slip_radius_m, slip_center_x_m, slip_center_y_m,
            num_slices, max_iter, tol,
        )

    # Partial specification: use the provided value, search the rest.
    R_grid: list[float]
    if slip_radius_m is not None:
        R_grid = [slip_radius_m]
    else:
        # Radius range: shallow toe circle (R ~ H) to deep circle (R ~ 3H)
        R_grid = [H * r for r in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)]

    # Center grid: for each R, try several yc values; xc is fixed by toe-passing.
    yc_offsets = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

    best_F = float('inf')
    for R in R_grid:
        for yc_off in yc_offsets:
            yc = yc_off * R + 0.3 * H * (1.0 - yc_off)
            xc_sq = R**2 - yc**2
            if xc_sq <= 0:
                continue
            xc = math.sqrt(xc_sq)
            F = _bishop_single_circle(
                H, tan_beta, crest_x, phi, c, gamma, ru,
                R, xc, yc, num_slices, max_iter, tol,
            )
            if F < best_F:
                best_F = F

    return best_F if best_F != float('inf') else float('inf')


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
        slope_height_m=150,
        slope_angle_deg=42,
        cohesion_kPa=250,
        friction_angle_deg=35,
        unit_weight_kN_m3=26,
        pore_pressure_ratio_ru=0.15,
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
    print("Slope stability per SME and Hoek-Bray methods.")
