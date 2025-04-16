"""App-related phone control functions."""

import json
import re
from ..core import run_command, check_device_connection


async def open_app(app_name: str) -> str:
    """Open an application on the phone.

    Launches the specified application by its package name or attempts to
    find and launch a matching app if a common name is provided.

    Args:
        app_name (str): The application name or package name to open.
                       Common names like "camera", "maps", etc. are supported.

    Returns:
        str: Success message if the app was opened, or an error message
             if the app could not be found or launched.
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Dictionary of common app names to package names
    common_apps = {
        "camera": "com.android.camera",
        "maps": "com.google.android.apps.maps",
        "photos": "com.google.android.apps.photos",
        "settings": "com.android.settings",
        "chrome": "com.android.chrome",
        "youtube": "com.google.android.youtube",
        "gmail": "com.google.android.gm",
        "calendar": "com.google.android.calendar",
        "clock": "com.google.android.deskclock",
        "contacts": "com.android.contacts",
        "calculator": "com.google.android.calculator",
        "files": "com.google.android.apps.nbu.files",
        "music": "com.google.android.music",
        "messages": "com.google.android.apps.messaging",
        "facebook": "com.facebook.katana",
        "instagram": "com.instagram.android",
        "twitter": "com.twitter.android",
        "whatsapp": "com.whatsapp",
        "wechat": "com.tencent.mm",
        "alipay": "com.eg.android.AlipayGphone",
        "taobao": "com.taobao.taobao",
        "jd": "com.jingdong.app.mall",
        "douyin": "com.ss.android.ugc.aweme",
        "weibo": "com.sina.weibo",
    }

    # Check if the app_name is in our dictionary
    package_name = common_apps.get(app_name.lower(), app_name)

    # Launch the app
    cmd = f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
    success, output = await run_command(cmd)

    if success and "No activities found" not in output:
        return f"Successfully opened {app_name}"
    else:
        return f"Failed to open app '{app_name}'. Please check if the app is installed."


async def list_installed_apps(
    filter_keyword=None, only_system=False, only_third_party=False, limit=50
):
    """List installed applications on the device.

    Args:
        filter_keyword (str, optional): Keyword to filter app packages by name
        only_system (bool): If True, only show system apps
        only_third_party (bool): If True, only show third-party apps
        limit (int): Maximum number of apps to return (default: 50)

    Returns:
        str: JSON string with list of installed apps or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Build the command based on options
    if only_system:
        cmd = "adb shell cmd package list packages -s"  # System packages only
    elif only_third_party:
        cmd = "adb shell cmd package list packages -3"  # Third-party packages only
    else:
        cmd = "adb shell cmd package list packages"  # All packages

    success, output = await run_command(cmd)

    if not success:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to get installed apps",
                "output": output,
            },
            indent=2,
        )

    # Process the output - convert package list to array
    package_names = []
    for line in output.strip().split("\n"):
        if line.startswith("package:"):
            package_name = line[8:].strip()  # Remove "package:" prefix

            # Apply keyword filter if provided
            if filter_keyword and filter_keyword.lower() not in package_name.lower():
                continue

            package_names.append(package_name)

    # Sort package names alphabetically
    package_names.sort()
    
    # Apply limit
    package_names = package_names[:limit]
    
    # Get details for all found packages
    detailed_apps = []
    
    for package in package_names:
        # Create basic app info with package name
        app_info = {
            "package_name": package,
            "app_name": package.split(".")[-1],  # Default app name from package
            "is_system": False  # Will be updated below
        }
        
        # Check if this is a system package
        if only_system:
            app_info["is_system"] = True
        elif only_third_party:
            app_info["is_system"] = False
        else:
            # Need to determine if system app
            system_check_cmd = f"adb shell cmd package list packages -s | grep \"{package}\""
            sys_success, sys_output = await run_command(system_check_cmd)
            app_info["is_system"] = (sys_success and package in sys_output)
        
        # Get app label (display name)
        get_label_cmd = f"adb shell dumpsys package {package} | grep -E 'targetSdk|applicationInfo'"
        label_success, label_output = await run_command(get_label_cmd)
        
        if label_success and label_output:
            # Try to extract the app name
            name_match = re.search(r"label=([^=\s]+)", label_output)
            if name_match:
                app_info["app_name"] = name_match.group(1)
                
            # Try to extract target SDK version
            sdk_match = re.search(r"targetSdk=(\d+)", label_output)
            if sdk_match:
                app_info["target_sdk"] = sdk_match.group(1)
                
        # Get app version information
        version_cmd = f"adb shell dumpsys package {package} | grep -E 'versionName|versionCode'"
        version_success, version_output = await run_command(version_cmd)
        
        if version_success and version_output:
            # Extract version name
            version_name_match = re.search(r"versionName=([^=\s]+)", version_output)
            if version_name_match:
                app_info["version_name"] = version_name_match.group(1)
                
            # Extract version code
            version_code_match = re.search(r"versionCode=(\d+)", version_output)
            if version_code_match:
                app_info["version_code"] = version_code_match.group(1)
        
        detailed_apps.append(app_info)
    
    # Create the final result with proper stats
    result = {
        "status": "success",
        "count": len(detailed_apps),
        "apps": detailed_apps
    }
    
    if filter_keyword:
        result["filter"] = filter_keyword
    if only_system:
        result["type"] = "system"
    elif only_third_party:
        result["type"] = "third_party"
    
    return json.dumps(result, indent=2)


async def list_app_activities(package_name: str):
    """List all activities in a specific app package.

    Args:
        package_name (str): Package name of the app

    Returns:
        str: JSON string with list of activities or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Build the command to query activities
    cmd = f"adb shell cmd package query-activities -a android.intent.action.MAIN -c android.intent.category.LAUNCHER --components {package_name}"
    success, output = await run_command(cmd)

    if not success:
        return json.dumps(
            {
                "status": "error",
                "message": f"Failed to get activities for {package_name}",
                "output": output,
            },
            indent=2,
        )

    activities = []

    # Process the output - extract activities
    for line in output.strip().split("\n"):
        if package_name in line:
            # Format: packageName/activityName
            parts = line.strip().split()
            if len(parts) > 0:
                activity = parts[0].strip()
                activities.append(activity)

    return json.dumps(
        {
            "status": "success",
            "package": package_name,
            "count": len(activities),
            "activities": activities,
        },
        indent=2,
    )


async def terminate_app(package_name: str):
    """Force stop an application on the device.

    Args:
        package_name (str): Package name of the app to terminate

    Returns:
        str: Success or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Verify the package exists
    cmd = f"adb shell pm list packages | grep {package_name}"
    success, output = await run_command(cmd)

    if not success or package_name not in output:
        # Try an exact match instead of grep
        verify_cmd = "adb shell pm list packages"
        success, verify_output = await run_command(verify_cmd)

        package_exists = False
        if success:
            for line in verify_output.strip().split("\n"):
                if line.strip() == f"package:{package_name}":
                    package_exists = True
                    break

        if not package_exists:
            return f"Package {package_name} not found on device"

    # Force stop the application
    cmd = f"adb shell am force-stop {package_name}"
    success, output = await run_command(cmd)

    if success:
        return f"Successfully terminated {package_name}"
    else:
        return f"Failed to terminate app: {output}"


async def set_alarm(hour: int, minute: int, label: str = "Alarm") -> str:
    """Set an alarm on the phone.

    Creates a new alarm with the specified time and label using the default
    clock application.

    Args:
        hour (int): Hour in 24-hour format (0-23)
        minute (int): Minute (0-59)
        label (str): Optional label for the alarm (default: "Alarm")

    Returns:
        str: Success message if the alarm was set, or an error message
             if the alarm could not be created.
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Validate time inputs
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return "Invalid time. Hour must be 0-23 and minute must be 0-59."

    # Format time for display
    time_str = f"{hour:02d}:{minute:02d}"
    escaped_label = label.replace("'", "\\'")

    # Create the alarm using the alarm clock intent
    cmd = (
        f"adb shell am start -a android.intent.action.SET_ALARM "
        f"-e android.intent.extra.alarm.HOUR {hour} "
        f"-e android.intent.extra.alarm.MINUTES {minute} "
        f"-e android.intent.extra.alarm.MESSAGE '{escaped_label}' "
        f"-e android.intent.extra.alarm.SKIP_UI true"
    )

    success, output = await run_command(cmd)

    if success:
        return f"Alarm set for {time_str} with label '{label}'"
    else:
        return f"Failed to set alarm: {output}"
