"""
Tools module for Phone MCP.
Contains all the phone control functionality categorized by domain.
"""

# Import all submodules to make them accessible
from . import call
from . import messaging
from . import contacts
from . import media
from . import apps
from . import system

# Import new modules for extended functionality
from . import interactions
from . import ui
from . import ui_enhanced
from . import ui_monitor
from . import adb_tools

from .media import take_screenshot, start_screen_recording, play_media
from .apps import list_installed_apps, terminate_app, launch_app_activity, launch_intent
from .system import get_current_window, get_app_shortcuts

# Basic interactions
from .interactions import tap_screen, swipe_screen, press_key, input_text, open_url

# Additional ADB tools
from .adb_tools import (
    adb_install, adb_uninstall,  adb_pull, adb_push,
    take_screenshot_and_save, clear_app_data, force_stop_app, go_to_home, open_settings,
    clear_cache_and_restart, force_restart_app
)

# Basic UI inspection
from .ui import dump_ui, find_element_by_text, find_element_by_id, tap_element

# Enhanced UI functionality
from .ui_enhanced import (
    find_element_by_content_desc,
    find_element_by_class,
    find_clickable_elements,
    wait_for_element,
    scroll_to_element,
)

# Import map-related functionality, including environment variable check
try:
    from .maps import get_phone_numbers_from_poi, HAS_VALID_API_KEY
except ImportError:
    # Define defaults if maps module can't be imported
    HAS_VALID_API_KEY = False
    
    async def get_phone_numbers_from_poi(*args, **kwargs):
        """Placeholder function when maps module is not available"""
        import json
        return json.dumps({"error": "Maps functionality not available. Module could not be imported."})

# Basic tools list
__all__ = [
    "take_screenshot",
    "start_screen_recording",
    "play_media",
    "list_installed_apps",
    "terminate_app",
    "get_current_window",
    "get_app_shortcuts",
    "launch_app_activity",
    "launch_intent",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "input_text",
    "open_url",
    "dump_ui",
    "find_element_by_text",
    "find_element_by_id",
    "tap_element",
    "find_element_by_content_desc",
    "find_element_by_class",
    "find_clickable_elements",
    "wait_for_element",
    "scroll_to_element",
    # Additional ADB tools
    "adb_install",
    "adb_uninstall",
    "adb_list_packages",
    "adb_pull",
    "adb_push",
    "take_screenshot_and_save",
    "clear_app_data",
    "force_stop_app",
    "go_to_home",
    "open_settings",
    "clear_cache_and_restart",
    "force_restart_app",
]

# Only add map functionality if there is a valid API key
if HAS_VALID_API_KEY:
    __all__.append("get_phone_numbers_from_poi")
