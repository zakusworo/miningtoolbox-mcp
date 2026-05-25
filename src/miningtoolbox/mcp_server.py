"""
FastMCP server exposing mining engineering tools.

Empirical mining engineering methods — no water phase properties.
Tools cover: rock mechanics, ventilation, slurry, dewatering,
slope stability, blasting.

Run:  fastmcp run src/miningtoolbox/mcp_server.py
"""
from fastmcp import FastMCP
from miningtoolbox import rock_mechanics, ventilation, slurry, dewatering, slope_stability, blasting

mcp = FastMCP("miningtoolbox")

# ================================================================
# ROCK MECHANICS
# ================================================================

@mcp.tool()
def get_rock_mass_parameters(gsi: float, mi: float, D: float = 0.0, sigma_ci_MPa: float = 100.0) -> dict:
    """Calculate Hoek-Brown rock mass parameters from GSI and mi."""
    return rock_mechanics.hoek_brown_parameters(gsi, mi, D, sigma_ci_MPa)

@mcp.tool()
def rock_mass_strength(sigma3_MPa: float, mb: float, s: float, a: float, sigma_ci_MPa: float) -> float:
    """Hoek-Brown major principal stress at failure."""
    return rock_mechanics.hoek_brown_strength(sigma3_MPa, mb, s, a, sigma_ci_MPa)

@mcp.tool()
def mohr_coulomb_equiv(mb: float, s: float, a: float, sigma_ci_MPa: float, sigma3_max_MPa: float) -> dict:
    """Convert Hoek-Brown to equivalent Mohr-Coulomb cohesion and friction angle."""
    return rock_mechanics.mohr_coulomb_from_hoek_brown(mb, s, a, sigma_ci_MPa, sigma3_max_MPa)

@mcp.tool()
def calculate_rqd(core_pieces_cm: list) -> float:
    """Calculate Rock Quality Designation from drill core lengths."""
    return rock_mechanics.rqd_from_core_recovery(core_pieces_cm)


# ================================================================
# VENTILATION
# ================================================================

@mcp.tool()
def mine_psychrometrics(T_dry_C: float, RH: float, P_kPa: float = 101.325) -> dict:
    """Complete psychrometric state for mine ventilation design."""
    return ventilation.psychrometric_properties(T_dry_C, RH, P_kPa)

@mcp.tool()
def ventilation_pressure_drop(Q_m3s: float, L_m: float, D_m: float, rho_kg_m3: float, friction_factor: float = 0.02) -> float:
    """Darcy-Weisbach pressure drop in mine airway."""
    return ventilation.friction_pressure_drop(Q_m3s, L_m, D_m, rho_kg_m3, friction_factor)

@mcp.tool()
def fan_shaft_power(Q_m3s: float, delta_P_Pa: float, efficiency: float = 0.65) -> float:
    """Fan power for mine ventilation."""
    return ventilation.fan_power(Q_m3s, delta_P_Pa, efficiency)

@mcp.tool()
def heat_stress_assessment(T_dry_C: float, T_wetbulb_C: float, WBGT_C: float | None = None) -> dict:
    """Mine heat stress assessment per NIOSH/ACGIH."""
    return ventilation.heat_stress_index(T_dry_C, T_wetbulb_C, WBGT_C)

@mcp.tool()
def machinery_heat_load(diesel_kW: float, electric_kW: float, load_factor: float = 0.75) -> float:
    """Heat rejected into mine air from machinery."""
    return ventilation.heat_load_from_machinery(diesel_kW, electric_kW, load_factor)


# ================================================================
# SLURRY
# ================================================================

@mcp.tool()
def slurry_density(water_density_kg_m3: float, solids_density_kg_m3: float, Cw: float) -> float:
    """Mixture density of solid-liquid slurry."""
    return slurry.slurry_density(water_density_kg_m3, solids_density_kg_m3, Cw)

@mcp.tool()
def bingham_parameters(water_viscosity_Pas: float, Cw: float, particle_size_mm: float, solids_density_kg_m3: float) -> dict:
    """Bingham plastic rheology parameters for slurry."""
    return slurry.slurry_viscosity_bingham(water_viscosity_Pas, Cw, particle_size_mm, solids_density_kg_m3)

@mcp.tool()
def slurry_pipe_dp(Q_m3s: float, D_m: float, L_m: float, rho_m_kg_m3: float, tau_y_Pa: float, mu_p_Pas: float) -> float:
    """Pressure drop for Bingham plastic slurry in pipe."""
    return slurry.slurry_pressure_drop_bingham(Q_m3s, D_m, L_m, rho_m_kg_m3, tau_y_Pa, mu_p_Pas)


# ================================================================
# DEWATERING
# ================================================================

@mcp.tool()
def npsh_available(P_atm_kPa: float, water_level_below_m: float, suction_losses_kPa: float, T_water_C: float) -> dict:
    """Net Positive Suction Head Available for mine dewatering pump."""
    return dewatering.npsh_available(P_atm_kPa, water_level_below_m, suction_losses_kPa, T_water_C)

@mcp.tool()
def pump_shaft_power(Q_m3h: float, head_m: float, rho_kg_m3: float, efficiency: float = 0.70) -> float:
    """Shaft power for mine dewatering pump."""
    return dewatering.pump_power(Q_m3h, head_m, rho_kg_m3, efficiency)

@mcp.tool()
def groundwater_inflow(k_m_d: float, aquifer_thickness_m: float, drawdown_m: float, influence_radius_m: float, pit_area_m2: float) -> float:
    """Estimate groundwater inflow using Theim equation."""
    return dewatering.groundwater_inflow_empirical(k_m_d, aquifer_thickness_m, drawdown_m, influence_radius_m, pit_area_m2)


# ================================================================
# SLOPE STABILITY
# ================================================================

@mcp.tool()
def factor_of_safety(slope_height_m: float, slope_angle_deg: float, cohesion_kPa: float,
                     friction_angle_deg: float, unit_weight_kN_m3: float,
                     pore_pressure_ratio_ru: float = 0.0, slip_radius_m: float | None = None) -> float:
    """Bishop simplified factor of safety for circular slip surface."""
    return slope_stability.bishop_factor_of_safety(
        slope_height_m, slope_angle_deg, cohesion_kPa, friction_angle_deg,
        unit_weight_kN_m3, pore_pressure_ratio_ru, slip_radius_m
    )

@mcp.tool()
def slope_status(F: float, slope_height_m: float, slope_angle_deg: float) -> dict:
    """Assess slope stability status and recommended action."""
    return slope_stability.slope_stability_status(F, slope_height_m, slope_angle_deg)

@mcp.tool()
def bench_geometry(bench_height_m: float, bench_angle_deg: float, berm_width_m: float,
                   geotechnical_domain: str = "hard_rock") -> dict:
    """Open-pit bench geometry design with catch capacity."""
    return slope_stability.bench_design(bench_height_m, bench_angle_deg, berm_width_m, geotechnical_domain)


# ================================================================
# BLASTING
# ================================================================

@mcp.tool()
def blast_vibration(distance_m: float, charge_per_delay_kg: float,
                    site_factor_k: float = 1000.0, attenuation_alpha: float = 1.5) -> float:
    """Predict peak particle velocity (PPV) from blast."""
    return blasting.peak_particle_velocity(distance_m, charge_per_delay_kg, site_factor_k, attenuation_alpha)

@mcp.tool()
def vibration_check(ppv_mm_s: float, structure_type: str = "residential") -> dict:
    """Assess blast vibration against regulatory limits."""
    return blasting.vibration_assessment(ppv_mm_s, structure_type)

@mcp.tool()
def air_overpressure(distance_m: float, charge_kg: float,
                   site_factor_k: float = 500.0, attenuation_beta: float = 1.4) -> float:
    """Predict air overpressure (blast noise) in dB."""
    return blasting.air_overpressure(distance_m, charge_kg, site_factor_k, attenuation_beta)

@mcp.tool()
def blast_design_tool(bench_height_m: float, hole_diameter_mm: float = 150.0,
                     burden_m: float | None = None, spacing_m: float | None = None,
                     stemming_m: float | None = None) -> dict:
    """Simplified blast design for open-pit bench."""
    return blasting.blast_design(bench_height_m, burden_m, spacing_m, stemming_m, hole_diameter_mm)


# ================================================================
# META
# ================================================================

@mcp.tool()
def toolbox_info() -> dict:
    """Return toolbox version and module count."""
    return {
        "name": "miningtoolbox-mcp",
        "version": "0.1.0",
        "modules": ["rock_mechanics", "ventilation", "slurry", "dewatering", "slope_stability", "blasting"],
        "standards": ["Hoek-Brown 2002", "ASHRAE", "USBM RI 8507", "SME", "NIOSH", "ASTM D7012/D5731"],
        
        
    }


if __name__ == "__main__":
    mcp.run()
