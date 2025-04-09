"""Call-related phone control functions."""

import re
from ..core import run_command, check_device_connection
from ..config import DEFAULT_COUNTRY_CODE


async def call_number(mcp, phone_number: str) -> str:
    """Make a phone call to the specified number.

    Initiates a call using Android's dialer app through ADB. The number
    will be dialed immediately without requiring user confirmation.

    Args:
        phone_number (str): The phone number to call. Country code 
                          will be automatically added if not provided.

    Returns:
        str: Success message with the number being called, or an error message
             if the call could not be initiated.
    """
    # Add country code if not already included
    if not phone_number.startswith("+"):
        phone_number = DEFAULT_COUNTRY_CODE + phone_number

    # Validate phone number format
    if not phone_number[1:].isdigit():
        return "Invalid phone number format. Please use numeric digits only."

    cmd = f'adb shell am start -a android.intent.action.CALL -d tel:{phone_number}'
    success, output = await run_command(cmd)

    if success:
        return f"Calling {phone_number}..."
    else:
        return f"Failed to initiate call: {output}"


async def end_call(mcp) -> str:
    """End the current phone call.

    Terminates any active phone call by sending the end call keycode
    through ADB.

    Returns:
        str: Success message if the call was ended, or an error message
             if the end call command failed.
    """
    success, output = await run_command("adb shell input keyevent KEYCODE_ENDCALL")

    if success:
        return "Call ended successfully."
    else:
        return f"Failed to end call: {output}"


async def receive_incoming_call(mcp) -> str:
    """Handle an incoming phone call.

    Checks for any incoming calls and provides options to answer
    or reject the call. This function first checks if there's an
    incoming call, then can either answer it or reject it based
    on the action parameter.

    Returns:
        str: Information about any incoming call including the caller
             number, or a message indicating no incoming calls.
    """
    # First check if there's an incoming call by examining the phone state
    cmd = "adb shell dumpsys telephony.registry | grep mCallState"
    success, output = await run_command(cmd)

    if not success:
        return f"Failed to check call state: {output}"

    # Parse the call state (0=idle, 1=ringing, 2=offhook/active)
    call_state = None
    if "mCallState" in output:
        match = re.search(r'mCallState=(\d)', output)
        if match:
            call_state = int(match.group(1))

    if call_state != 1:  # Not ringing
        return "No incoming call detected."

    # Get the caller number
    cmd = "adb shell dumpsys telephony.registry | grep mCallIncomingNumber"
    success, output = await run_command(cmd)

    caller_number = "Unknown"
    if success and "mCallIncomingNumber" in output:
        match = re.search(r'mCallIncomingNumber=([^\s,]+)', output)
        if match:
            caller_number = match.group(1)

    # Provide options for the call
    return f"Incoming call from: {caller_number}\n" \
           f"To answer: Use 'adb shell input keyevent KEYCODE_CALL'\n" \
           f"To reject: Use 'adb shell input keyevent KEYCODE_ENDCALL'" 