"""UI monitoring and observation functions for Phone MCP.
This module provides functions to monitor UI changes and trigger actions.
"""

import asyncio
import json
import time
import re
import hashlib
from typing import List, Dict, Any, Optional, Callable, Union
from .ui import dump_ui
from .ui_enhanced import element_exists, perform_action_chain
from ..core import run_command, check_device_connection


class UISnapshot:
    """Class to store and compare UI snapshots."""

    def __init__(self, ui_data: Dict[str, Any]):
        """Initialize with UI data."""
        self.timestamp = time.time()
        self.data = ui_data
        self.elements_count = len(ui_data.get("elements", []))
        self.elements_hash = self._generate_elements_hash(ui_data.get("elements", []))

    def _generate_elements_hash(self, elements: List[Dict[str, Any]]) -> str:
        """Generate a hash of the UI elements to detect changes."""
        # Create a simpler representation of elements for hashing
        elements_repr = []
        for elem in elements:
            # Only include key fields that would indicate a UI change
            elem_repr = {
                "class": elem.get("class", ""),
                "resource-id": elem.get("resource-id", ""),
                "text": elem.get("text", ""),
                "bounds": elem.get("bounds", {}),
            }
            elements_repr.append(str(elem_repr))

        # Sort to ensure consistent hashing regardless of element order
        elements_repr.sort()

        # Join and hash
        hash_input = "||".join(elements_repr)
        return hashlib.md5(hash_input.encode()).hexdigest()

    def differs_from(self, other: "UISnapshot") -> bool:
        """Check if this snapshot differs significantly from another."""
        # Simple check: different number of elements or different hash
        return (
            self.elements_count != other.elements_count
            or self.elements_hash != other.elements_hash
        )

    def get_added_elements(self, previous: "UISnapshot") -> List[Dict[str, Any]]:
        """Get elements that appear in this snapshot but not in the previous one."""
        if not previous:
            return []

        current_elements = self.data.get("elements", [])
        previous_elements = previous.data.get("elements", [])

        # Create a unique identifier for each element
        def element_id(elem):
            return f"{elem.get('class', '')}:{elem.get('resource-id', '')}:{elem.get('text', '')}:{elem.get('bounds', {})}"

        previous_ids = {element_id(elem) for elem in previous_elements}

        # Find elements in current that weren't in previous
        added = []
        for elem in current_elements:
            if element_id(elem) not in previous_ids:
                added.append(elem)

        return added

    def get_removed_elements(self, previous: "UISnapshot") -> List[Dict[str, Any]]:
        """Get elements that appear in the previous snapshot but not in this one."""
        if not previous:
            return []

        # Just reverse the comparison
        current_elements = self.data.get("elements", [])
        previous_elements = previous.data.get("elements", [])

        def element_id(elem):
            return f"{elem.get('class', '')}:{elem.get('resource-id', '')}:{elem.get('text', '')}:{elem.get('bounds', {})}"

        current_ids = {element_id(elem) for elem in current_elements}

        # Find elements in previous that aren't in current
        removed = []
        for elem in previous_elements:
            if element_id(elem) not in current_ids:
                removed.append(elem)

        return removed


async def take_ui_snapshot() -> Optional[UISnapshot]:
    """Take a snapshot of the current UI."""
    response = await dump_ui()

    try:
        data = json.loads(response)
        if data.get("status") == "success":
            return UISnapshot(data)
    except:
        pass

    return None


async def monitor_ui_changes(
    interval_seconds: float = 1.0,
    max_duration_seconds: float = 300.0,
    on_change_callback: Optional[Callable[[UISnapshot, UISnapshot], None]] = None,
    stop_condition: Optional[Callable[[UISnapshot], bool]] = None,
) -> str:
    """Monitor the UI for changes.

    Args:
        interval_seconds (float): Time between UI checks
        max_duration_seconds (float): Maximum monitoring time
        on_change_callback (callable): Function to call when UI changes
        stop_condition (callable): Function that returns True when monitoring should stop

    Returns:
        str: JSON string with monitoring results
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return json.dumps(
            {
                "status": "error",
                "message": "Device not connected",
                "details": connection_status,
            },
            indent=2,
        )

    start_time = time.time()
    previous_snapshot = None
    change_count = 0
    changes = []

    # Take initial snapshot
    current_snapshot = await take_ui_snapshot()
    if not current_snapshot:
        return json.dumps(
            {"status": "error", "message": "Failed to take initial UI snapshot"},
            indent=2,
        )

    previous_snapshot = current_snapshot

    # Monitor loop
    while time.time() - start_time < max_duration_seconds:
        # Wait for the specified interval
        await asyncio.sleep(interval_seconds)

        # Take a new snapshot
        current_snapshot = await take_ui_snapshot()
        if not current_snapshot:
            continue

        # Check if the UI has changed
        if current_snapshot.differs_from(previous_snapshot):
            change_count += 1

            # Get added and removed elements
            added = current_snapshot.get_added_elements(previous_snapshot)
            removed = current_snapshot.get_removed_elements(previous_snapshot)

            change_info = {
                "timestamp": time.time(),
                "elapsed_seconds": time.time() - start_time,
                "elements_before": previous_snapshot.elements_count,
                "elements_after": current_snapshot.elements_count,
                "elements_added": len(added),
                "elements_removed": len(removed),
                "added_elements": added[:5],  # Limit to first 5 for brevity
                "removed_elements": removed[:5],  # Limit to first 5 for brevity
            }

            changes.append(change_info)

            # Call the change callback if provided
            if on_change_callback:
                try:
                    on_change_callback(previous_snapshot, current_snapshot)
                except Exception as e:
                    changes[-1]["callback_error"] = str(e)

            # Update the previous snapshot
            previous_snapshot = current_snapshot

        # Check stop condition
        if stop_condition and stop_condition(current_snapshot):
            break

    # Prepare final report
    end_time = time.time()
    duration = end_time - start_time

    return json.dumps(
        {
            "status": "complete",
            "duration_seconds": duration,
            "changes_detected": change_count,
            "changes": changes,
        },
        indent=2,
    )


async def wait_for_ui_condition(
    condition_func: Callable[[Dict[str, Any]], bool],
    timeout_seconds: int = 30,
    interval_seconds: float = 0.5,
    description: str = "custom condition",
) -> str:
    """Wait for a custom UI condition to be met.

    Args:
        condition_func (callable): Function that takes UI data and returns True when condition is met
        timeout_seconds (int): Maximum time to wait
        interval_seconds (float): Time between checks
        description (str): Description of the condition for reporting

    Returns:
        str: JSON string with success or timeout message
    """
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        # Get current UI
        response = await dump_ui()

        try:
            data = json.loads(response)

            if data.get("status") == "success":
                # Check condition
                if condition_func(data):
                    return json.dumps(
                        {
                            "status": "success",
                            "message": f"Condition '{description}' met after {time.time() - start_time:.1f} seconds",
                            "elapsed_seconds": time.time() - start_time,
                        },
                        indent=2,
                    )
        except:
            # Continue if there was an error processing the UI
            pass

        # Wait before next check
        await asyncio.sleep(interval_seconds)

    # Timeout reached
    return json.dumps(
        {
            "status": "error",
            "message": f"Condition '{description}' not met within {timeout_seconds} seconds",
            "timeout_seconds": timeout_seconds,
        },
        indent=2,
    )


async def create_ui_trigger(
    trigger_condition: Dict[str, Any],
    actions: List[Dict[str, Any]],
    max_duration_seconds: float = 300.0,
    check_interval_seconds: float = 1.0,
) -> str:
    """Create a trigger that performs actions when a UI condition is met.

    Args:
        trigger_condition (dict): Condition spec with:
            - type: "element_appears", "element_disappears", "text_appears", etc.
            - params: Dict with condition parameters
        actions (list): List of actions to perform when triggered
        max_duration_seconds (float): Maximum monitoring time
        check_interval_seconds (float): Time between UI checks

    Returns:
        str: JSON string with trigger results
    """
    condition_type = trigger_condition.get("type", "")
    condition_params = trigger_condition.get("params", {})

    # Define the condition check function based on the condition type
    async def check_condition(snapshot: UISnapshot) -> bool:
        if condition_type == "element_appears":
            # Check if an element matching criteria appears
            find_method = condition_params.get("method", "text")
            search_value = condition_params.get("value", "")
            additional_params = condition_params.get("additional_params", {})

            return await element_exists(find_method, search_value, **additional_params)

        elif condition_type == "element_disappears":
            # Check if an element matching criteria disappears
            find_method = condition_params.get("method", "text")
            search_value = condition_params.get("value", "")
            additional_params = condition_params.get("additional_params", {})

            return not await element_exists(
                find_method, search_value, **additional_params
            )

        elif condition_type == "ui_stable":
            # Check if UI has been stable (unchanged) for some time
            stable_duration = condition_params.get("stable_seconds", 2.0)

            # This requires keeping track of the last change time
            # For simplicity, we'll consider it met if the current snapshot
            # doesn't differ from the last one
            return not snapshot.differs_from(last_snapshot)

        elif condition_type == "package_in_foreground":
            # Check if a specific package is in the foreground
            package_name = condition_params.get("package_name", "")

            # Check the current window
            cmd = "adb shell dumpsys window windows | grep -E 'mCurrentFocus'"
            success, output = await run_command(cmd)

            if success and package_name in output:
                return True

            return False

        else:
            # Unknown condition type
            return False

    # Set up monitoring
    start_time = time.time()
    triggered = False
    trigger_time = None
    last_snapshot = await take_ui_snapshot()

    if not last_snapshot:
        return json.dumps(
            {"status": "error", "message": "Failed to take initial UI snapshot"},
            indent=2,
        )

    # Monitor loop
    while time.time() - start_time < max_duration_seconds and not triggered:
        # Wait for the check interval
        await asyncio.sleep(check_interval_seconds)

        # Take a new snapshot
        current_snapshot = await take_ui_snapshot()
        if not current_snapshot:
            continue

        # Check condition
        if await check_condition(current_snapshot):
            triggered = True
            trigger_time = time.time()
            break

        # Update last snapshot
        last_snapshot = current_snapshot

    # If triggered, perform the actions
    action_results = None
    if triggered:
        action_results = await perform_action_chain(actions)
        try:
            action_results = json.loads(action_results)
        except:
            pass

    # Prepare final report
    end_time = time.time()
    duration = end_time - start_time

    return json.dumps(
        {
            "status": "complete",
            "triggered": triggered,
            "duration_seconds": duration,
            "trigger_elapsed_seconds": (
                trigger_time - start_time if trigger_time else None
            ),
            "condition": {"type": condition_type, "params": condition_params},
            "action_results": action_results,
        },
        indent=2,
    )


async def compare_ui_states(snapshot1: str, snapshot2: str) -> str:
    """Compare two UI snapshots to identify differences.

    Args:
        snapshot1 (str): JSON string of first UI snapshot
        snapshot2 (str): JSON string of second UI snapshot

    Returns:
        str: JSON string with comparison results
    """
    try:
        # Parse the snapshots
        data1 = json.loads(snapshot1)
        data2 = json.loads(snapshot2)

        # Create UISnapshot objects
        snap1 = UISnapshot(data1)
        snap2 = UISnapshot(data2)

        # Get differences
        added = snap2.get_added_elements(snap1)
        removed = snap1.get_removed_elements(snap2)

        # Find modified elements (same ID but different properties)
        def element_basic_id(elem):
            return f"{elem.get('resource-id', '')}:{elem.get('class', '')}"

        modified = []

        # Create dictionaries for faster lookup
        snap1_elements = {element_basic_id(e): e for e in data1.get("elements", [])}
        snap2_elements = {element_basic_id(e): e for e in data2.get("elements", [])}

        # Find elements with the same basic ID but different properties
        common_ids = set(snap1_elements.keys()) & set(snap2_elements.keys())

        for elem_id in common_ids:
            elem1 = snap1_elements[elem_id]
            elem2 = snap2_elements[elem_id]

            # Check differences in text or clickable state
            differences = {}
            for key in ["text", "content-desc", "clickable", "enabled", "checked"]:
                if elem1.get(key) != elem2.get(key):
                    differences[key] = {
                        "before": elem1.get(key),
                        "after": elem2.get(key),
                    }

            if differences:
                modified.append({"element": elem2, "changes": differences})

        return json.dumps(
            {
                "status": "success",
                "elements_added": len(added),
                "elements_removed": len(removed),
                "elements_modified": len(modified),
                "added": added,
                "removed": removed,
                "modified": modified,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {"status": "error", "message": f"Failed to compare UI states: {str(e)}"},
            indent=2,
        )


async def mcp_monitor_ui_changes(
    interval_seconds: float = 1.0,
    max_duration_seconds: float = 60.0,
    watch_for: str = "any_change",
    target_text: str = "",
    target_id: str = "",
    target_class: str = "",
    target_content_desc: str = ""
) -> str:
    """Monitor the UI for changes with MCP compatible parameters.
    
    This is a simplified version of monitor_ui_changes that doesn't use callback functions,
    making it compatible with MCP's JSON schema requirements.

    Args:
        interval_seconds (float): Time between UI checks (seconds)
        max_duration_seconds (float): Maximum monitoring time (seconds)
        watch_for (str): What to watch for - "any_change", "text_appears", "text_disappears", 
                        "id_appears", "id_disappears", "class_appears", "content_desc_appears"
        target_text (str): Text to watch for (when watch_for includes "text")
        target_id (str): ID to watch for (when watch_for includes "id")
        target_class (str): Class to watch for (when watch_for includes "class")
        target_content_desc (str): Content description to watch for (when watch_for includes "content_desc")

    Returns:
        str: JSON string with monitoring results
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        return json.dumps(
            {
                "status": "error",
                "message": "Device not connected",
                "details": connection_status,
            },
            indent=2,
        )

    start_time = time.time()
    previous_snapshot = None
    change_count = 0
    changes = []
    condition_met = False
    condition_met_time = None

    # Take initial snapshot
    try:
        initial_dump = await dump_ui()
        initial_data = json.loads(initial_dump)
        if initial_data.get("status") != "success":
            return json.dumps(
                {"status": "error", "message": "Failed to take initial UI snapshot"},
                indent=2,
            )
        
        previous_snapshot = UISnapshot(initial_data)
    except Exception as e:
        return json.dumps(
            {"status": "error", "message": f"Error initializing UI monitoring: {str(e)}"},
            indent=2,
        )

    # Helper function to check for specific conditions
    async def check_condition(current_data: Dict[str, Any]) -> bool:
        if watch_for == "any_change":
            return True
        
        elements = current_data.get("elements", [])
        
        if watch_for == "text_appears":
            for elem in elements:
                if target_text in elem.get("text", ""):
                    return True
            return False
        
        elif watch_for == "text_disappears":
            for elem in elements:
                if target_text in elem.get("text", ""):
                    return False
            return True
            
        elif watch_for == "id_appears":
            for elem in elements:
                if target_id in elem.get("resource-id", ""):
                    return True
            return False
            
        elif watch_for == "id_disappears":
            for elem in elements:
                if target_id in elem.get("resource-id", ""):
                    return False
            return True
            
        elif watch_for == "class_appears":
            for elem in elements:
                if target_class in elem.get("class", ""):
                    return True
            return False
            
        elif watch_for == "content_desc_appears":
            for elem in elements:
                if target_content_desc in elem.get("content-desc", ""):
                    return True
            return False
            
        return False

    # Monitor loop
    while time.time() - start_time < max_duration_seconds and not condition_met:
        # Wait for the specified interval
        await asyncio.sleep(interval_seconds)

        # Take a new snapshot
        try:
            current_dump = await dump_ui()
            current_data = json.loads(current_dump)
            if current_data.get("status") != "success":
                continue
                
            current_snapshot = UISnapshot(current_data)
        except Exception:
            continue

        # Check if the UI has changed
        if previous_snapshot and current_snapshot.differs_from(previous_snapshot):
            change_count += 1
            change_time = time.time()

            # Get added and removed elements
            added = current_snapshot.get_added_elements(previous_snapshot)
            removed = previous_snapshot.get_removed_elements(current_snapshot)

            change_info = {
                "timestamp": change_time,
                "elapsed_seconds": change_time - start_time,
                "elements_before": previous_snapshot.elements_count,
                "elements_after": current_snapshot.elements_count,
                "elements_added": len(added),
                "elements_removed": len(removed),
                "added_elements": added[:5],  # Limit to first 5 for brevity
                "removed_elements": removed[:5],  # Limit to first 5 for brevity
            }

            changes.append(change_info)
            
            # Check if the specific condition is met
            if await check_condition(current_data):
                condition_met = True
                condition_met_time = change_time

            # Update the previous snapshot
            previous_snapshot = current_snapshot

    # Prepare final report
    end_time = time.time()
    duration = end_time - start_time

    return json.dumps(
        {
            "status": "complete",
            "condition_met": condition_met,
            "condition_type": watch_for,
            "duration_seconds": duration,
            "condition_met_at": condition_met_time - start_time if condition_met_time else None,
            "changes_detected": change_count,
            "changes": changes,
        },
        indent=2,
    )
