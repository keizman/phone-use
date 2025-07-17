import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("phone_call")

# Import optimized 12-tool architecture
# Core Professional Layer (★★★★-★★★)
from .tools.omniparser_tools import (
    omniparser_analyze_screen,
    omniparser_tap_element_by_uuid,
    omniparser_execute_action_by_uuid
)
from .tools.prompt_engineering import get_task_guidance, get_tv_app_guidance

# Common Function Layer (★★)
from .tools.unified_tools import (
    phone_screen_interact,
    phone_app_control,
    phone_system_control,
    phone_communication
)

# Auxiliary Layer (★)
from .tools.unified_tools import (
    phone_file_operations,
    phone_media_control,
    phone_web_browser,
    phone_device_info
)

# Register Core Professional Tools (★★★★-★★★)
mcp.tool()(omniparser_analyze_screen)       # ★★★★ PRIMARY VISUAL ANALYSIS
mcp.tool()(omniparser_tap_element_by_uuid)  # ★★★★ PRECISION INTERACTION
mcp.tool()(omniparser_execute_action_by_uuid) # ★★★ ADVANCED INTERACTIONS
mcp.tool()(get_task_guidance)               # ★★★ AI TASK ORCHESTRATION
mcp.tool()(get_tv_app_guidance)             # ★★★ TV APP AUTOMATION GUIDANCE

# Register Common Function Tools (★★)
mcp.tool()(phone_screen_interact)           # ★★★ UNIFIED SCREEN INTERACTION
mcp.tool()(phone_app_control)               # ★★ APP MANAGEMENT
mcp.tool()(phone_system_control)            # ★★ SYSTEM CONTROL
mcp.tool()(phone_communication)             # ★★ COMMUNICATION

# Register Auxiliary Tools (★)
mcp.tool()(phone_file_operations)           # ★ FILE OPERATIONS
mcp.tool()(phone_media_control)             # ★ MEDIA CONTROL
mcp.tool()(phone_web_browser)               # ★ WEB BROWSER
mcp.tool()(phone_device_info)               # ★ DEVICE INFO

def main():
    """Run the MCP server with optimized 12-tool architecture."""
    print(" Starting MCP Server with Optimized Tool Architecture")
    
    mcp.run(transport="stdio")


if __name__ == "__main__":
    # Initialize and run the server
    main()