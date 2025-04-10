#!/usr/bin/env python3
"""
Command-line interface for Phone MCP.
This script provides a direct command line interface to phone control functions.
"""

import argparse
import asyncio
import sys
import json
from .core import check_device_connection
from .tools.call import call_number, end_call, receive_incoming_call
from .tools.messaging import send_text_message, receive_text_messages, get_raw_messages
from .tools.media import take_screenshot, start_screen_recording, play_media
from .tools.apps import open_app, set_alarm
from .tools.contacts import get_contacts
from .tools.system import get_current_window, get_app_shortcuts, launch_activity

# Import map-related functionality, including environment variable check
try:
    from .tools.maps import get_poi_info_by_location, HAS_VALID_API_KEY
except ImportError:
    HAS_VALID_API_KEY = False


async def call(args):
    """Make a phone call."""
    result = await call_number(args.number)
    print(result)


async def hangup(args):
    """End the current call."""
    result = await end_call()
    print(result)


async def check_device(args):
    """Check device connection."""
    result = await check_device_connection()
    print(result)


async def message(args):
    """Send a text message."""
    result = await send_text_message(args.number, args.text)
    print(result)


async def check_messages(args):
    """Check recent text messages."""
    result = await get_raw_messages(limit=args.limit)
    print(result)


async def screenshot(args):
    """Take a screenshot."""
    result = await take_screenshot()
    print(result)


async def record(args):
    """Record screen."""
    result = await start_screen_recording(args.duration)
    print(result)


async def media_control(args):
    """Control media playback."""
    result = await play_media()
    print(result)


async def launch_app(args):
    """Launch an app."""
    result = await open_app(args.name)
    print(result)


async def alarm(args):
    """Set an alarm."""
    result = await set_alarm(args.hour, args.minute, args.label)
    print(result)


async def receive_call(args):
    """Check for incoming calls."""
    result = await receive_incoming_call()
    print(result)


async def check_contacts(args):
    """Retrieve contacts from the phone."""
    result = await get_contacts(limit=args.limit)
    
    # Check if the result is a JSON string
    try:
        import json
        contacts = json.loads(result)
        if isinstance(contacts, list):
            if len(contacts) == 0:
                print("No contacts found.")
            else:
                print(f"Found {len(contacts)} contact(s):")
                for i, contact in enumerate(contacts, 1):
                    name = contact.get('name', contact.get('display_name', 'Unknown'))
                    number = contact.get('number', 'Unknown')
                    print(f"{i}. {name}: {number}")
        else:
            print(result)
    except (json.JSONDecodeError, TypeError):
        # If not JSON, just print the raw result
        print(result)


async def check_window(args):
    """Get current window information."""
    result = await get_current_window()
    
    try:
        import json
        window_info = json.loads(result)
        print("Current Window Information:")
        for key, value in window_info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    except (json.JSONDecodeError, TypeError):
        print(result)


async def check_shortcuts(args):
    """Get app shortcuts."""
    result = await get_app_shortcuts(package_name=args.package)
    
    try:
        import json
        shortcuts_info = json.loads(result)
        
        print("App Shortcuts Information:")
        
        if "packages_with_shortcuts" in shortcuts_info:
            packages = shortcuts_info.pop("packages_with_shortcuts")
            print(f"\nPackages with shortcuts ({len(packages)}):")
            for pkg in packages:
                print(f"  - {pkg}")
        
        for package, info in shortcuts_info.items():
            print(f"\nPackage: {package}")
            
            if "shortcuts" in info and isinstance(info["shortcuts"], list):
                print(f"  Shortcuts ({len(info['shortcuts'])}):")
                for shortcut in info["shortcuts"]:
                    print(f"    • {shortcut.get('id', 'Unknown ID')}")
                    if "title" in shortcut:
                        print(f"      Title: {shortcut['title']}")
                    if "short_label" in shortcut:
                        print(f"      Label: {shortcut['short_label']}")
            elif "shortcuts" in info and isinstance(info["shortcuts"], str):
                print(f"  Raw Shortcut Data: {info['shortcuts'][:100]}...")
            else:
                print("  No specific shortcuts found")
    except (json.JSONDecodeError, TypeError):
        print(result)


async def launch_specific_activity(args):
    """Launch a specific activity with custom action and component."""
    result = await launch_activity(package_component=args.component, action=args.action, extra_args=args.extras)
    print(result)


async def launch_cmd(args):
    """Launch a specific activity (alias for 'launch-activity')."""
    result = await launch_activity(package_component=args.component, action=args.action, extra_args=args.extras)
    print(result)


async def send_sms(args):
    """Send a text message (alias for 'message')."""
    result = await send_text_message(args.number, args.text)
    print(result)


async def receive_sms(args):
    """Check recent text messages (alias for 'messages')."""
    limit = args.limit if hasattr(args, 'limit') else 5
    result = await get_raw_messages(limit=limit)
    print(result)


async def get_poi_by_location(args):
    """Search for POI information (including phone numbers) around a specified location."""
    try:
        result = await get_poi_info_by_location(args.location, args.keywords, args.radius)
        print(result)
    except Exception as e:
        print(json.dumps({"error": f"Failed to get POI information: {str(e)}"}, ensure_ascii=False))


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Phone MCP CLI - Control your Android phone from the command line")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Call command
    call_parser = subparsers.add_parser("call", help="Make a phone call")
    call_parser.add_argument("number", help="Phone number to call")
    
    # End call command
    subparsers.add_parser("hangup", help="End the current call")
    
    # Check device command
    subparsers.add_parser("check", help="Check device connection")
    
    # Send SMS command
    send_sms_parser = subparsers.add_parser("send-sms", help="Send a text message")
    send_sms_parser.add_argument("number", help="Phone number to send message to")
    send_sms_parser.add_argument("text", help="Message content")
    
    # Check messages command
    check_messages_parser = subparsers.add_parser("messages", help="Check recent text messages")
    check_messages_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
    # Contacts command
    contacts_parser = subparsers.add_parser("contacts", help="Retrieve contacts from the phone")
    contacts_parser.add_argument("--limit", type=int, default=20, help="Number of contacts to retrieve")
    
    # Window information command
    subparsers.add_parser("window", help="Get current window information")
    
    # App shortcuts command
    shortcuts_parser = subparsers.add_parser("shortcuts", help="Get app shortcuts")
    shortcuts_parser.add_argument("--package", help="Specific package to get shortcuts for")
    
    # Launch activity command
    launch_activity_parser = subparsers.add_parser("launch-activity", help="Launch a specific activity with custom action and component")
    launch_activity_parser.add_argument("component", help="App component in format 'package/activity'")
    launch_activity_parser.add_argument("--action", help="Intent action to use")
    launch_activity_parser.add_argument("--extras", help="Additional intent arguments")
    
    # Launch command (shorter alias for launch-activity)
    launch_parser = subparsers.add_parser("launch", help="Launch a specific activity (alias for 'launch-activity')")
    launch_parser.add_argument("component", help="App component in format 'package/activity'")
    launch_parser.add_argument("--action", help="Intent action to use")
    launch_parser.add_argument("--extras", help="Additional intent arguments")
    
    # Screenshot command
    subparsers.add_parser("screenshot", help="Take a screenshot of the current screen")
    
    # Screen recording command
    record_parser = subparsers.add_parser("record", help="Record the screen for a specified duration")
    record_parser.add_argument("--duration", type=int, default=30, help="Recording duration in seconds (max 180)")
    
    # Media control command
    subparsers.add_parser("media", help="Play or pause media")
    
    # App launch command
    app_parser = subparsers.add_parser("app", help="Open an app")
    app_parser.add_argument("name", help="App name or package name")
    
    # Alarm command
    alarm_parser = subparsers.add_parser("alarm", help="Set an alarm")
    alarm_parser.add_argument("hour", type=int, help="Hour (0-23)")
    alarm_parser.add_argument("minute", type=int, help="Minute (0-59)")
    alarm_parser.add_argument("--label", default="Alarm", help="Alarm label")
    
    # Incoming call command
    subparsers.add_parser("incoming", help="Check for incoming calls")
    
    # POI command for getting location information
    poi_parser = subparsers.add_parser("get-poi", help="Get POI information (including phone numbers) by location")
    poi_parser.add_argument("location", help="Central coordinate point (longitude,latitude)")
    poi_parser.add_argument("--keywords", help="Search keywords (e.g., 'restaurant', 'hotel')")
    poi_parser.add_argument("--radius", default="1000", help="Search radius in meters (default: 1000)")
    
    # Map-around command (alias for get-poi)
    map_around_parser = subparsers.add_parser("map-around", help="Search POIs around a location (alias for 'get-poi')")
    map_around_parser.add_argument("location", help="Central coordinate point (longitude,latitude)")
    map_around_parser.add_argument("--keywords", help="Search keywords (e.g., 'restaurant', 'hotel')")
    map_around_parser.add_argument("--radius", default="1000", help="Search radius in meters (default: 1000)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Command mapping
    commands = {
        "call": call,
        "hangup": hangup,
        "check": check_device,
        "send-sms": send_sms,
        "messages": check_messages,
        "contacts": check_contacts,
        "window": check_window,
        "shortcuts": check_shortcuts,
        "launch-activity": launch_specific_activity,
        "launch": launch_cmd,  # Alias for launch-activity
        "screenshot": screenshot,
        "record": record,
        "media": media_control,
        "app": launch_app,
        "alarm": alarm,
        "incoming": receive_call,
        "get-poi": get_poi_by_location,
        "map-around": get_poi_by_location  # Alias for get-poi
    }
    
    # Check if command exists in mapping
    if args.command not in commands:
        print(f"Error: Unknown command '{args.command}'")
        parser.print_help()
        return
    
    # Execute the command
    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main() 