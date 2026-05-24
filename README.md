# MiningToolbox MCP

Mining engineering toolbox as an MCP (Model Context Protocol) server for Hermes Agent.

**Zero IAPWS dependency.** Mining engineering uses empirical, industry-standard
methods for rock, soil, slurry, and ore — none of which are covered by IAPWS
water/steam thermodynamics.

## Why Separate from pygeotoolbox-mcp?

| Toolbox | Domain | Standards | IAPWS? |
|---------|--------|-----------|--------|
| pygeotoolbox-mcp | Geothermal / water / steam | IAPWS-IF97, G11-15, G12-15, G13-15, G14-19 | YES |
| **miningtoolbox-mcp** | **Mining / rock / slurry / blasting** | **Hoek-Brown, SME, NIOSH, USBM, ASHRAE** | **NO** |

Mining and geothermal are **adjacent but distinct** engineering fields.
Water appears in both (dewatering, ventilation), but the core physics differs:
- Geothermal = IAPWS water/steam properties + heat transfer
- Mining = rock mechanics, explosives, slurry rheology, geotechnical stability

## Modules

| Module | Tools | Standard |
|--------|-------|----------|
| `rock_mechanics` | Hoek-Brown, RMR, GSI, Mohr-Coulomb | Hoek (2002), Bieniawski, ISRM |
| `ventilation` | Psychrometrics, heat stress, fan power | ASHRAE, NIOSH, McPherson |
| `slurry` | Density, Bingham plastic, settling | SME, Wilson et al. (2006) |
| `dewatering` | NPSH, pump power, inflow | SME, Hartman & Mutmansky |
| `slope_stability` | Bishop FOS, bench design | Hoek-Bray, SME |
| `blasting` | PPV, overpressure, blast design | USBM RI 8507, AS 2187.2 |

## MCP Tools (24 tools)

```text
Rock Mechanics:
  get_rock_mass_parameters     — Hoek-Brown from GSI, mi
  rock_mass_strength           — Major principal stress at failure
  mohr_coulomb_equiv           — Cohesion + friction angle equivalent
  calculate_rqd                — Rock Quality Designation

Ventilation:
  mine_psychrometrics          — Humidity, enthalpy, wet-bulb, density
  ventilation_pressure_drop    — Darcy-Weisbach ΔP
  fan_shaft_power              — Fan power kW
  heat_stress_assessment       — WBGT classification
  machinery_heat_load          — Heat from diesel + electric

Slurry:
  slurry_density               — Mixture density
  bingham_parameters           — Yield stress, plastic viscosity
  slurry_pipe_dp               — Pipeline pressure drop

Dewatering:
  npsh_available               — NPSH available + status
  pump_shaft_power             — Pump power kW
  groundwater_inflow           — Theim equation inflow

Slope Stability:
  factor_of_safety             — Bishop simplified FOS
  slope_status                 — Risk classification + action
  bench_geometry               — Inter-ramp + overall slope angles

Blasting:
  blast_vibration              — USBM PPV prediction
  vibration_check              — Regulatory limit assessment
  air_overpressure             — Blast noise dB
  blast_design_tool            — Burden, spacing, stemming, charge

Meta:
  toolbox_info                 — Version, modules, standards
```

## Quick Start

```bash
# Install
pip install -e .

# Run MCP server
fastmcp run src/miningtoolbox/mcp_server.py

# Or run as Python module
PYTHONPATH=src python3 src/miningtoolbox/mcp_server.py
```

## Hermes Agent Integration

```text
# In Hermes Agent, add to MCP servers:
- pygeotoolbox-mcp  (for geothermal / water / steam)
- miningtoolbox-mcp (for mining / rock / blasting)

Hermes will automatically discover all 24+29 = 53 tools across both servers.
```

## Tests

Copy test files from hermes-mining-engineering/tests/ and run:

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

All 36 tests pass with zero external dependencies (stdlib Python only).

## License

MIT License — Copyright 2026 Zulfikar Aji Kusworo
