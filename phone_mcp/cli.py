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
    
    # Message command
    message_parser = subparsers.add_parser("message", help="Send a text message")
    message_parser.add_argument("number", help="Phone number to send message to")
    message_parser.add_argument("text", help="Message content")
    
    # Check messages command
    check_messages_parser = subparsers.add_parser("messages", help="Check recent text messages")
    check_messages_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
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