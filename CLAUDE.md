# Mining Engineering Standards

This toolbox implements mining engineering calculations following these rules.

## Units

- Always use SI units internally:
  - Stress/Strength: MPa (state if using kPa or Pa)
  - Pressure: kPa or Pa — state which
  - Density: kg/m³
  - Flow rate: m³/h or m³/s — state which
  - Length: m
  - Time: s or year — state which
- If converting from legacy units (psi, ton, ft), document the conversion factor explicitly.

## Rock Mechanics

- Prefer Hoek-Brown (2002) for rock mass strength.
- Use RMR (Bieniawski) or GSI for rock mass classification.
- State intact rock UCS (σ_ci) and material constant (mi).
- Document disturbance factor D (0.0 = undisturbed, 1.0 = heavily blasted).
- Convert to Mohr-Coulomb for slope stability if needed.
- Never use uniaxial compressive strength of intact rock directly for rock mass design.

## Slope Stability

- Use Bishop simplified method for circular failure.
- Check FOS against minimum thresholds:
  - Permanent slopes: FOS ≥ 1.5
  - Temporary slopes: FOS ≥ 1.3
  - Seismic/pseudo-static: FOS ≥ 1.1
- State pore pressure ratio ru and how it was estimated.
- For bench design: specify bench height, face angle, berm width, and resulting inter-ramp / overall slope angles.

## Blasting

- Use USBM RI 8507 scaling law for PPV prediction:
  - PPV = K × (R / √W)^(-α)
  - Document K and α for your site.
- Compare predicted PPV against regulatory limits:
  - Residential: 5 mm/s
  - Industrial: 10 mm/s
  - Heritage: 2 mm/s
- Air overpressure: compare against 120 dB (damaging) and 115 dB (annoyance).

## Ventilation

- Psychrometric calculations use ASHRAE or Tetens equations.
- Heat stress index uses WBGT (Wet Bulb Globe Temperature) per ACGIH/NIOSH.
- Specify work/rest schedules based on heat stress classification.
- Fan power: include both shaft power and motor efficiency.

## Slurry Transport

- Use Bingham plastic model for non-Newtonian slurry.
- State solids concentration by weight (Cw) or by volume.
- Document particle density and fluid density.
- Pressure drop: include both viscous and yield stress components.

## Dewatering

- NPSH available = atmospheric pressure + static head – suction losses – vapor pressure.
- NPSH required must include 3 m safety margin.
- Pump power: P = ρ × g × Q × H / (3600 × η)
- Groundwater inflow: use Theim equation for steady-state, document assumptions.

## Testing

- Every module must have tests with:
  - Known-value checks against published data or textbook examples
  - Monotonicity checks (e.g., FOS decreases with increasing ru)
  - Invalid-input rejection (e.g., negative density raises ValueError)
  - Boundary condition checks (e.g., RQD = 0 for all pieces < 10 cm)

## Agentic AI Workflow

- **Explore**: Read code and data before editing. Understand the physics.
- **Plan**: Write a brief plan before modifying code.
- **Code**: Implement with tests first (TDD).
- **Verify**: Run tests and check physical plausibility.
- **Review**: Send risky code to a subagent reviewer (AGENTS.md).
- **Document**: Update README.md and CLAUDE.md if conventions change.
