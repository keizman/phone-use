"""Messaging-related phone control functions."""

import asyncio
import subprocess
from ..core import run_command
from ..config import DEFAULT_COUNTRY_CODE


async def send_text_message(mcp, phone_number: str, message: str) -> str:
    """Send a text message to the specified number.

    Opens the messaging app with the specified recipient and message,
    then simulates keypresses to send the message.

    Args:
        phone_number (str): The recipient's phone number. Country code
                          will be automatically added if not provided.
        message (str): The text content to send in the message.

    Returns:
        str: Success message if the text was sent, or an error message
             describing what part of the process failed.
    """
    # Add country code if not already included
    if not phone_number.startswith("+"):
        phone_number = DEFAULT_COUNTRY_CODE + phone_number

    # Validate phone number format
    if not phone_number[1:].isdigit():
        return "Invalid phone number format. Please use numeric digits only."

    # Escape single quotes in the message
    escaped_message = message.replace("'", "\\'")

    # Open messaging app with the number and message
    cmd = f"adb shell am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body '{escaped_message}'"
    success, output = await run_command(cmd)

    if not success:
        return f"Failed to open messaging app: {output}"

    # Give the app time to open
    await asyncio.sleep(2)

    # Press right button to focus on send button (keyevent 22)
    success1, output1 = await run_command("adb shell input keyevent 22")
    if not success1:
        return f"Failed to navigate to send button: {output1}"

    # Press enter to send the message (keyevent 66)
    success2, output2 = await run_command("adb shell input keyevent 66")
    if not success2:
        return f"Failed to press send button: {output2}"

    return f"Text message sent to {phone_number}"


async def receive_text_messages(mcp, limit: int = 5) -> str:
    """Check for recent text messages on the phone.

    Retrieves recent SMS messages from the device's SMS database
    using ADB and content provider queries.

    Args:
        limit (int): Maximum number of messages to retrieve (default: 5)

    Returns:
        str: JSON string containing recent messages with sender, content,
             and timestamp, or an error message if retrieval failed.
    """
    # Use the exact command format as specified
    cmd = 'adb shell "content query --uri content://sms/ --projection \'address,date,body\'"'
    
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode('utf-8') if stdout else ""
        
        if process.returncode == 0 and stdout_text.strip():
            # Process the results - limit to requested number of entries
            rows = stdout_text.strip().split("Row: ")
            rows = [r for r in rows if r.strip()]
            
            if len(rows) > limit:
                rows = rows[:limit]
                
            formatted_output = "Row: " + "Row: ".join(rows)
            return f"Recent text messages:\n\n{formatted_output}"
        else:
            return "No recent text messages found."
    except Exception as e:
        return f"Failed to retrieve text messages: {str(e)}" 