"""
Rock mechanics for mining engineering.

Based on:
- Hoek-Brown (2002) failure criterion for rock masses
- Mohr-Coulomb envelope
- RQD (Rock Quality Designation) — Deere 1967
- GSI (Geological Strength Index) — Hoek & Brown 1997

NOT based on IAPWS — this is purely empirical rock engineering.
"""
import math

# ---------------------------------------------------------------------------
# Rock Mass Rating (RMR) — Bieniawski 1976
# ---------------------------------------------------------------------------

def rmr_basic(rqd: int, spacing: float, condition: int, groundwater: int, orientation: int) -> int:
    """
    Basic RMR (Rock Mass Rating) 1976 version.
    
    Args:
        rqd: Rock Quality Designation 0-100
        spacing: Joint spacing in meters
        condition: Joint condition rating 0-30
        groundwater: Groundwater condition 0-15
        orientation: Favorable/unfavorable orientation adjustment -12 to 0
    
    Returns:
        RMR score 0-100
    """
    # RQD rating
    rqd_rating = min(20, rqd / 5)
    # Joint spacing rating
    if spacing > 2.0:
        spacing_rating = 20
    elif spacing > 0.6:
        spacing_rating = 15
    elif spacing > 0.2:
        spacing_rating = 10
    elif spacing > 0.06:
        spacing_rating = 8
    else:
        spacing_rating = 5
    
    rmr = rqd_rating + spacing_rating + condition + groundwater + orientation
    return max(0, min(100, int(rmr)))


# ---------------------------------------------------------------------------
# Hoek-Brown (2002) Generalized Failure Criterion
# ---------------------------------------------------------------------------

def hoek_brown_parameters(gsi: float, mi: float, D: float = 0.0) -> dict:
    """
    Calculate Hoek-Brown material constants mb, s, a from GSI.
    
    Based on Hoek, Carranza-Torres & Corkum (2002) — 'Hoek-Brown 2002'.
    
    Args:
        gsi: Geological Strength Index 0-100
        mi: Intact rock material constant (e.g., granite ~25, sandstone ~17, shale ~7)
        D: Disturbance factor 0=undisturbed, 1=very disturbed
    
    Returns:
        dict with mb, s, a, E_rm (rock mass modulus in MPa)
    """
    if gsi < 0 or gsi > 100:
        raise ValueError("GSI must be 0 to 100")
    
    # Material constants
    mb = mi * math.exp((gsi - 100) / 28 - 14 * D)
    
    if gsi < 25:
        s = 0.0
        a = 0.65 - gsi / 200
    else:
        s = math.exp((gsi - 100) / 9)
        a = 0.5
    
    # Rock mass modulus (MPa) — Hoek-Diederichs equation
    E_rm = 100000 * (0.5 + 0.5 * math.cos(math.pi * gsi / 100 + math.pi / 6)) ** 2
    if gsi > 50:
        # More accurate for high GSI
        E_rm = 100000 * ((100 - gsi) / 100) ** 2
    
    return {
        "mb": round(mb, 3),
        "s": round(s, 6),
        "a": round(a, 3),
        "E_rm_MPa": round(E_rm, 1),
        "sigma_cm_MPa": round(mb * s**a, 3) if s > 0 else 0.0
    }


def hoek_brown_strength(sigma3: float, mb: float, s: float, a: float, sigma_ci: float) -> float:
    """
    Hoek-Brown (2002) failure criterion.
    sigma1 = sigma3 + sigma_ci * (mb * sigma3/sigma_ci + s)^a
    
    Args:
        sigma3: Confining stress (minor principal stress) in MPa
        mb, s, a: Hoek-Brown material constants
        sigma_ci: Uniaxial compressive strength of intact rock in MPa
    
    Returns:
        Major principal stress at failure (sigma1) in MPa
    """
    if sigma_ci <= 0:
        return 0.0
    ratio = mb * sigma3 / sigma_ci + s
    if ratio < 0:
        ratio = 0.0
    sigma1 = sigma3 + sigma_ci * (ratio ** a)
    return round(sigma1, 3)


# ---------------------------------------------------------------------------
# Mohr-Coulomb equivalent parameters from Hoek-Brown
# ---------------------------------------------------------------------------

def mohr_coulomb_from_hoek_brown(mb: float, s: float, a: float, sigma_ci: float, sigma3_max: float) -> dict:
    """
    Convert Hoek-Brown to equivalent Mohr-Coulomb cohesion and friction angle.
    
    Args:
        sigma3_max: Maximum confining stress for fit (typically 1/3 to 1/4 of overburden)
    
    Returns:
        dict with cohesion_c (MPa), friction_angle (degrees), tensile_strength (MPa)
    """
    # Fit line to Hoek-Brown curve between sigma3 = 0 and sigma3_max
    sigma3_1 = 0.0
    sigma1_1 = hoek_brown_strength(sigma3_1, mb, s, a, sigma_ci)
    
    sigma3_2 = sigma3_max
    sigma1_2 = hoek_brown_strength(sigma3_2, mb, s, a, sigma_ci)
    
    # Slope of line
    if sigma3_2 - sigma3_1 == 0:
        return {"cohesion_MPa": 0.0, "friction_angle_deg": 0.0, "tensile_strength_MPa": 0.0}
    
    slope = (sigma1_2 - sigma1_1) / (sigma3_2 - sigma3_1)
    
    # Mohr-Coulomb: sin(phi) = (slope - 1) / (slope + 1)
    sin_phi = (slope - 1.0) / (slope + 1.0)
    if sin_phi <= -1.0 or sin_phi >= 1.0:
        phi = 0.0
    else:
        phi = math.degrees(math.asin(sin_phi))
    
    # Cohesion: c = sigma1_intercept / (2 * sqrt(slope))
    # Or more precisely: c = (sigma1_1 * (1 - sin_phi)) / (2 * cos(phi_rad))
    phi_rad = math.radians(phi)
    if math.cos(phi_rad) == 0:
        cohesion = 0.0
    else:
        cohesion = (sigma1_1 * (1 - sin_phi)) / (2 * math.cos(phi_rad))
    
    # Tensile strength (Hoek-Brown): sigma_t = -s * sigma_ci / mb
    if mb > 0:
        tensile = -s * sigma_ci / mb
    else:
        tensile = 0.0
    
    return {
        "cohesion_MPa": round(max(0, cohesion), 3),
        "friction_angle_deg": round(phi, 1),
        "tensile_strength_MPa": round(tensile, 3)
    }


# ---------------------------------------------------------------------------
# Rock Quality Designation (RQD)
# ---------------------------------------------------------------------------

def rqd_from_core_recovery(core_length_cm: list) -> float:
    """
    Calculate RQD from drill core lengths (Deere 1967).
    
    RQD = sum of all core pieces > 10 cm / total core length × 100
    
    Args:
        core_length_cm: list of individual core piece lengths in cm
    
    Returns:
        RQD percentage 0-100
    """
    total = sum(core_length_cm)
    if total == 0:
        return 0.0
    sound = sum(p for p in core_length_cm if p >= 10.0)
    rqd = 100.0 * sound / total
    return round(min(100.0, rqd), 1)


if __name__ == "__main__":
    # Demo: Granite rock mass
    gsi = 65
    mi = 25
    D = 0.5
    
    params = hoek_brown_parameters(gsi, mi, D)
    print(f"Hoek-Brown for GSI={gsi}, mi={mi}, D={D}:")
    print(f"  mb={params['mb']}, s={params['s']}, a={params['a']}")
    print(f"  E_rm={params['E_rm_MPa']} MPa")
    
    sigma3 = 5.0  # MPa
    sigma1 = hoek_brown_strength(sigma3, params['mb'], params['s'], params['a'], 150.0)
    print(f"  At σ3={sigma3} MPa: σ1_failure={sigma1} MPa")
    
    mc = mohr_coulomb_from_hoek_brown(params['mb'], params['s'], params['a'], 150.0, 15.0)
    print(f"  Mohr-Coulomb equiv: c={mc['cohesion_MPa']} MPa, φ={mc['friction_angle_deg']}°")
    
    # RQD
    pieces = [15, 8, 22, 5, 30, 12, 18, 7, 25, 10]
    rqd = rqd_from_core_recovery(pieces)
    print(f"  RQD from core: {rqd}%")
    
    print("\nNOTE: All methods are empirical rock engineering (Hoek-Brown, RQD, GSI).")
    print("NO IAPWS standard covers rock mechanics.")
