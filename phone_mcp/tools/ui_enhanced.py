"""Enhanced UI inspection and automation functions for Phone MCP.
This module extends basic UI functionality with advanced features for UI testing and automation.
"""

import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from .ui import dump_ui, tap_element, find_element_by_text, find_element_by_id
from .interactions import swipe_screen, press_key, input_text
from ..core import run_command, check_device_connection


async def find_element_by_content_desc(
    content_desc: str, partial_match: bool = False
) -> str:
    """Find UI element by content description.

    Args:
        content_desc (str): Content description to search for
        partial_match (bool): If True, find elements containing the description

    Returns:
        str: JSON string with matching elements or error message
    """
    # Get the full UI dump
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_desc = element.get("content-desc", "")

            if (
                partial_match and content_desc in element_desc
            ) or element_desc == content_desc:
                matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": content_desc,
                "partial_match": partial_match,
                "count": len(matches),
                "elements": matches,
            },
            indent=2,
        )
    except json.JSONDecodeError:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to process UI data",
                "raw_response": dump_response[:500],
            },
            indent=2,
        )


async def find_element_by_class(
    class_name: str, package_name: Optional[str] = None
) -> str:
    """Find UI element by class name.

    Args:
        class_name (str): Class name to search for (e.g., "android.widget.Button")
        package_name (str, optional): Package name to limit search to

    Returns:
        str: JSON string with matching elements or error message
    """
    # Get the full UI dump
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_class = element.get("class", "")
            element_package = element.get("package", "")

            if class_name in element_class and (
                package_name is None or package_name in element_package
            ):
                matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": class_name,
                "package_filter": package_name,
                "count": len(matches),
                "elements": matches,
            },
            indent=2,
        )
    except json.JSONDecodeError:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to process UI data",
                "raw_response": dump_response[:500],
            },
            indent=2,
        )


async def find_clickable_elements() -> str:
    """Find all clickable elements on the screen.

    Returns:
        str: JSON string with clickable elements or error message
    """
    # Get the full UI dump
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response

        # Find clickable elements
        matches = []
        for element in dump_data.get("elements", []):
            if element.get("clickable", False):
                matches.append(element)

        return json.dumps(
            {"status": "success", "count": len(matches), "elements": matches}, indent=2
        )
    except json.JSONDecodeError:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to process UI data",
                "raw_response": dump_response[:500],
            },
            indent=2,
        )


async def wait_for_element(
    find_method: str,
    search_value: str,
    timeout_seconds: int = 30,
    interval_seconds: float = 1.0,
    **kwargs,
) -> str:
    """Wait for an element to appear on the screen.

    Args:
        find_method (str): Method to use: "text", "id", "content_desc", "class", "clickable"
        search_value (str): Value to search for
        timeout_seconds (int): Maximum time to wait in seconds
        interval_seconds (float): Time between checks in seconds
        **kwargs: Additional arguments for the find method

    Returns:
        str: JSON string with element if found, or error message
    """
    # Map of find methods to their functions
    find_methods = {
        "text": find_element_by_text,
        "id": find_element_by_id,
        "content_desc": find_element_by_content_desc,
        "class": find_element_by_class,
        "clickable": find_clickable_elements,
    }

    # Validate find method
    if find_method not in find_methods:
        return json.dumps(
            {
                "status": "error",
                "message": f"Invalid find method: {find_method}. Valid methods are: {', '.join(find_methods.keys())}",
            },
            indent=2,
        )

    # Get the appropriate find function directly
    find_func = find_methods[find_method]

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        # Call the appropriate find function
        try:
            if find_method == "clickable":
                response = await find_func()
            elif find_method == "text":
                response = await find_func(search_value, kwargs.get("partial", True))
            else:
                response = await find_func(search_value, **kwargs)
                
            response_data = json.loads(response)

            if (
                response_data.get("status") == "success"
                and response_data.get("count", 0) > 0
            ):
                # Element found
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Element found after {time.time() - start_time:.1f} seconds",
                        "element": response_data.get("elements", [])[0],
                        "all_elements": response_data.get("elements", []),
                    },
                    indent=2,
                )
        except Exception as e:
            # If error occurs, log and continue waiting
            print(f"Error while waiting for element: {str(e)}")

        # Wait before next check
        await asyncio.sleep(interval_seconds)

    # Timeout reached
    return json.dumps(
        {
            "status": "error",
            "message": f"Element not found within {timeout_seconds} seconds",
            "find_method": find_method,
            "search_value": search_value,
        },
        indent=2,
    )


async def wait_until_element_gone(
    find_method: str,
    search_value: str,
    timeout_seconds: int = 30,
    interval_seconds: float = 1.0,
    **kwargs,
) -> str:
    """Wait for an element to disappear from the screen.

    Args:
        find_method (str): Method to use: "text", "id", "content_desc", "class"
        search_value (str): Value to search for
        timeout_seconds (int): Maximum time to wait in seconds
        interval_seconds (float): Time between checks in seconds
        **kwargs: Additional arguments for the find method

    Returns:
        str: JSON string with success message if element disappeared, or error message
    """
    # Map of find methods to their functions
    find_methods = {
        "text": find_element_by_text,
        "id": find_element_by_id,
        "content_desc": find_element_by_content_desc,
        "class": find_element_by_class,
    }

    # Validate find method
    if find_method not in find_methods:
        return json.dumps(
            {
                "status": "error",
                "message": f"Invalid find method: {find_method}. Valid methods are: {', '.join(find_methods.keys())}",
            },
            indent=2,
        )

    # Get the appropriate find function directly
    find_func = find_methods[find_method]

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        # Call the appropriate find function
        try:
            if find_method == "text":
                response = await find_func(search_value, kwargs.get("partial", True))
            else:
                response = await find_func(search_value, **kwargs)
                
            response_data = json.loads(response)

            if (
                response_data.get("status") == "success"
                and response_data.get("count", 0) == 0
            ):
                # Element is gone
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Element disappeared after {time.time() - start_time:.1f} seconds",
                    },
                    indent=2,
                )
        except Exception as e:
            # Log error but treat as if element is still present
            print(f"Error while checking if element is gone: {str(e)}")

        # Wait before next check
        await asyncio.sleep(interval_seconds)

    # Timeout reached
    return json.dumps(
        {
            "status": "error",
            "message": f"Element still present after {timeout_seconds} seconds",
            "find_method": find_method,
            "search_value": search_value,
        },
        indent=2,
    )


async def scroll_to_element(
    find_method: str,
    search_value: str,
    direction: str = "down",
    max_swipes: int = 5,
    swipe_duration_ms: int = 500,
    **kwargs,
) -> str:
    """Scroll the screen until an element is found.

    Args:
        find_method (str): Method to use: "text", "id", "content_desc", "class"
        search_value (str): Value to search for
        direction (str): Direction to scroll: "up", "down", "left", "right"
        max_swipes (int): Maximum number of swipes to perform
        swipe_duration_ms (int): Duration of each swipe in milliseconds
        **kwargs: Additional arguments for the find method

    Returns:
        str: JSON string with element if found, or error message
    """
    # Map of find methods to their functions
    find_methods = {
        "text": find_element_by_text,  # Using direct function reference
        "id": find_element_by_id,      # Using direct function reference
        "content_desc": find_element_by_content_desc,
        "class": find_element_by_class,
    }

    # Validate find method
    if find_method not in find_methods:
        return json.dumps(
            {
                "status": "error",
                "message": f"Invalid find method: {find_method}. Valid methods are: {', '.join(find_methods.keys())}",
            },
            indent=2,
        )

    # Get the appropriate find function
    find_func = find_methods[find_method]

    # Get screen size for swipe calculations
    screen_size_response = await run_command("adb shell wm size")
    screen_width, screen_height = 1080, 1920  # Default values

    if screen_size_response[0]:  # If command was successful
        match = re.search(r"(\d+)x(\d+)", screen_size_response[1])
        if match:
            screen_width, screen_height = int(match.group(1)), int(match.group(2))

    # Define swipe coordinates based on direction
    swipe_coords = {
        "up": (
            screen_width // 2,
            screen_height // 4,
            screen_width // 2,
            screen_height * 3 // 4,
        ),
        "down": (
            screen_width // 2,
            screen_height * 3 // 4,
            screen_width // 2,
            screen_height // 4,
        ),
        "left": (
            screen_width // 4,
            screen_height // 2,
            screen_width * 3 // 4,
            screen_height // 2,
        ),
        "right": (
            screen_width * 3 // 4,
            screen_height // 2,
            screen_width // 4,
            screen_height // 2,
        ),
    }

    if direction not in swipe_coords:
        return json.dumps(
            {
                "status": "error",
                "message": f"Invalid direction: {direction}. Valid directions are: {', '.join(swipe_coords.keys())}",
            },
            indent=2,
        )

    # First check if element is already visible
    try:
        if find_method == "text":
            response = await find_func(search_value, kwargs.get("partial", True))
        else:
            response = await find_func(search_value, **kwargs)

        response_data = json.loads(response)

        if (
            response_data.get("status") == "success"
            and response_data.get("count", 0) > 0
        ):
            # Element already found
            return json.dumps(
                {
                    "status": "success",
                    "message": "Element already visible, no scrolling needed",
                    "element": response_data.get("elements", [])[0],
                },
                indent=2,
            )
    except Exception as e:
        # Log the error but continue with scrolling
        print(f"Error checking if element is already visible: {str(e)}")

    # Element not found, start scrolling
    for i in range(max_swipes):
        # Perform the swipe
        x1, y1, x2, y2 = swipe_coords[direction]
        swipe_response = await swipe_screen(x1, y1, x2, y2, swipe_duration_ms)

        # Wait a moment for the screen to settle
        await asyncio.sleep(0.5)

        # Check if element is now visible
        try:
            if find_method == "text":
                response = await find_func(search_value, kwargs.get("partial", True))
            else:
                response = await find_func(search_value, **kwargs)

            response_data = json.loads(response)

            if (
                response_data.get("status") == "success"
                and response_data.get("count", 0) > 0
            ):
                # Element found
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Element found after {i+1} swipes",
                        "element": response_data.get("elements", [])[0],
                        "swipes_performed": i + 1,
                    },
                    indent=2,
                )
        except Exception as e:
            # Log the error but continue with scrolling
            print(f"Error checking if element is visible after swipe {i+1}: {str(e)}")

    # Element not found after maximum swipes
    return json.dumps(
        {
            "status": "error",
            "message": f"Element not found after {max_swipes} swipes",
            "find_method": find_method,
            "search_value": search_value,
            "direction": direction,
        },
        indent=2,
    )


async def element_exists(find_method: str, search_value: str, **kwargs) -> bool:
    """Check if an element exists on the screen.

    Args:
        find_method (str): Method to use: "text", "id", "content_desc", "class"
        search_value (str): Value to search for
        **kwargs: Additional arguments for the find method

    Returns:
        bool: True if element exists, False otherwise
    """
    # Map of find methods to their functions
    find_methods = {
        "text": find_element_by_text,
        "id": find_element_by_id,
        "content_desc": find_element_by_content_desc,
        "class": find_element_by_class,
    }

    # Validate find method
    if find_method not in find_methods:
        return False

    # Get the appropriate find function directly
    find_func = find_methods[find_method]

    # Call the appropriate find function
    try:
        if find_method == "text":
            response = await find_func(search_value, kwargs.get("partial", True))
        else:
            response = await find_func(search_value, **kwargs)
            
        response_data = json.loads(response)
        return (
            response_data.get("status") == "success"
            and response_data.get("count", 0) > 0
        )
    except Exception as e:
        print(f"Error checking if element exists: {str(e)}")
        return False


async def perform_action_chain(actions: List[Dict[str, Any]]) -> str:
    """Perform a chain of UI actions in sequence.

    Args:
        actions (List[Dict]): List of action dictionaries, each with:
            - action_type: "tap", "swipe", "wait", "input", "key", "find", "scroll"
            - params: Dictionary of parameters for the action

    Returns:
        str: JSON string with results of each action
    """
    results = []

    for i, action in enumerate(actions):
        action_type = action.get("action_type", "").lower()
        params = action.get("params", {})

        try:
            # Handle different action types
            if action_type == "tap":
                if "element" in params:
                    # Tap an element
                    result = await tap_element(json.dumps(params["element"]))
                else:
                    # Tap coordinates
                    x = params.get("x", 0)
                    y = params.get("y", 0)
                    from .interactions import tap_screen

                    result = await tap_screen(x, y)

                results.append(
                    {
                        "step": i + 1,
                        "action": "tap",
                        "status": "success" if "success" in result.lower() else "error",
                        "message": result,
                    }
                )

            elif action_type == "swipe":
                # Swipe on the screen
                x1 = params.get("x1", 0)
                y1 = params.get("y1", 0)
                x2 = params.get("x2", 0)
                y2 = params.get("y2", 0)
                duration = params.get("duration_ms", 300)

                result = await swipe_screen(x1, y1, x2, y2, duration)

                results.append(
                    {
                        "step": i + 1,
                        "action": "swipe",
                        "status": "success" if "success" in result.lower() else "error",
                        "message": result,
                    }
                )

            elif action_type == "wait":
                # Wait for a specified time
                seconds = params.get("seconds", 1.0)
                await asyncio.sleep(seconds)

                results.append(
                    {
                        "step": i + 1,
                        "action": "wait",
                        "status": "success",
                        "message": f"Waited for {seconds} seconds",
                    }
                )

            elif action_type == "input":
                # Input text
                text = params.get("text", "")

                result = await input_text(text)

                results.append(
                    {
                        "step": i + 1,
                        "action": "input",
                        "status": "success" if "success" in result.lower() else "error",
                        "message": result,
                    }
                )

            elif action_type == "key":
                # Press a key
                key = params.get("key", "")

                result = await press_key(key)

                results.append(
                    {
                        "step": i + 1,
                        "action": "key",
                        "status": "success" if "success" in result.lower() else "error",
                        "message": result,
                    }
                )

            elif action_type == "find":
                # Find an element
                find_method = params.get("method", "text")
                search_value = params.get("value", "")
                additional_params = params.get("additional_params", {})

                find_func_name = f"find_element_by_{find_method}"
                if find_func_name not in globals():
                    results.append(
                        {
                            "step": i + 1,
                            "action": "find",
                            "status": "error",
                            "message": f"Invalid find method: {find_method}",
                        }
                    )
                    continue

                find_func = globals()[find_func_name]
                result = await find_func(search_value, **additional_params)

                results.append(
                    {
                        "step": i + 1,
                        "action": "find",
                        "status": "success",
                        "message": f"Find operation completed",
                        "result": (
                            json.loads(result) if isinstance(result, str) else result
                        ),
                    }
                )

            elif action_type == "scroll":
                # Scroll to find an element
                find_method = params.get("method", "text")
                search_value = params.get("value", "")
                direction = params.get("direction", "down")
                max_swipes = params.get("max_swipes", 5)
                additional_params = params.get("additional_params", {})

                result = await scroll_to_element(
                    find_method,
                    search_value,
                    direction,
                    max_swipes,
                    **additional_params,
                )

                results.append(
                    {
                        "step": i + 1,
                        "action": "scroll",
                        "status": "success" if "success" in result else "error",
                        "message": (
                            json.loads(result)
                            if isinstance(result, str) and "{" in result
                            else result
                        ),
                    }
                )

            else:
                # Unknown action type
                results.append(
                    {
                        "step": i + 1,
                        "action": action_type,
                        "status": "error",
                        "message": f"Unknown action type: {action_type}",
                    }
                )

        except Exception as e:
            # Handle any exceptions during action execution
            results.append(
                {
                    "step": i + 1,
                    "action": action_type,
                    "status": "error",
                    "message": f"Error executing action: {str(e)}",
                }
            )

    return json.dumps(
        {"status": "complete", "actions_performed": len(results), "results": results},
        indent=2,
    )
