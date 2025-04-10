"""Messaging-related phone control functions."""

import asyncio
import subprocess
import json
from ..core import run_command
from ..config import DEFAULT_COUNTRY_CODE


async def send_text_message(mcp, phone_number: str, message: str) -> str:
    """Send a text message to the specified number.

    Uses the phone's messaging app with UI automation to send SMS.
    Process: Opens messaging app, fills recipient and content, automatically clicks send button, then auto-exits app.

    Args:
        phone_number (str): Recipient's phone number. Country code will be automatically added if not included.
                          Example: "13812345678" or "+8613812345678"
        message (str): SMS content. Supports any text, including emojis.
                     Example: "Hello, this is a test message"

    Returns:
        str: String description of the operation result:
             - Success: "Text message sent to {phone_number}"
             - Failure: Message containing error reason, like "Failed to open messaging app: {error}"
                       or "Failed to navigate to send button: {error}"
    """
    # Add country code if not already included
    if not phone_number.startswith("+"):
        phone_number = DEFAULT_COUNTRY_CODE + phone_number

    # Validate phone number format
    if not phone_number[1:].isdigit():
        return "Invalid phone number format. Please use numeric digits only."

    # Escape single quotes in the message
    escaped_message = message.replace("'", "\\'")

    # Open messaging app with the number and message, and auto-exit after sending
    cmd = f"adb shell am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body '{escaped_message}' --ez exit_on_sent true"
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
    
    # Wait a moment for the message to be sent
    await asyncio.sleep(1)
    
    # In case auto-exit doesn't work, press BACK once
    await run_command("adb shell input keyevent 4")

    return f"Text message sent to {phone_number}"


async def receive_text_messages(mcp, limit: int = 5) -> str:
    """Get recent text messages from the phone.

    Retrieves recent SMS messages from the device's SMS database
    using ADB and content provider queries to get structured message data.

    Args:
        limit (int): Maximum number of messages to retrieve (default: 5)
                    Example: 10 will return the 10 most recent messages

    Returns:
        str: JSON string containing messages or an error message:
             - Success: Formatted JSON string with list of messages, each with fields:
                       - address: Sender's number
                       - body: Message content
                       - date: Timestamp
                       - formatted_date: Human-readable date time (like "2023-07-25 14:30:22")
                       - read: Whether message has been read
                       - type: Message type
                       Example: [{"address": "+8613812345678", "body": "Hello", ...}]
             - Failure: Text message describing the error, like "No recent text messages found..."
    """
    # Check for connected device
    from ..core import check_device_connection
    connection_status = await check_device_connection(mcp)
    if "ready" not in connection_status:
        return connection_status
        
    # Method 1: Content provider query - more reliable
    cmd = f'adb shell content query --uri content://sms/inbox --sort "date DESC" --limit {limit}'
    success, output = await run_command(cmd)
    
    if not success or "Error" in output or "Permission" in output:
        # Try alternative command format if first one fails
        cmd = f'adb shell "content query --uri content://sms/ --projection address,date,body,read,type --sort \'date DESC\' --limit {limit}"'
        success, output = await run_command(cmd)
    
    try:
        if success and output.strip():
            # Process the results into a structured JSON format
            rows = output.strip().split("Row: ")
            rows = [r for r in rows if r.strip()]
            
            messages = []
            for row in rows:
                message = {}
                parts = row.split(", ")
                
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        message[key.strip()] = value.strip()
                
                # Format the date if present
                if "date" in message:
                    try:
                        # Convert timestamp to more readable format
                        timestamp = int(message["date"])
                        import datetime
                        date_str = datetime.datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                        message["formatted_date"] = date_str
                    except:
                        # Keep original if conversion fails
                        pass
                        
                messages.append(message)
                
            # Return as JSON
            return json.dumps(messages, indent=2)
        else:
            # Try dumpsys as a fallback
            cmd = 'adb shell dumpsys telephony.registry'
            success, output = await run_command(cmd)
            
            if success and "mNewSms" in output:
                # Try to extract some SMS information from dumpsys output
                import re
                sms_pattern = re.compile(r'mNewSms=.*?from=([^,]+),.*?text=(.*?)(?:,|$)')
                matches = sms_pattern.findall(output)
                
                if matches:
                    messages = [{"address": sender, "body": text} for sender, text in matches[:limit]]
                    return json.dumps(messages, indent=2)
            
            return "No recent text messages found or unable to access SMS database."
    except Exception as e:
        return f"Failed to retrieve text messages: {str(e)}" 