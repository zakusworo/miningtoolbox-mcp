"""
Blasting vibration and air-overpressure analysis.

Based on:
- USBM RI 8507 — Blast vibration prediction (Langefors-Kihlström)
- Duvall-Petke scaling law for ground vibration
- Australian/New Zealand standard AS 2187.2 — Explosives
- SME Handbook — Drilling and Blasting chapter

NOT based on IAPWS — purely geotechnical / explosives engineering.
"""
import math

# ---------------------------------------------------------------------------
# Ground vibration (PPV) — USBM RI 8507 scaling law
# ---------------------------------------------------------------------------

def peak_particle_velocity(
    distance_m: float,
    charge_per_delay_kg: float,
    site_factor_k: float = 1000.0,
    attenuation_exponent_alpha: float = 1.5
) -> float:
    """
    Predict peak particle velocity (PPV) from blast vibration.
    
    USBM scaling: PPV = K × (D/√W)^(-α)
    
    where D = distance (m), W = charge per delay (kg)
    scaled distance SD = D / √W
    
    Args:
        distance_m: Distance from blast to monitoring point, m
        charge_per_delay_kg: Maximum charge per delay, kg
        site_factor_k: Site-specific K factor (typical 500-2000)
        attenuation_exponent_alpha: Attenuation exponent (typical 1.3-1.8)
    
    Returns:
        PPV in mm/s
    """
    if charge_per_delay_kg <= 0:
        return 0.0
    
    scaled_distance = distance_m / math.sqrt(charge_per_delay_kg)
    
    if scaled_distance <= 0:
        return float('inf')
    
    ppv = site_factor_k * (scaled_distance ** (-attenuation_exponent_alpha))
    return round(ppv, 2)


def vibration_assessment(ppv_mm_s: float, structure_type: str = "residential") -> dict:
    """
    Assess blast vibration against regulatory limits.
    
    Typical regulatory limits (USBM / ISEE guidelines):
    - Residential: 5 mm/s (daytime), 2 mm/s (nighttime)
    - Industrial/commercial: 10 mm/s
    - Historic/fragile: 2 mm/s
    - Mine structures: 25 mm/s
    
    Args:
        ppv_mm_s: Predicted peak particle velocity, mm/s
        structure_type: Type of structure at risk
    
    Returns:
        dict with status, limit, exceedance_factor, recommendation
    """
    limits = {
        "residential": 5.0,
        "commercial": 10.0,
        "industrial": 12.5,
        "historic": 2.0,
        "mine_structure": 25.0,
        "pipeline": 15.0,
        "dam": 5.0
    }
    
    limit = limits.get(structure_type, 5.0)
    exceed = ppv_mm_s / limit if limit > 0 else float('inf')
    
    if exceed <= 0.5:
        status = "negligible"
        rec = "No restrictions needed"
    elif exceed <= 1.0:
        status = "acceptable"
        rec = "Monitor vibrations, maintain current practices"
    elif exceed <= 1.5:
        status = "caution"
        rec = "Reduce charge per delay, increase monitoring frequency"
    elif exceed <= 2.0:
        status = "violation"
        rec = "STOP blast redesign required: reduce charge, increase distance, pre-split"
    else:
        status = "severe_violation"
        rec = "HALT blasting immediately. Engage blast specialist. Risk of structural damage."
    
    return {
        "ppv_mm_s": ppv_mm_s,
        "structure_type": structure_type,
        "regulatory_limit_mm_s": limit,
        "exceedance_factor": round(exceed, 2),
        "status": status,
        "recommendation": rec
    }


# ---------------------------------------------------------------------------
# Air overpressure (blast noise)
# ---------------------------------------------------------------------------

def air_overpressure(
    distance_m: float,
    charge_kg: float,
    site_factor_k: float = 500.0,
    attenuation_exponent: float = 1.4
) -> float:
    """
    Predict air overpressure (blast noise) in decibels.
    
    OP = K × (D/√W)^(-β)  [kPa or dB linear]
    
    Args:
        distance_m: Distance from blast, m
        charge_kg: Total charge, kg
        site_factor_k: Site factor for air blast (typically 200-800)
        attenuation_exponent: Beta (typically 1.2-1.6)
    
    Returns:
        Overpressure in dB(linear) relative to 20 μPa
    """
    if charge_kg <= 0 or distance_m <= 0:
        return 0.0
    
    sd = distance_m / math.sqrt(charge_kg)
    op_linear = site_factor_k * (sd ** (-attenuation_exponent))
    
    # Convert to dB (20 μPa reference)
    op_db = 20 * math.log10(op_linear / 0.02)  # 0.02 Pa = 20 μPa
    
    return round(op_db, 1)


def overpressure_assessment(op_db: float, structure_type: str = "residential") -> dict:
    """
    Assess blast overpressure against damage thresholds.
    
    Typical thresholds:
    - Glass breakage: 115-120 dB
    - Plaster cracking: 125-130 dB
    - Structural damage: 140+ dB
    
    Args:
        op_db: Overpressure in dB(linear)
        structure_type: Type of structure
    
    Returns:
        dict with status, threshold, recommendation
    """
    thresholds = {
        "residential": 115,
        "commercial": 120,
        "historic": 110,
        "mine_structure": 140,
        "pipeline": 130,
        "dam": 115
    }
    
    threshold = thresholds.get(structure_type, 115)
    
    if op_db <= threshold - 10:
        status = "acceptable"
        rec = "No air blast concerns"
    elif op_db <= threshold:
        status = "caution"
        rec = "Monitor overpressure, check stemming and confinement"
    elif op_db <= threshold + 10:
        status = "violation"
        rec = "REDESIGN: improve stemming, decking, use delay sequencing"
    else:
        status = "severe"
        rec = "HALT: inadequate confinement. Risk of glass breakage and public complaint."
    
    return {
        "overpressure_dB": op_db,
        "threshold_dB": threshold,
        "status": status,
        "recommendation": rec
    }


# ---------------------------------------------------------------------------
# Blast design basics
# ---------------------------------------------------------------------------

def blast_design(
    bench_height_m: float,
    burden_m: float | None = None,
    spacing_m: float | None = None,
    stemming_m: float | None = None,
    hole_diameter_mm: float = 150.0,
    rock_density_kg_m3: float = 2600.0,
    powder_factor_kg_m3: float = 0.40
) -> dict:
    """
    Simplified blast design for open-pit bench.
    
    Args:
        bench_height_m: Bench height, m
        burden_m: Burden distance (optimal ~ 25-35 × hole diameter)
        spacing_m: Spacing between holes (~ 1.2 × burden)
        stemming_m: Stemming depth (~ 0.7 × burden)
        hole_diameter_mm: Drill hole diameter, mm
        rock_density_kg_m3: Rock density, kg/m³
        powder_factor_kg_m3: Explosive per m³ rock, kg/m³
    
    Returns:
        dict with burden, spacing, stemming, charge, powder factor
    """
    d_m = hole_diameter_mm / 1000.0
    
    # Rule of thumb burden = 25-35 × diameter
    if burden_m is None:
        burden = 30 * d_m
    else:
        burden = burden_m
    
    if spacing_m is None:
        spacing = 1.2 * burden
    else:
        spacing = spacing_m
    
    if stemming_m is None:
        stemming = 0.7 * burden
    else:
        stemming = stemming_m
    
    # Hole depth = bench height + subdrill
    subdrill = 0.3 * burden
    hole_depth = bench_height_m + subdrill
    
    # Charge per hole
    # Explosive column = hole_depth - stemming - subdrill
    explosive_column = hole_depth - stemming - subdrill
    # Assume ANFO density ~ 0.8 g/cm³ = 800 kg/m³
    explosive_density = 800.0  # kg/m³
    hole_area = math.pi * (d_m / 2) ** 2
    charge_kg = explosive_column * hole_area * explosive_density
    
    # Volume per hole
    volume_per_hole = burden * spacing * bench_height_m
    
    # Powder factor
    actual_pf = charge_kg / volume_per_hole
    
    return {
        "hole_diameter_mm": hole_diameter_mm,
        "hole_depth_m": round(hole_depth, 1),
        "burden_m": round(burden, 1),
        "spacing_m": round(spacing, 1),
        "stemming_m": round(stemming, 1),
        "subdrill_m": round(subdrill, 1),
        "charge_kg": round(charge_kg, 1),
        "volume_m3": round(volume_per_hole, 1),
        "powder_factor_kg_m3": round(actual_pf, 3),
        "target_powder_factor": powder_factor_kg_m3,
        "status": "OK" if 0.3 <= actual_pf <= 0.6 else "REVIEW powder factor"
    }


if __name__ == "__main__":
    # Demo: Blast vibration assessment
    print("Blasting Vibration Analysis")
    print("=" * 50)
    
    # Predict PPV at 500m from 100 kg per delay
    ppv = peak_particle_velocity(500, 100, site_factor_k=800, attenuation_exponent_alpha=1.6)
    print(f"PPV at 500m: {ppv} mm/s")
    
    assessment = vibration_assessment(ppv, "residential")
    print(f"Status:      {assessment['status']}")
    print(f"Limit:       {assessment['regulatory_limit_mm_s']} mm/s")
    print(f"Exceed:      {assessment['exceedance_factor']}×")
    print(f"Action:      {assessment['recommendation']}")
    
    # Air overpressure
    op = air_overpressure(500, 500, site_factor_k=400, attenuation_exponent=1.4)
    op_assess = overpressure_assessment(op, "residential")
    print(f"\nAir overpressure: {op} dB")
    print(f"Status:          {op_assess['status']}")
    print(f"Action:          {op_assess['recommendation']}")
    
    # Blast design
    design = blast_design(bench_height_m=15, hole_diameter_mm=150)
    print(f"\nBlast Design:")
    print(f"  Burden:    {design['burden_m']} m")
    print(f"  Spacing:   {design['spacing_m']} m")
    print(f"  Stemming:  {design['stemming_m']} m")
    print(f"  Charge:    {design['charge_kg']} kg/hole")
    print(f"  Powder factor: {design['powder_factor_kg_m3']} kg/m3")
    
    print("\nNOTE: USBM RI 8507 empirical blast vibration model.")
    print("Detailed design requires blast specialist and site-specific calibration.")
    print("NO IAPWS standard covers blasting or rock fragmentation.")
