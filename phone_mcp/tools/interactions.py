"""Device interaction functions for Phone MCP.
This module provides functions to interact with the device screen and input.
"""

import asyncio
import json
import re
from ..core import run_command, check_device_connection
import logging

logger = logging.getLogger(__name__)


async def get_screen_size():
    """Get the screen size of the device.

    Returns:
        str: JSON string with width and height or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    cmd = "adb shell wm size"
    success, output = await run_command(cmd)

    if success and "Physical size:" in output:
        # Extract dimensions using regex
        match = re.search(r"Physical size: (\d+)x(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            return json.dumps(
                {"width": width, "height": height, "status": "success"}, indent=2
            )

    # Try alternative method if the first one fails
    cmd = "adb shell dumpsys window displays | grep 'init='"
    success, output = await run_command(cmd)

    if success:
        # Look for init dimension in the output
        match = re.search(r"init=(\d+)x(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            return json.dumps(
                {"width": width, "height": height, "status": "success"}, indent=2
            )

    return json.dumps(
        {
            "status": "error",
            "message": "Could not determine screen size",
            "output": output,
        },
        indent=2,
    )


async def tap_screen(x: int, y: int):
    """Tap on the specified coordinates on the device screen.

    Args:
        x (int): X-coordinate
        y (int): Y-coordinate

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # First get screen size to validate coordinates
    size_response = await get_screen_size()
    try:
        size_data = json.loads(size_response)
        if size_data.get("status") == "success":
            width, height = size_data.get("width"), size_data.get("height")

            # Validate coordinates are within screen boundaries
            if x < 0 or x > width or y < 0 or y > height:
                return f"Invalid coordinates ({x},{y}). Device screen size is {width}x{height}."
    except:
        # Continue even if we couldn't validate the coordinates
        pass

    cmd = f"adb shell input tap {x} {y}"
    success, output = await run_command(cmd)

    if success:
        return f"Successfully tapped at coordinates ({x}, {y})"
    else:
        return f"Failed to tap screen: {output}"


async def swipe_screen(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
    """Perform a swipe gesture on the device screen.

    Args:
        x1 (int): Starting X-coordinate
        y1 (int): Starting Y-coordinate
        x2 (int): Ending X-coordinate
        y2 (int): Ending Y-coordinate
        duration_ms (int): Duration of swipe in milliseconds (default: 300)

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Validate duration
    if duration_ms < 0:
        return "Duration must be a positive value"

    cmd = f"adb shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"
    success, output = await run_command(cmd)

    if success:
        return f"Successfully swiped from ({x1}, {y1}) to ({x2}, {y2}) over {duration_ms}ms"
    else:
        return f"Failed to perform swipe: {output}"


async def press_key(keycode: str):
    """Press a key on the device using Android keycode.

    Args:
        keycode (str): Android keycode to press (e.g., "KEYCODE_HOME", "KEYCODE_BACK")
                      Can also be an integer keycode value.

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Common keycodes dictionary for ease of use
    common_keycodes = {
        "home": "KEYCODE_HOME",
        "back": "KEYCODE_BACK",
        "menu": "KEYCODE_MENU",
        "search": "KEYCODE_SEARCH",
        "power": "KEYCODE_POWER",
        "camera": "KEYCODE_CAMERA",
        "volume_up": "KEYCODE_VOLUME_UP",
        "volume_down": "KEYCODE_VOLUME_DOWN",
        "mute": "KEYCODE_VOLUME_MUTE",
        "call": "KEYCODE_CALL",
        "end_call": "KEYCODE_ENDCALL",
        "enter": "KEYCODE_ENTER",
        "delete": "KEYCODE_DEL",
        "brightness_up": "KEYCODE_BRIGHTNESS_UP",
        "brightness_down": "KEYCODE_BRIGHTNESS_DOWN",
        "play": "KEYCODE_MEDIA_PLAY",
        "pause": "KEYCODE_MEDIA_PAUSE",
        "play_pause": "KEYCODE_MEDIA_PLAY_PAUSE",
        "next": "KEYCODE_MEDIA_NEXT",
        "previous": "KEYCODE_MEDIA_PREVIOUS",
    }

    # Check if the keycode is in our common keycodes
    actual_keycode = common_keycodes.get(keycode.lower(), keycode)

    cmd = f"adb shell input keyevent {actual_keycode}"
    success, output = await run_command(cmd)

    if success:
        return f"Successfully pressed {keycode}"
    else:
        return f"Failed to press key: {output}"


async def input_text(text: str):
    """Input text on the device at the current focus.

    Args:
        text (str): Text to input

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Method 1: Try with the standard input text command first
    # Don't escape characters - let the shell handle it
    cmd = f'adb shell input text "{text}"'
    success, output = await run_command(cmd)

    # If successful, return success
    if success:
        return json.dumps({"status": "success", "message": f"Successfully input text: '{text}'"})
    
    # Method 2: If Method 1 fails, try with individual character input
    # This is slower but more reliable for special characters
    logger.info(f"Standard text input failed: {output}. Trying character-by-character method.")
    
    try:
        # Input each character individually
        for char in text:
            if char == ' ':
                char_cmd = "adb shell input keyevent 62"  # Space keycode
            else:
                char_cmd = f'adb shell input text "{char}"'
            
            char_success, char_output = await run_command(char_cmd)
            if not char_success:
                logger.warning(f"Failed to input character '{char}': {char_output}")
                # Add a small delay between characters
                await asyncio.sleep(0.1)
        
        return json.dumps({"status": "success", "message": f"Successfully input text (char-by-char): '{text}'"})
    
    except Exception as e:
        # Method 3: Last resort - try using ADB keyevent codes for each character
        logger.warning(f"Character-by-character input failed: {str(e)}. Trying keyevent method.")
        try:
            for char in text:
                # Get keyevent code for the character
                # This is a simplified approach - a complete implementation would map all characters
                if char == ' ':
                    keycode = 62  # Space
                elif '0' <= char <= '9':
                    keycode = 7 + int(char)  # 0-9 keys
                elif 'a' <= char.lower() <= 'z':
                    keycode = 29 + (ord(char.lower()) - ord('a'))  # a-z keys
                else:
                    # Skip unsupported characters
                    continue
                
                key_cmd = f"adb shell input keyevent {keycode}"
                await run_command(key_cmd)
                await asyncio.sleep(0.1)
            
            return json.dumps({"status": "success", "message": f"Successfully input text (keyevent): '{text}'"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"All text input methods failed: {str(e)}"})
    
    return json.dumps({"status": "error", "message": f"Failed to input text: {output}"})


async def open_url(url: str):
    """Open a URL in the device's default browser.

    Args:
        url (str): URL to open

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    cmd = f'adb shell am start -a android.intent.action.VIEW -d "{url}"'
    success, output = await run_command(cmd)

    if success:
        return f"Successfully opened URL: {url}"
    else:
        return f"Failed to open URL: {output}"
