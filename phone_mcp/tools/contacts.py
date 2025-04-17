"""
Contact-related functions for Phone MCP.
This module provides functions to access and manage contacts on the phone.
"""

import asyncio
import json
import re
from ..core import run_command


async def _check_contact_permissions():
    """Check if the app has the necessary permissions to access contacts."""
    # Try to check if we have permission by running a simple query
    cmd = "adb shell pm list permissions -g"
    success, output = await run_command(cmd)

    # Use Python to check for contacts permissions
    return success and any("contacts" in line.lower() for line in output.splitlines())


async def get_contacts(limit=20):
    """Retrieve contacts from the phone.

    Core function for accessing the contacts database on the device.
    Fetches contact information including names and phone numbers.
    Returns data in structured JSON format.

    Args:
        limit (int): Number of contacts to retrieve, defaults to 20

    Returns:
        str: JSON string with contact data or error message
    """
    # Check for connected device
    from ..core import check_device_connection

    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return connection_status

    # Check permissions
    has_permissions = await _check_contact_permissions()
    if not has_permissions:
        return "Cannot access contacts. Permission may be denied. Please check your device settings."

    try:
        # Use the verified working command first - this is known to work
        cmd = f"adb shell content query --uri content://contacts/phones/"
        success, output = await run_command(cmd)

        if success and "Row:" in output:
            # Process the output
            contacts = []
            rows = output.strip().split("Row: ")
            # Skip empty first element if it exists
            if rows and not rows[0].strip():
                rows = rows[1:]

            for row in rows:
                if not row.strip():
                    continue

                contact = {}
                parts = row.split(", ")

                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        # Only add non-NULL values
                        if value and value != "NULL" and value != "null":
                            contact[key.strip()] = value.strip()

                # Add the contact if it has at least name and number
                if ("name" in contact or "display_name" in contact) and len(contact) > 0:
                    # Normalize the contact data
                    if "display_name" in contact and "name" not in contact:
                        contact["name"] = contact["display_name"]
                    # Ensure phone field is called 'phone' and is consistent
                    if "number" in contact:
                        contact["phone"] = contact["number"]
                    
                    contacts.append(contact)

            if contacts:
                return json.dumps(contacts, indent=2)

        # If our first approach fails, try the original fallback approaches
        # Other methods are kept as fallbacks but the main method should work on most devices

        # Try dumpsys contact
        cmd = "adb shell dumpsys contact"
        success, output = await run_command(cmd)

        if success and "Contact" in output and len(output) > 100:
            # Parse the output from dumpsys
            contacts = []

            # Extract contacts with a regex pattern
            contact_pattern = re.compile(r"name=([^,]+),\s+number=([^,]+)")
            matches = contact_pattern.findall(output)

            for name, number in matches:
                contacts.append({
                    "name": name.strip(), 
                    "phone": number.strip()
                })

            if contacts:
                # Limit the results if needed
                if len(contacts) > limit:
                    contacts = contacts[:limit]
                return json.dumps(contacts, indent=2)

        # Further fallback methods continue...
        # These are kept for device compatibility but rarely needed now

        # If prior methods didn't work, try the different content URIs
        cmd = f"adb shell content query --uri content://com.android.contacts/data --projection display_name:data1:mimetype --limit {limit}"
        success, output = await run_command(cmd)

        if not success or "usage:" in output:
            cmd = f"adb shell content query --uri content://contacts/data --projection display_name:data1:mimetype --limit {limit}"
            success, output = await run_command(cmd)

        if not success or "usage:" in output:
            cmd = f"adb shell content query --uri content://contacts/phones --limit {limit}"
            success, output = await run_command(cmd)

        if not success or "usage:" in output:
            cmd = f"adb shell content query --uri content://com.android.contacts/data/phones --limit {limit}"
            success, output = await run_command(cmd)

        if not success or "usage:" in output:
            cmd = (
                'adb shell "sqlite3 /data/data/com.android.providers.contacts/databases/contacts2.db \'SELECT display_name, data1 FROM raw_contacts JOIN data ON (raw_contacts._id = data.raw_contact_id) WHERE mimetype_id = (SELECT _id FROM mimetypes WHERE mimetype = "vnd.android.cursor.item/phone_v2") LIMIT '
                + str(limit)
                + ";'\""
            )
            success, output = await run_command(cmd)

        if (
            not success
            or not output.strip()
            or "Error:" in output
            or "usage:" in output
        ):
            return "Failed to retrieve contacts. Contact access may require additional permissions or may not be supported on this device."

        # Process the output based on its format
        contacts = []

        if "|" in output:  # SQLite output format
            lines = output.strip().split("\n")
            for line in lines:
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        # Only add if name and number are not empty
                        name = parts[0].strip()
                        number = parts[1].strip()
                        if name and number:
                            contact = {"name": name, "phone": number}
                            contacts.append(contact)
        else:  # Content provider output format
            rows = output.split("Row: ")
            # Skip empty first element if it exists
            if rows and not rows[0].strip():
                rows = rows[1:]

            for row in rows:
                if not row.strip():
                    continue

                contact = {}
                parts = row.split(", ")

                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        # Only add non-NULL values
                        if value and value != "NULL" and value != "null":
                            contact[key.strip()] = value.strip()

                # Normalize fields before adding
                if contact:
                    if "display_name" in contact and "name" not in contact:
                        contact["name"] = contact["display_name"]
                    
                    # Standardize phone number field
                    if "number" in contact:
                        contact["phone"] = contact["number"]
                    elif "data1" in contact and contact.get("mimetype", "").endswith("phone_v2"):
                        contact["phone"] = contact["data1"]
                        
                    contacts.append(contact)

        if not contacts:
            return "No contacts found or unable to parse contacts data."

        # Return filtered contacts directly
        return json.dumps(contacts, indent=2)
    except Exception as e:
        return f"Error retrieving contacts: {str(e)}"
