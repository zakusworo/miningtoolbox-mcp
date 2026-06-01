"""Tests for the MCP server meta and tool registration."""
import asyncio
from miningtoolbox import mcp_server


def test_toolbox_info_lists_all_modules():
    info = mcp_server.toolbox_info.fn() if hasattr(mcp_server.toolbox_info, "fn") else mcp_server.toolbox_info()
    modules = info["modules"]
    expected = {"rock_mechanics", "ventilation", "slurry", "dewatering",
                "slope_stability", "blasting", "economics"}
    assert set(modules) == expected, (
        f"toolbox_info modules {modules} missing items: {expected - set(modules)}"
    )
    assert info["name"] == "miningtoolbox-mcp"
    assert "version" in info


def test_economics_registered_as_mcp_tool():
    """The economics module's NPV function must be reachable as an MCP tool."""
    mcp = mcp_server.mcp
    tools = asyncio.run(mcp.list_tools())
    tool_names = {t.name for t in tools}
    assert "calculate_npv" in tool_names
    assert "calculate_payback" in tool_names
    assert "calculate_cutoff_grade" in tool_names
    assert "calculate_annual_revenue" in tool_names
    assert "calculate_mining_cost" in tool_names
