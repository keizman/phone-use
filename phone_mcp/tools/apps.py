"""App-related phone control functions."""

from ..core import run_command


async def open_app(mcp, app_name: str) -> str:
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
        "weibo": "com.sina.weibo"
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


async def set_alarm(mcp, hour: int, minute: int, label: str = "Alarm") -> str:
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
    # Validate time inputs
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return "Invalid time. Hour must be 0-23 and minute must be 0-59."

    # Format time for display
    time_str = f"{hour:02d}:{minute:02d}"
    escaped_label = label.replace("'", "\\'")

    # Create the alarm using the alarm clock intent
    cmd = (f"adb shell am start -a android.intent.action.SET_ALARM "
           f"-e android.intent.extra.alarm.HOUR {hour} "
           f"-e android.intent.extra.alarm.MINUTES {minute} "
           f"-e android.intent.extra.alarm.MESSAGE '{escaped_label}' "
           f"-e android.intent.extra.alarm.SKIP_UI true")

    success, output = await run_command(cmd)

    if success:
        return f"Alarm set for {time_str} with label '{label}'"
    else:
        return f"Failed to set alarm: {output}" 