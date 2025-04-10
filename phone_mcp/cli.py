#!/usr/bin/env python3
"""
Command-line interface for Phone MCP.
This script provides a direct command line interface to phone control functions.
"""

import argparse
import asyncio
import sys
from .core import check_device_connection
from .tools.call import call_number, end_call, receive_incoming_call
from .tools.messaging import send_text_message, receive_text_messages
from .tools.media import take_screenshot, start_screen_recording, play_media
from .tools.apps import open_app, set_alarm
from .tools.contacts import get_contacts
from .tools.system import get_current_window, get_app_shortcuts, launch_activity


async def call(args):
    """Make a phone call."""
    # Using None as placeholder for mcp
    result = await call_number(None, args.number)
    print(result)


async def hangup(args):
    """End the current call."""
    result = await end_call(None)
    print(result)


async def check_device(args):
    """Check device connection."""
    result = await check_device_connection(None)
    print(result)


async def message(args):
    """Send a text message."""
    result = await send_text_message(None, args.number, args.text)
    print(result)


async def check_messages(args):
    """Check recent text messages."""
    result = await receive_text_messages(None, args.limit)
    print(result)


async def screenshot(args):
    """Take a screenshot."""
    result = await take_screenshot(None)
    print(result)


async def record(args):
    """Record screen."""
    result = await start_screen_recording(None, args.duration)
    print(result)


async def media_control(args):
    """Control media playback."""
    result = await play_media(None)
    print(result)


async def launch_app(args):
    """Launch an app."""
    result = await open_app(None, args.name)
    print(result)


async def alarm(args):
    """Set an alarm."""
    result = await set_alarm(None, args.hour, args.minute, args.label)
    print(result)


async def receive_call(args):
    """Check for incoming calls."""
    result = await receive_incoming_call(None)
    print(result)


async def check_contacts(args):
    """Retrieve contacts from the phone."""
    result = await get_contacts(None, args.limit)
    
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
    result = await get_current_window(None)
    
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
    result = await get_app_shortcuts(None, args.package)
    
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
    result = await launch_activity(None, args.component, args.action, args.extras)
    print(result)


async def launch_cmd(args):
    """Launch a specific activity (alias for 'launch-activity')."""
    result = await launch_activity(None, args.component, args.action, args.extras)
    print(result)


async def send_sms(args):
    """Send a text message (alias for 'message')."""
    result = await send_text_message(None, args.number, args.text)
    print(result)


async def receive_sms(args):
    """Check recent text messages (alias for 'messages')."""
    result = await receive_text_messages(None, args.limit)
    print(result)


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
    
    # Message command (original)
    message_parser = subparsers.add_parser("message", help="Send a text message")
    message_parser.add_argument("number", help="Phone number to send message to")
    message_parser.add_argument("text", help="Message content")
    
    # Send SMS command (new, more intuitive name)
    send_sms_parser = subparsers.add_parser("send-sms", help="Send a text message")
    send_sms_parser.add_argument("number", help="Phone number to send message to")
    send_sms_parser.add_argument("text", help="Message content")
    
    # SMS send command (alternative)
    sms_send_parser = subparsers.add_parser("sms-send", help="Send a text message")
    sms_send_parser.add_argument("number", help="Phone number to send message to")
    sms_send_parser.add_argument("text", help="Message content")
    
    # Check messages command (original)
    check_messages_parser = subparsers.add_parser("messages", help="Check recent text messages")
    check_messages_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
    # Read SMS command (new, more intuitive name)
    read_sms_parser = subparsers.add_parser("read-sms", help="Read recent text messages")
    read_sms_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
    # SMS list command (alternative)
    sms_list_parser = subparsers.add_parser("sms-list", help="List recent text messages")
    sms_list_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
    # Contacts command
    contacts_parser = subparsers.add_parser("contacts", help="Retrieve contacts from the phone")
    contacts_parser.add_argument("--limit", type=int, default=20, help="Number of contacts to retrieve")
    
    # Window information command
    subparsers.add_parser("window", help="Get current window information")
    
    # App shortcuts command
    shortcuts_parser = subparsers.add_parser("shortcuts", help="Get app shortcuts")
    shortcuts_parser.add_argument("--package", help="Specific package to get shortcuts for")
    
    # Launch specific activity command
    activity_parser = subparsers.add_parser("launch-activity", help="Launch a specific activity with custom action")
    activity_parser.add_argument("--component", required=True, help="App component in format 'package/activity' (e.g. 'com.example.app/.MainActivity')")
    activity_parser.add_argument("--action", help="Intent action to use (e.g. 'android.intent.action.VIEW')")
    activity_parser.add_argument("--extras", help="Additional intent arguments as a single string")
    
    # Launch command (shorter alias for launch-activity)
    launch_parser = subparsers.add_parser("launch", help="Launch a specific activity (shorter alias)")
    launch_parser.add_argument("--component", required=True, help="App component in format 'package/activity'")
    launch_parser.add_argument("--action", help="Intent action to use")
    launch_parser.add_argument("--extras", help="Additional intent arguments")
    
    # Screenshot command
    subparsers.add_parser("screenshot", help="Take a screenshot")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record screen")
    record_parser.add_argument("--duration", type=int, default=30, help="Recording duration in seconds")
    
    # Media control command
    subparsers.add_parser("media", help="Control media playback")
    
    # Launch app command
    app_parser = subparsers.add_parser("app", help="Launch an app")
    app_parser.add_argument("name", help="App name or package name")
    
    # Set alarm command
    alarm_parser = subparsers.add_parser("alarm", help="Set an alarm")
    alarm_parser.add_argument("hour", type=int, help="Hour (0-23)")
    alarm_parser.add_argument("minute", type=int, help="Minute (0-59)")
    alarm_parser.add_argument("--label", default="Alarm", help="Alarm label")
    
    # Receive call command
    subparsers.add_parser("incoming", help="Check for incoming calls")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Command mapping
    commands = {
        "call": call,
        "hangup": hangup,
        "check": check_device,
        "message": message,
        "messages": check_messages,
        "send-sms": send_sms,
        "sms-send": send_sms,
        "read-sms": receive_sms,
        "sms-list": receive_sms,
        "contacts": check_contacts,
        "window": check_window,
        "shortcuts": check_shortcuts,
        "launch-activity": launch_specific_activity,
        "launch": launch_cmd,
        "screenshot": screenshot,
        "record": record,
        "media": media_control,
        "app": launch_app,
        "alarm": alarm,
        "incoming": receive_call
    }
    
    # Execute the command
    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main() 