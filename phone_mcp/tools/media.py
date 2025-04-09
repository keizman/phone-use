"""Media-related phone control functions."""

import asyncio
import subprocess
from ..core import run_command
from ..config import SCREENSHOT_PATH, RECORDING_PATH, COMMAND_TIMEOUT


async def take_screenshot(mcp) -> str:
    """Take a screenshot of the phone's current screen.

    Captures the current screen content of the device and saves it to
    the phone's storage in the configured screenshots directory.

    Returns:
        str: Success message with the path to the screenshot, or an error
             message if the screenshot could not be taken.
    """
    # Generate a timestamp for the filename
    timestamp_cmd = "date +%Y%m%d_%H%M%S"
    success, timestamp = await run_command(timestamp_cmd)
    if not success:
        timestamp = "screenshot"  # Fallback name

    filename = f"screenshot_{timestamp.strip()}.png"
    storage_path = f"{SCREENSHOT_PATH}{filename}"

    # Take the screenshot using ADB
    cmd = f"adb shell screencap -p {storage_path}"
    success, output = await run_command(cmd)

    if success:
        return f"Screenshot taken and saved to {storage_path}"
    else:
        return f"Failed to take screenshot: {output}"


async def start_screen_recording(mcp, duration_seconds: int = 30) -> str:
    """Start recording the phone's screen.

    Records the screen activity for the specified duration and saves
    the video to the phone's storage.

    Args:
        duration_seconds (int): Recording duration in seconds (default: 30,
                               max: 180 seconds due to ADB limitations)

    Returns:
        str: Success message with the path to the recording, or an error
             message if the recording could not be started.
    """
    # Limit duration to prevent excessive recordings
    if duration_seconds > 180:
        duration_seconds = 180

    # Generate filename with timestamp
    timestamp_cmd = "date +%Y%m%d_%H%M%S"
    success, timestamp = await run_command(timestamp_cmd)
    if not success:
        timestamp = "recording"  # Fallback name

    filename = f"recording_{timestamp.strip()}.mp4"
    storage_path = f"{RECORDING_PATH}{filename}"

    # Start screen recording with the specified duration
    cmd = f"adb shell screenrecord --time-limit {duration_seconds} {storage_path}"

    try:
        # Run the command in a separate process so we can return immediately
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return (f"Started screen recording. Recording for {duration_seconds} seconds "
                f"and will be saved to {storage_path}")
    except Exception as e:
        return f"Failed to start screen recording: {str(e)}"


async def play_media(mcp) -> str:
    """Play or pause media on the phone.

    Sends the media play/pause keycode to control any currently active media.
    Can be used to play music or videos that were recently playing.

    Returns:
        str: Success message if the command was sent, or an error message
             if the command failed.
    """
    cmd = "adb shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE"
    success, output = await run_command(cmd)

    if success:
        return "Media play/pause command sent successfully"
    else:
        return f"Failed to control media: {output}" 