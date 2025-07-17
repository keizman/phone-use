import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("phone_call")

# Import all tools
from .core import check_device_connection
from .tools.media import start_screen_recording, play_media
from .tools.apps import list_installed_apps, terminate_app, launch_app_activity
from .tools.system import get_current_window, get_app_shortcuts
# Import screen interface for unified interaction and analysis
from .tools.screen_interface import analyze_screen, interact_with_screen
# Import UI monitoring - use MCP compatible version
from .tools.ui_monitor import mcp_monitor_ui_changes
from .tools.interactions import open_url
# Import additional ADB tools
from .tools.adb_tools import (
    adb_install, adb_uninstall,  adb_pull, adb_push,
    take_screenshot_and_save, clear_app_data, force_stop_app, go_to_home, open_settings,
    clear_cache_and_restart, force_restart_app
)

# Import Omniparser tools
from .tools.omniparser_tools import (
    omniparser_analyze_screen, omniparser_find_elements_by_content,
    omniparser_find_interactive_elements, omniparser_tap_element_by_uuid,
    omniparser_get_element_info, omniparser_get_current_focus_pkg_name,
    omniparser_clear_cache_and_restart, omniparser_get_screen_state,
    omniparser_execute_action_by_uuid
)

# Import prompt engineering tools
from .tools.prompt_engineering import get_task_guidance, get_positioning_guidance, get_bias_recommendation

# Import Android computer integration tools
from .tools.android_computer_integration import (
    android_tap_coordinates, android_long_press_coordinates, android_double_tap_coordinates,
    android_swipe_gesture, android_scroll_screen, android_press_key,
    android_input_text, android_get_screen_info
)


# Import map functionality if available
try:
    from .tools.maps import get_phone_numbers_from_poi, HAS_VALID_API_KEY
except ImportError:
    HAS_VALID_API_KEY = False

# Register all tools with MCP
mcp.tool()(check_device_connection)
# mcp.tool()(take_screenshot)
mcp.tool()(start_screen_recording)
mcp.tool()(play_media)
mcp.tool()(get_current_window)
# mcp.tool()(get_app_shortcuts)
mcp.tool()(launch_app_activity)
mcp.tool()(list_installed_apps)
# mcp.tool()(terminate_app)
mcp.tool()(open_url)

# Register unified screen interface tools
mcp.tool()(analyze_screen)
mcp.tool()(interact_with_screen)
mcp.tool()(mcp_monitor_ui_changes)

# Register additional ADB tools
mcp.tool()(adb_install)
mcp.tool()(adb_uninstall)
mcp.tool()(adb_pull)
mcp.tool()(adb_push)
mcp.tool()(take_screenshot_and_save)
mcp.tool()(clear_app_data)
mcp.tool()(force_stop_app)
mcp.tool()(go_to_home)
mcp.tool()(open_settings)
mcp.tool()(clear_cache_and_restart)
mcp.tool()(force_restart_app)


# Register Omniparser tools
mcp.tool()(omniparser_analyze_screen)
mcp.tool()(omniparser_find_elements_by_content)
mcp.tool()(omniparser_find_interactive_elements)
mcp.tool()(omniparser_tap_element_by_uuid)
mcp.tool()(omniparser_get_element_info)
mcp.tool()(omniparser_get_current_focus_pkg_name)
mcp.tool()(omniparser_clear_cache_and_restart)
mcp.tool()(omniparser_get_screen_state)
mcp.tool()(omniparser_execute_action_by_uuid)

# Register prompt engineering tools
mcp.tool()(get_task_guidance)
mcp.tool()(get_positioning_guidance)
mcp.tool()(get_bias_recommendation)

# Register Android computer integration tools
mcp.tool()(android_tap_coordinates)
mcp.tool()(android_long_press_coordinates)
mcp.tool()(android_double_tap_coordinates)
mcp.tool()(android_swipe_gesture)
mcp.tool()(android_scroll_screen)
mcp.tool()(android_press_key)
mcp.tool()(android_input_text)
mcp.tool()(android_get_screen_info)


# Conditionally register map tool if API key is available
# if HAS_VALID_API_KEY:
#     mcp.tool()(get_phone_numbers_from_poi)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    # Initialize and run the server
    main()
