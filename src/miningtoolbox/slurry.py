"""
Mine slurry transport and rheology.

Based on:
- Bingham plastic model for non-Newtonian slurry flow
- Wilson et al. (2006) — Slurry Transport Using Centrifugal Pumps
- SME Handbook — Slurry Pipeline Design

NOT based on IAPWS — slurry is a two-phase mixture (water + solids).
IAPWS covers water phase properties only; solids are handled empirically.
"""
import math

# ---------------------------------------------------------------------------
# Slurry properties
# ---------------------------------------------------------------------------

def slurry_density(water_density: float, solids_density: float, Cw: float) -> float:
    """
    Mixture density of slurry.
    
    ρ_m = 1 / (Cw/ρ_s + (1-Cw)/ρ_w)
    
    Args:
        water_density: Density of carrier fluid, kg/m3
        solids_density: Density of solids, kg/m3
        Cw: Solids concentration by WEIGHT (0-1)
    
    Returns:
        Slurry density, kg/m3
    """
    if Cw <= 0:
        return water_density
    if Cw >= 1:
        return solids_density
    
    rho_m = 1.0 / (Cw / solids_density + (1.0 - Cw) / water_density)
    return round(rho_m, 2)


def slurry_viscosity_bingham(
    water_viscosity_Pas: float,
    Cw: float,
    particle_size_mm: float,
    solids_density: float
) -> dict:
    """
    Bingham plastic parameters for slurry.
    
    τ = τ_y + μ_p × γ̇
    
    Args:
        water_viscosity_Pas: Base fluid viscosity at operating T
        Cw: Solids weight concentration 0-1
        particle_size_mm: Median particle size, mm
        solids_density: Solids density, kg/m3
    
    Returns:
        dict with yield_stress_Pa, plastic_viscosity_Pas, relative_viscosity
    """
    # Thomas (1965) relative viscosity for suspensions
    # μ_r = 1 + 2.5*Cv + 10.05*Cv² + 0.00273*exp(16.6*Cv)
    # Convert weight to volume concentration (approximate)
    Cv = Cw * water_viscosity_Pas / (Cw * water_viscosity_Pas + (1-Cw) * solids_density)  # rough
    # Better: Cv = Cw * ρ_m / ρ_s
    
    rho_m = slurry_density(1000, solids_density, Cw)
    Cv = Cw * rho_m / solids_density
    
    if Cv > 0.6:
        Cv = 0.6  # packing limit
    
    mu_relative = 1.0 + 2.5 * Cv + 10.05 * Cv**2 + 0.00273 * math.exp(16.6 * Cv)
    mu_plastic = water_viscosity_Pas * mu_relative
    
    # Yield stress increases with concentration and fines content
    # Empirical: τ_y ~ 0.1 * Cv^3 * (1 / d50)^0.5 (very rough)
    # For coarse slurries (sand), τ_y is low. For paste, τ_y is high.
    if particle_size_mm < 0.074:  # fine (silt/clay)
        tau_y = 5.0 * Cv**3
    elif particle_size_mm < 1.0:  # medium
        tau_y = 0.5 * Cv**2.5
    else:  # coarse
        tau_y = 0.05 * Cv**2
    
    return {
        "yield_stress_Pa": round(tau_y, 3),
        "plastic_viscosity_Pas": round(mu_plastic, 6),
        "relative_viscosity": round(mu_relative, 2),
        "volume_concentration_Cv": round(Cv, 3)
    }


# ---------------------------------------------------------------------------
# Slurry pipeline pressure drop
# ---------------------------------------------------------------------------

def slurry_pressure_drop_bingham(
    Q_m3s: float,
    D_m: float,
    L_m: float,
    rho_m: float,
    tau_y_Pa: float,
    mu_p_Pas: float
) -> float:
    """
    Pressure drop for Bingham plastic slurry in pipe.
    
    Uses Buckingham-Reiner equation for laminar flow.
    For turbulent, uses empirical correlation.
    
    Args:
        Q_m3s: Flow rate, m³/s
        D_m: Pipe diameter, m
        L_m: Pipe length, m
        rho_m: Slurry density, kg/m³
        tau_y_Pa: Yield stress, Pa
        mu_p_Pas: Plastic viscosity, Pa·s
    
    Returns:
        Pressure drop, Pa
    """
    A = math.pi * (D_m / 2) ** 2
    v = Q_m3s / A
    
    # Hedstrom number
    if mu_p_Pas <= 0:
        He = 0
    else:
        He = rho_m * tau_y_Pa * (D_m ** 2) / (mu_p_Pas ** 2)
    
    # Reynolds number
    Re = rho_m * v * D_m / mu_p_Pas if mu_p_Pas > 0 else float('inf')
    
    if Re < 2100:
        # Laminar — Buckingham-Reiner
        # Approximate: ΔP/L = (4/3) * (τ_y + 3*μ_p*v/D)  [simplified]
        # More exact requires solving cubic
        dp_per_m = (4.0 / 3.0) * (tau_y_Pa + 3.0 * mu_p_Pas * v / D_m)
    else:
        # Turbulent — empirical (Wilson et al. 2006)
        # Use Darcy-Weisbach with apparent viscosity
        f = 0.02  # rough estimate
        dp_per_m = f * (rho_m * v ** 2) / (2 * D_m)
    
    return round(dp_per_m * L_m, 1)


# ---------------------------------------------------------------------------
# Settling velocity (hindered)
# ---------------------------------------------------------------------------

def hindered_settling_velocity(
    particle_size_mm: float,
    solids_density: float,
    fluid_density: float,
    fluid_viscosity_Pas: float,
    Cv: float
) -> float:
    """
    Hindered settling velocity in slurry.
    
    Uses Richardson-Zaki equation with hindered settling factor.
    
    Args:
        particle_size_mm: Particle diameter, mm
        solids_density: Density of solids, kg/m³
        fluid_density: Density of carrier fluid, kg/m³
        fluid_viscosity_Pas: Viscosity of carrier, Pa·s
        Cv: Volume concentration of solids 0-1
    
    Returns:
        Settling velocity, m/s
    """
    d = particle_size_mm / 1000.0  # m
    g = 9.81
    delta_rho = solids_density - fluid_density
    
    # Stokes regime for small particles
    if d < 0.1e-3:  # <0.1 mm
        v_stokes = (delta_rho * g * d**2) / (18 * fluid_viscosity_Pas)
    else:
        # Intermediate — use empirical
        v_stokes = 0.1  # m/s placeholder
    
    # Hindered settling: v_h = v_stokes * (1 - Cv)^n
    # n ~ 4.65 for low Re, ~2.5 for high Re
    n = 4.65
    v_h = v_stokes * ((1.0 - Cv) ** n)
    
    return round(v_h, 4)


if __name__ == "__main__":
    # Demo: Copper ore slurry pipeline
    Cw = 0.35  # 35% solids by weight
    d50 = 0.5  # mm
    rho_s = 2800  # kg/m3 (chalcopyrite)
    rho_w = 1000  # fresh water at 25 C
    
    rho_m = slurry_density(rho_w, rho_s, Cw)
    print(f"Copper ore slurry: Cw={Cw*100:.0f}%, d50={d50}mm")
    print(f"  Slurry density:     {rho_m:.1f} kg/m3")
    
    bingham = slurry_viscosity_bingham(0.001, Cw, d50, rho_s)
    print(f"  Yield stress:       {bingham['yield_stress_Pa']:.3f} Pa")
    print(f"  Plastic viscosity:  {bingham['plastic_viscosity_Pas']:.4f} Pa·s")
    print(f"  Volume conc:        {bingham['volume_concentration_Cv']:.3f}")
    
    # Pipeline: 0.3 m diameter, 1000 m, 0.5 m3/s
    dp = slurry_pressure_drop_bingham(0.5, 0.3, 1000, rho_m, bingham['yield_stress_Pa'], bingham['plastic_viscosity_Pas'])
    print(f"  Pressure drop:      {dp:.0f} Pa ({dp/1000:.1f} kPa)")
    
    # Settling
    v_settle = hindered_settling_velocity(d50, rho_s, rho_w, 0.001, bingham['volume_concentration_Cv'])
    print(f"  Hindered settling:  {v_settle:.4f} m/s")
    
    print("\nNOTE: Slurry uses Bingham plastic + empirical settling models.")
    print("NO IAPWS standard covers two-phase solid-liquid mixtures.")
