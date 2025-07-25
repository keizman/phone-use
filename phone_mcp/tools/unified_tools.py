"""
Unified MCP Tools for Phone Control
Consolidates all phone control functionality into 8 core tools for better LLM tool selection
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
import asyncio
import os
import tempfile
import time
from pathlib import Path

from ..core import run_command, check_device_connection
from .omniparser_interface import get_omniparser_client, get_screen_analyzer, get_interaction_manager
from .prompt_engineering import get_task_guidance, detect_bias_requirement

logger = logging.getLogger("phone_mcp")


async def phone_screen_interact(
    action: str,
    target: Optional[str] = None,
    coordinates: Optional[str] = None,
    text: Optional[str] = None,
    use_omniparser: bool = True,
    server_url: str = "http://100.122.57.128:9333",
    bias: Optional[bool] = None,
    delay_seconds: float = 2.0
) -> str:
    """
    ★★★ UNIFIED SCREEN INTERACTION - Use when Omniparser unavailable OR for coordinate-based actions
    
    **WHEN TO USE**: 
    - When Omniparser server is unavailable (fallback mode)
    - For coordinate-based interactions (swipe, scroll)
    - For basic text input operations
    - As secondary option after Omniparser tools
    
    **PRIORITY**: Use omniparser_analyze_screen + omniparser_tap_element_by_uuid first for precision
    
    **CAPABILITIES**:
    - Visual analysis + interaction (when Omniparser available)
    - Coordinate-based fallback interactions
    - Text input with target field detection
    - Gesture support (swipe, scroll, tap variants)
    
    Args:
        action: Action to perform: 'tap', 'long_press', 'double_tap', 'swipe', 'scroll', 'input_text', 'analyze_only'
        target: Element to interact with (text content, description, or UUID from previous analysis)
        coordinates: Direct coordinates as "x,y" or "x1,y1,x2,y2" for swipe actions
        text: Text to input (required for 'input_text' action)
        use_omniparser: Use visual element recognition (recommended: True)
        server_url: Omniparser server URL
        bias: Apply bias correction for media content (auto-detected if not specified)
        delay_seconds: Delay after action operation in seconds (default: 2.0s for TV loading)
        
    Returns:
        JSON with interaction result and screen analysis
        
    Examples:
        - Tap on text: {"action": "tap", "target": "Settings"}
        - Input text: {"action": "input_text", "target": "search box", "text": "hello"}
        - Swipe gesture: {"action": "swipe", "coordinates": "500,800,500,200"}
        - Analyze screen: {"action": "analyze_only"}
    """
    try:
        # Auto-detect bias if not specified
        if bias is None and target:
            bias = detect_bias_requirement(target)
        
        # Get screen analyzer
        analyzer = get_screen_analyzer(server_url)
        
        # Always analyze screen first for context
        analysis_result = await analyzer.analyze_current_screen(use_paddleocr=True)
        
        if action == "analyze_only":
            return json.dumps({
                "status": "success",
                "action": "analyze_only",
                "analysis": analysis_result
            })
        
        # Get interaction manager
        interaction_manager = get_interaction_manager(server_url)
        
        result = {"status": "success", "action": action, "analysis": analysis_result}
        
        if action in ["tap", "long_press", "double_tap"]:
            if target:
                # Find element by content and interact
                elements = analysis_result.get("elements", [])
                matching_element = None
                for elem in elements:
                    if (target.lower() in elem.get("content", "").lower() or 
                        target.lower() in elem.get("description", "").lower() or
                        target == elem.get("uuid")):
                        matching_element = elem
                        break
                
                if matching_element:
                    interaction_result = await interaction_manager.execute_action_by_uuid(
                        matching_element["uuid"], action, bias=bias
                    )
                    result["interaction"] = interaction_result
                else:
                    result["status"] = "error"
                    result["message"] = f"Element not found: {target}"
            
            elif coordinates:
                # Direct coordinate interaction
                x, y = map(int, coordinates.split(","))
                cmd = f"adb shell input tap {x} {y}"
                if action == "long_press":
                    cmd = f"adb shell input swipe {x} {y} {x} {y} 1000"
                elif action == "double_tap":
                    cmd = f"adb shell input tap {x} {y} && adb shell input tap {x} {y}"
                
                success, output = await run_command(cmd)
                result["interaction"] = {"success": success, "output": output}
        
        elif action == "swipe":
            if coordinates:
                coords = coordinates.split(",")
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    cmd = f"adb shell input swipe {x1} {y1} {x2} {y2}"
                    success, output = await run_command(cmd)
                    result["interaction"] = {"success": success, "output": output}
        
        elif action == "scroll":
            # Default scroll gesture
            cmd = "adb shell input swipe 500 800 500 200"
            success, output = await run_command(cmd)
            result["interaction"] = {"success": success, "output": output}
        
        elif action == "input_text" and text:
            # Input text at current focus or find input field
            if target:
                # Find input field and tap first
                elements = analysis_result.get("elements", [])
                input_element = None
                for elem in elements:
                    if ("input" in elem.get("content", "").lower() or
                        "text" in elem.get("description", "").lower() or
                        target.lower() in elem.get("content", "").lower()):
                        input_element = elem
                        break
                
                if input_element:
                    # Tap on input field first
                    await interaction_manager.execute_action_by_uuid(input_element["uuid"], "tap")
            
            # Input text
            escaped_text = text.replace('"', '\\"').replace("'", "\\'")
            cmd = f'adb shell input text "{escaped_text}"'
            success, output = await run_command(cmd)
            result["interaction"] = {"success": success, "output": output}
        
        # Add delay after action operation for TV loading
        if delay_seconds > 0 and action in ["tap", "long_press", "double_tap", "swipe", "scroll", "input_text"]:
            await asyncio.sleep(delay_seconds)
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Screen interaction error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_app_control(
    action: str,
    app_name: Optional[str] = None,
    package_name: Optional[str] = None,
    activity_name: Optional[str] = None
) -> str:
    """
    ★★ APP MANAGEMENT - Use for all app lifecycle operations
    
    Controls Android applications - launch, terminate, list installed apps, and get app info.
    
    Args:
        action: Action to perform: 'launch_app', 'launch_activity', 'terminate', 'force_stop', 'list_apps', 'get_current'
        app_name: App display name (for launch action)
        package_name: App package name (for specific package operations)
        activity_name: Specific activity to launch (for launch_activity)
        
    Returns:
        JSON with operation result
        
    Examples:
        - Launch app: {"action": "launch_app", "app_name": "Settings"}
        - List apps: {"action": "list_apps"}
        - Stop app: {"action": "terminate", "package_name": "com.android.settings"}
        - Get current app: {"action": "get_current"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        if action == "launch_app" and app_name:
            # Launch app by name - fixed to avoid shell command substitution issues
            # First, get the package list
            list_cmd = "adb shell pm list packages"
            success, package_list = await run_command(list_cmd)
            
            if not success:
                return json.dumps({
                    "status": "error",
                    "action": "launch_app",
                    "app_name": app_name,
                    "output": "Failed to get package list"
                })
            
            # Find package containing the app name
            target_package = None
            for line in package_list.strip().split('\n'):
                if ':' in line and app_name.lower() in line.lower():
                    target_package = line.split(':')[1].strip()
                    break
            
            if not target_package:
                return json.dumps({
                    "status": "error",
                    "action": "launch_app",
                    "app_name": app_name,
                    "output": f"Package not found for app: {app_name}"
                })
            
            # Launch the app using the found package
            cmd = f'adb shell monkey -p {target_package} -c android.intent.category.LAUNCHER 1'
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "launch_app",
                "app_name": app_name,
                "package": target_package,
                "output": output
            })
        
        elif action == "launch_activity" and package_name and activity_name:
            # Launch specific activity
            cmd = f"adb shell am start -n {package_name}/{activity_name}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "launch_activity",
                "package_name": package_name,
                "activity_name": activity_name,
                "output": output
            })
        
        elif action == "terminate" and package_name:
            # Terminate app gracefully
            cmd = f"adb shell am force-stop {package_name}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "terminate",
                "package_name": package_name,
                "output": output
            })
        
        elif action == "force_stop" and package_name:
            # Force stop app
            cmd = f"adb shell am kill {package_name}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "force_stop",
                "package_name": package_name,
                "output": output
            })
        
        elif action == "list_apps":
            # List all installed apps
            cmd = "adb shell pm list packages -3"
            success, output = await run_command(cmd)
            if success:
                packages = [line.split(":")[1] for line in output.strip().split("\n") if ":" in line]
                return json.dumps({
                    "status": "success",
                    "action": "list_apps",
                    "packages": packages,
                    "count": len(packages)
                })
        
        elif action == "get_current":
            # Get current foreground app
            cmd = "adb shell dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "get_current",
                "output": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"App control error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_system_control(
    action: str,
    key: Optional[str] = None,
    setting: Optional[str] = None,
    value: Optional[str] = None
) -> str:
    """
    ★★ SYSTEM CONTROL - Use for device settings, navigation, and system operations
    
    Controls Android system functions - navigation keys, settings, home screen, notifications.
    
    Args:
        action: Action to perform: 'press_key', 'go_home', 'open_settings', 'recent_apps', 'notifications', 'back', 'menu'
        key: Key to press (for press_key action): 'home', 'back', 'menu', 'power', 'volume_up', 'volume_down'
        setting: System setting to modify (for setting actions)
        value: Value to set (for setting actions)
        
    Returns:
        JSON with operation result
        
    Examples:
        - Go home: {"action": "go_home"}
        - Press back: {"action": "back"}
        - Open settings: {"action": "open_settings"}
        - Press volume up: {"action": "press_key", "key": "volume_up"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        key_mappings = {
            "home": "3", "back": "4", "menu": "82", "power": "26",
            "volume_up": "24", "volume_down": "25", "recent_apps": "187"
        }
        
        if action == "press_key" and key:
            keycode = key_mappings.get(key.lower(), key)
            cmd = f"adb shell input keyevent {keycode}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "press_key",
                "key": key,
                "output": output
            })
        
        elif action in ["go_home", "home"]:
            cmd = "adb shell input keyevent 3"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "go_home",
                "output": output
            })
        
        elif action == "back":
            cmd = "adb shell input keyevent 4"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "back",
                "output": output
            })
        
        elif action == "open_settings":
            cmd = "adb shell am start -a android.settings.SETTINGS"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "open_settings",
                "output": output
            })
        
        elif action == "recent_apps":
            cmd = "adb shell input keyevent 187"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "recent_apps",
                "output": output
            })
        
        elif action == "notifications":
            cmd = "adb shell cmd statusbar expand-notifications"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "notifications",
                "output": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"System control error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_file_operations(
    action: str,
    source_path: Optional[str] = None,
    destination_path: Optional[str] = None,
    apk_path: Optional[str] = None,
    package_name: Optional[str] = None
) -> str:
    """
    ★ FILE OPERATIONS - Use for file transfers, app installation, and storage management
    
    Manages files and apps - install/uninstall APKs, push/pull files, take screenshots.
    
    Args:
        action: Action to perform: 'install', 'uninstall', 'push', 'pull', 'screenshot', 'clear_cache'
        source_path: Source file path (for push/pull/install actions)
        destination_path: Destination path (for push/pull actions)
        apk_path: APK file path (for install action)
        package_name: Package name (for uninstall/clear_cache actions)
        
    Returns:
        JSON with operation result
        
    Examples:
        - Install APK: {"action": "install", "apk_path": "/path/to/app.apk"}
        - Take screenshot: {"action": "screenshot"}
        - Push file: {"action": "push", "source_path": "/local/file", "destination_path": "/sdcard/file"}
        - Clear app cache: {"action": "clear_cache", "package_name": "com.example.app"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        if action == "install" and apk_path:
            if not os.path.exists(apk_path):
                return json.dumps({
                    "status": "error",
                    "message": f"APK file not found: {apk_path}"
                })
            
            cmd = f"adb install {apk_path}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "install",
                "apk_path": apk_path,
                "output": output
            })
        
        elif action == "uninstall" and package_name:
            cmd = f"adb uninstall {package_name}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "uninstall",
                "package_name": package_name,
                "output": output
            })
        
        elif action == "push" and source_path and destination_path:
            if not os.path.exists(source_path):
                return json.dumps({
                    "status": "error",
                    "message": f"Source file not found: {source_path}"
                })
            
            cmd = f"adb push {source_path} {destination_path}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "push",
                "source_path": source_path,
                "destination_path": destination_path,
                "output": output
            })
        
        elif action == "pull" and source_path and destination_path:
            cmd = f"adb pull {source_path} {destination_path}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "pull",
                "source_path": source_path,
                "destination_path": destination_path,
                "output": output
            })
        
        elif action == "screenshot":
            # Take screenshot and save to temporary file
            timestamp = int(time.time())
            temp_path = f"/tmp/screenshot_{timestamp}.png"
            
            cmd = f"adb shell screencap -p > {temp_path}"
            success, output = await run_command(cmd)
            
            if success:
                return json.dumps({
                    "status": "success",
                    "action": "screenshot",
                    "file_path": temp_path,
                    "message": f"Screenshot saved to {temp_path}"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "action": "screenshot",
                    "message": "Failed to take screenshot"
                })
        
        elif action == "clear_cache" and package_name:
            cmd = f"adb shell pm clear {package_name}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "clear_cache",
                "package_name": package_name,
                "output": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"File operations error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_communication(
    action: str,
    phone_number: Optional[str] = None,
    message: Optional[str] = None,
    contact_name: Optional[str] = None
) -> str:
    """
    ★★ COMMUNICATION - Use for calls, SMS, and contact management
    
    Manages phone communications - make calls, send SMS, manage contacts.
    
    Args:
        action: Action to perform: 'call', 'sms', 'hang_up', 'answer', 'add_contact', 'get_contacts'
        phone_number: Phone number for call/SMS actions
        message: SMS message content
        contact_name: Contact name for contact management
        
    Returns:
        JSON with operation result
        
    Examples:
        - Make call: {"action": "call", "phone_number": "1234567890"}
        - Send SMS: {"action": "sms", "phone_number": "1234567890", "message": "Hello"}
        - Hang up: {"action": "hang_up"}
        - Add contact: {"action": "add_contact", "contact_name": "John", "phone_number": "1234567890"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        if action == "call" and phone_number:
            cmd = f"adb shell am start -a android.intent.action.CALL -d tel:{phone_number}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "call",
                "phone_number": phone_number,
                "output": output
            })
        
        elif action == "sms" and phone_number and message:
            escaped_message = message.replace('"', '\\"')
            cmd = f'adb shell am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body "{escaped_message}"'
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "sms",
                "phone_number": phone_number,
                "message": message,
                "output": output
            })
        
        elif action == "hang_up":
            cmd = "adb shell input keyevent 6"  # KEYCODE_ENDCALL
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "hang_up",
                "output": output
            })
        
        elif action == "answer":
            cmd = "adb shell input keyevent 5"  # KEYCODE_CALL
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "answer",
                "output": output
            })
        
        elif action == "add_contact" and contact_name and phone_number:
            cmd = f'adb shell am start -a android.intent.action.INSERT -t vnd.android.cursor.dir/contact -e name "{contact_name}" -e phone "{phone_number}"'
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "add_contact",
                "contact_name": contact_name,
                "phone_number": phone_number,
                "output": output
            })
        
        elif action == "get_contacts":
            # Open contacts app to view contacts
            cmd = "adb shell am start -a android.intent.action.VIEW -d content://contacts/people"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "get_contacts",
                "output": output,
                "message": "Contacts app opened"
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"Communication error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_media_control(
    action: str,
    media_file: Optional[str] = None,
    recording_time: Optional[int] = None,
    output_path: Optional[str] = None
) -> str:
    """
    ★ MEDIA CONTROL - Use for media playback, recording, and camera functions
    
    Controls media functions - play audio/video, screen recording, camera operations.
    
    Args:
        action: Action to perform: 'play_media', 'start_recording', 'stop_recording', 'take_photo', 'open_camera'
        media_file: Media file path to play
        recording_time: Recording duration in seconds
        output_path: Output file path for recordings
        
    Returns:
        JSON with operation result
        
    Examples:
        - Play media: {"action": "play_media", "media_file": "/sdcard/music.mp3"}
        - Start recording: {"action": "start_recording", "recording_time": 30}
        - Take photo: {"action": "take_photo"}
        - Open camera: {"action": "open_camera"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        if action == "play_media" and media_file:
            cmd = f"adb shell am start -a android.intent.action.VIEW -d file://{media_file}"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "play_media",
                "media_file": media_file,
                "output": output
            })
        
        elif action == "start_recording":
            duration = recording_time or 30
            output_file = output_path or f"/tmp/screen_recording_{int(time.time())}.mp4"
            
            cmd = f"adb shell screenrecord --time-limit {duration} /sdcard/screen_recording.mp4"
            success, output = await run_command(cmd)
            
            if success:
                # Pull the recording to local path
                pull_cmd = f"adb pull /sdcard/screen_recording.mp4 {output_file}"
                await run_command(pull_cmd)
                
                return json.dumps({
                    "status": "success",
                    "action": "start_recording",
                    "duration": duration,
                    "output_file": output_file,
                    "message": f"Screen recording saved to {output_file}"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "action": "start_recording",
                    "message": "Failed to start recording"
                })
        
        elif action == "stop_recording":
            # Stop current recording
            cmd = "adb shell pkill -f screenrecord"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "stop_recording",
                "output": output
            })
        
        elif action == "take_photo":
            cmd = "adb shell am start -a android.media.action.IMAGE_CAPTURE"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "take_photo",
                "output": output,
                "message": "Camera app opened for photo capture"
            })
        
        elif action == "open_camera":
            cmd = "adb shell am start -a android.media.action.STILL_IMAGE_CAMERA"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "open_camera",
                "output": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"Media control error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_web_browser(
    action: str,
    url: Optional[str] = None,
    search_query: Optional[str] = None,
    bookmark_title: Optional[str] = None
) -> str:
    """
    ★ WEB BROWSER - Use for web browsing, search, and URL operations
    
    Controls web browser functions - open URLs, search, bookmarks, navigation.
    
    Args:
        action: Action to perform: 'open_url', 'search', 'bookmark', 'refresh', 'back', 'forward'
        url: URL to open
        search_query: Search query for search engines
        bookmark_title: Title for bookmark
        
    Returns:
        JSON with operation result
        
    Examples:
        - Open URL: {"action": "open_url", "url": "https://www.google.com"}
        - Search web: {"action": "search", "search_query": "weather today"}
        - Refresh page: {"action": "refresh"}
        - Go back: {"action": "back"}
    """
    try:
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({"status": "error", "message": connection_status})
        
        if action == "open_url" and url:
            cmd = f"adb shell am start -a android.intent.action.VIEW -d '{url}'"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "open_url",
                "url": url,
                "output": output
            })
        
        elif action == "search" and search_query:
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            cmd = f"adb shell am start -a android.intent.action.VIEW -d '{search_url}'"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "search",
                "search_query": search_query,
                "url": search_url,
                "output": output
            })
        
        elif action == "refresh":
            # Refresh current page (pull down gesture)
            cmd = "adb shell input swipe 500 300 500 600"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "refresh",
                "output": output
            })
        
        elif action == "back":
            cmd = "adb shell input keyevent 4"  # Back button
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "back",
                "output": output
            })
        
        elif action == "forward":
            # Forward navigation (usually through menu)
            cmd = "adb shell input keyevent 125"  # Menu key
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "forward",
                "output": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action or missing parameters"
        })
        
    except Exception as e:
        logger.error(f"Web browser error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


async def phone_device_info(
    action: str,
    info_type: Optional[str] = None
) -> str:
    """
    ★ DEVICE INFO - Use for device status, connection, and diagnostic information
    
    Retrieves device information - connection status, system info, battery, network status.
    
    Args:
        action: Action to perform: 'check_connection', 'get_system_info', 'get_battery', 'get_network', 'get_storage'
        info_type: Specific info type to retrieve
        
    Returns:
        JSON with device information
        
    Examples:
        - Check connection: {"action": "check_connection"}
        - Get system info: {"action": "get_system_info"}
        - Get battery info: {"action": "get_battery"}
        - Get network info: {"action": "get_network"}
    """
    try:
        if action == "check_connection":
            connection_status = await check_device_connection()
            return json.dumps({
                "status": "success",
                "action": "check_connection",
                "connection_status": connection_status,
                "connected": "ready" in connection_status
            })
        
        elif action == "get_system_info":
            cmd = "adb shell getprop"
            success, output = await run_command(cmd)
            
            if success:
                # Parse key system properties
                lines = output.strip().split('\n')
                system_info = {}
                for line in lines:
                    if '[' in line and ']' in line:
                        key = line.split('[')[1].split(']')[0]
                        value = line.split('[')[2].split(']')[0] if line.count('[') > 1 else ""
                        if key in ['ro.build.version.release', 'ro.product.model', 'ro.product.manufacturer']:
                            system_info[key] = value
                
                return json.dumps({
                    "status": "success",
                    "action": "get_system_info",
                    "system_info": system_info
                })
        
        elif action == "get_battery":
            cmd = "adb shell dumpsys battery"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "get_battery",
                "battery_info": output
            })
        
        elif action == "get_network":
            cmd = "adb shell dumpsys wifi"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "get_network",
                "network_info": output
            })
        
        elif action == "get_storage":
            cmd = "adb shell df"
            success, output = await run_command(cmd)
            return json.dumps({
                "status": "success" if success else "error",
                "action": "get_storage",
                "storage_info": output
            })
        
        return json.dumps({
            "status": "error",
            "message": "Invalid action"
        })
        
    except Exception as e:
        logger.error(f"Device info error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })