"""Additional ADB tools for phone control functions."""

import json
import os
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from ..core import run_command, check_device_connection

logger = logging.getLogger("phone_mcp")


async def adb_install(path: str, device_id: Optional[str] = None) -> str:
    """Install APK files on the device.
    
    Args:
        path (str): Path to APK file or directory containing APK files
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with installation result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Check if file/directory exists
        if not os.path.exists(path):
            return json.dumps({
                "status": "error",
                "message": f"File or directory does not exist: {path}"
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        
        # Check if path is directory or contains wildcards
        if os.path.isdir(path) or "*" in path:
            cmd = f"adb {device_flag}install-multiple {path}"
        else:
            cmd = f"adb {device_flag}install {path}"
            
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully installed APK from {path}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to install APK: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error installing APK: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error installing APK: {str(e)}"
        })


async def adb_uninstall(package_name: str, device_id: Optional[str] = None) -> str:
    """Uninstall an application from the device.
    
    Args:
        package_name (str): Package name of the application to uninstall
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with uninstall result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f"adb {device_flag}uninstall {package_name}"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully uninstalled {package_name}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to uninstall {package_name}: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error uninstalling package: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error uninstalling package: {str(e)}"
        })




async def adb_pull(remote_path: str, local_path: str, device_id: Optional[str] = None) -> str:
    """Pull files from device to local system.
    
    Args:
        remote_path (str): Path to the file or directory on the device
        local_path (str): Path where to save the file(s) locally
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with pull result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Resolve local path
        resolved_local_path = os.path.expanduser(local_path)
        if not os.path.isabs(resolved_local_path):
            resolved_local_path = os.path.join(os.path.expanduser("~"), local_path)
        
        # Ensure directory exists
        local_dir = os.path.dirname(resolved_local_path)
        os.makedirs(local_dir, exist_ok=True)
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f'adb {device_flag}pull "{remote_path}" "{resolved_local_path}"'
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully pulled file to {resolved_local_path}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to pull file: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error pulling file: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error pulling file: {str(e)}"
        })


async def adb_push(local_path: str, remote_path: str, device_id: Optional[str] = None) -> str:
    """Push files from local system to device.
    
    Args:
        local_path (str): Path to the local file or directory
        remote_path (str): Path on the device where to push the file(s)
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with push result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Resolve local path
        resolved_local_path = os.path.expanduser(local_path)
        if not os.path.isabs(resolved_local_path):
            resolved_local_path = os.path.join(os.path.expanduser("~"), local_path)
        
        # Check if local file exists
        if not os.path.exists(resolved_local_path):
            return json.dumps({
                "status": "error",
                "message": f"Local file does not exist: {resolved_local_path}"
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f'adb {device_flag}push "{resolved_local_path}" "{remote_path}"'
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully pushed file to {remote_path}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to push file: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error pushing file: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error pushing file: {str(e)}"
        })


async def take_screenshot_and_save(output_path: str, device_id: Optional[str] = None, format_type: str = "png") -> str:
    """Take a screenshot and save it to local system.
    
    Args:
        output_path (str): Path where to save the screenshot
        device_id (str, optional): Specific device ID to target
        format_type (str): Image format (png, jpg, webp, etc.)
        
    Returns:
        str: JSON string with screenshot result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Resolve output path
        resolved_output_path = os.path.expanduser(output_path)
        if not os.path.isabs(resolved_output_path):
            resolved_output_path = os.path.join(os.path.expanduser("~"), output_path)
        
        # Ensure directory exists
        output_dir = os.path.dirname(resolved_output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        
        # Use exec-out for direct screenshot capture
        cmd = f'adb {device_flag}exec-out screencap -p > "{resolved_output_path}"'
        
        # Execute command using shell
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return json.dumps({
                "status": "success",
                "message": f"Screenshot saved to {resolved_output_path}",
                "path": resolved_output_path
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to take screenshot: {stderr.decode()}"
            })
            
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error taking screenshot: {str(e)}"
        })




async def clear_app_data(package_name: str, device_id: Optional[str] = None) -> str:
    """Clear all data for a specific application.
    
    This function clears all user data, cache, and settings for the specified app,
    effectively resetting it to a fresh install state.
    
    **Common Usage Patterns:**
    - Clear problematic app data to fix issues
    - Reset app to default state
    - Part of app troubleshooting workflows
    - Chain with launch_app_activity() to restart clean
    
    **Workflow Integration:**
    - Often used after get_current_window() to get package name
    - Typically followed by launch_app_activity() to restart app
    - Can be used with force_stop_app() for thorough reset
    
    **Related Tools:**
    - clear_cache_and_restart(): Combines this with automatic restart
    - force_restart_app(): Force stop then restart (without clearing data)
    
    Args:
        package_name (str): Package name of the application to clear data for
                           (e.g., "com.example.app")
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with clear result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f"adb {device_flag}shell pm clear {package_name}"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully cleared data for {package_name}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to clear data for {package_name}: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error clearing app data: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error clearing app data: {str(e)}"
        })


async def force_stop_app(package_name: str, device_id: Optional[str] = None) -> str:
    """Force stop a running application.
    
    Immediately terminates the specified app and all its processes.
    
    **Common Usage Patterns:**
    - Stop unresponsive or problematic apps
    - Force close apps before data operations
    - Part of app restart workflows
    - Prepare apps for clean restart
    
    **Workflow Integration:**
    - Often used before clear_app_data() or launch_app_activity()
    - Can be chained with get_current_window() to target current app
    - Use with launch_app_activity() for clean restart
    
    **Related Tools:**
    - force_restart_app(): Combines this with automatic restart
    - clear_cache_and_restart(): Clears data and restarts
    
    Args:
        package_name (str): Package name of the application to force stop
                           (e.g., "com.example.app")
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with force stop result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f"adb {device_flag}shell am force-stop {package_name}"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully force stopped {package_name}",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to force stop {package_name}: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error force stopping app: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error force stopping app: {str(e)}"
        })


async def go_to_home(device_id: Optional[str] = None) -> str:
    """Navigate to the home screen.
    
    Args:
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with navigation result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f"adb {device_flag}shell input keyevent KEYCODE_HOME"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": "Successfully navigated to home screen",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to navigate to home: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error navigating to home: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error navigating to home: {str(e)}"
        })


async def open_settings(device_id: Optional[str] = None) -> str:
    """Open the Android Settings app.
    
    Args:
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with settings open result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Build command based on device_id
        device_flag = f"-s {device_id} " if device_id else ""
        cmd = f"adb {device_flag}shell am start -a android.settings.SETTINGS"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": "Successfully opened Settings app",
                "output": output
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to open Settings: {output}"
            })
            
    except Exception as e:
        logger.error(f"Error opening settings: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error opening settings: {str(e)}"
        })


async def clear_cache_and_restart(package_name: str, device_id: Optional[str] = None) -> str:
    """Clear app data and automatically restart the application.
    
    This is a convenience function that combines clear_app_data() and 
    launch_app_activity() into a single operation.
    
    **Common Usage Patterns:**
    - One-step app reset and restart
    - Fix app issues by clearing data and restarting
    - Convenient alternative to manual clear + launch sequence
    
    **Workflow Integration:**
    - Perfect for the workflow: get_current_window() → clear_cache_and_restart()
    - Equivalent to: clear_app_data() → wait → launch_app_activity()
    - Use when you want both operations in one call
    
    **Related Tools:**
    - clear_app_data(): Just clears data (no restart)
    - force_restart_app(): Restart without clearing data
    
    Args:
        package_name (str): Package name of the application to clear and restart
                           (e.g., "com.example.app")
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with clear and restart result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Clear app data first
        clear_result = await clear_app_data(package_name, device_id)
        clear_data = json.loads(clear_result)
        
        if clear_data["status"] != "success":
            return clear_result
        
        # Wait a moment before starting
        await asyncio.sleep(1)
        
        # Launch app
        launch_result = await launch_app_activity(package_name, device_id)
        launch_data = json.loads(launch_result)
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully cleared data and restarted {package_name}",
            "clear_result": clear_data["message"],
            "launch_result": launch_data["message"]
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache and restarting: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error clearing cache and restarting: {str(e)}"
        })


async def force_restart_app(package_name: str, device_id: Optional[str] = None) -> str:
    """Force stop and then restart an application.
    
    This function combines force_stop_app() and launch_app_activity() into
    a single operation, providing a clean restart without clearing data.
    
    **Common Usage Patterns:**
    - Restart frozen or unresponsive apps
    - Clean restart while preserving app data
    - Alternative to clear_cache_and_restart() when you want to keep data
    
    **Workflow Integration:**
    - Use after get_current_window() to restart current app
    - Equivalent to: force_stop_app() → wait → launch_app_activity()
    - Choose this over clear_cache_and_restart() to preserve app data
    
    **Related Tools:**
    - clear_cache_and_restart(): Restart with data clearing
    - force_stop_app(): Just stops app (no restart)
    
    Args:
        package_name (str): Package name of the application to force restart
                           (e.g., "com.example.app")
        device_id (str, optional): Specific device ID to target
        
    Returns:
        str: JSON string with force restart result
    """
    try:
        # Check for connected device
        connection_status = await check_device_connection()
        if "ready" not in connection_status:
            return json.dumps({
                "status": "error",
                "message": connection_status
            })
        
        # Force stop app first
        stop_result = await force_stop_app(package_name, device_id)
        stop_data = json.loads(stop_result)
        
        if stop_data["status"] != "success":
            return stop_result
        
        # Wait a moment before starting
        await asyncio.sleep(1)
        
        # Launch app
        launch_result = await launch_app_activity(package_name, device_id)
        launch_data = json.loads(launch_result)
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully force restarted {package_name}",
            "stop_result": stop_data["message"],
            "launch_result": launch_data["message"]
        })
        
    except Exception as e:
        logger.error(f"Error force restarting app: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error force restarting app: {str(e)}"
        })


# Import launch_app_activity from existing apps module
from .apps import launch_app_activity