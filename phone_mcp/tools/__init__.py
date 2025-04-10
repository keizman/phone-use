"""Phone MCP tools package."""

from .call import call_number, end_call, receive_incoming_call, check_device_connection
from .messaging import send_text_message, receive_text_messages
from .media import take_screenshot, start_screen_recording, play_media
from .apps import open_app, set_alarm
from .contacts import get_contacts
from .system import get_current_window, get_app_shortcuts, launch_activity

# Import map-related functionality, including environment variable check
from .maps import get_poi_info_by_location, HAS_VALID_API_KEY

# Basic tools list
__all__ = [
    "call_number", 
    "end_call", 
    "receive_incoming_call",
    "check_device_connection",
    "send_text_message", 
    "receive_text_messages", 
    "take_screenshot", 
    "start_screen_recording", 
    "play_media",
    "open_app", 
    "set_alarm",
    "get_contacts",
    "get_current_window",
    "get_app_shortcuts",
    "launch_activity",
]

# Only add map functionality if there is a valid API key
if HAS_VALID_API_KEY:
    __all__.append("get_poi_info_by_location") 