# MiningToolbox MCP

Mining engineering toolbox as an MCP (Model Context Protocol) server for Hermes Agent.

All modules use **stdlib Python only** — zero external dependencies beyond `fastmcp`.

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
  get_rock_mass_parameters     — Hoek-Brown from GSI, mi, sigma_ci
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
# Add to Hermes Agent MCP servers:
- miningtoolbox-mcp (for mining / rock / blasting)

Hermes will automatically discover all 24 tools.
```

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

All 36 tests pass with stdlib Python.

## License

MIT License — Copyright 2026 Zulfikar Aji Kusworo
