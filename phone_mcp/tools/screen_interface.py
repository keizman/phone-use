# -*- coding: utf-8 -*-
"""
Screen Interface Module - Provides functions for screen analysis and interaction.
Integrates multiple tools for UI analysis, element search, and device interaction.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union

# Import base functionality modules
from .ui import dump_ui, find_element_by_text, find_element_by_id
from .ui_enhanced import (
    find_element_by_content_desc, find_element_by_class, 
    find_clickable_elements, wait_for_element, scroll_to_element
)
from .interactions import tap_screen, swipe_screen, press_key, input_text, get_screen_size
from .media import take_screenshot
from ..core import run_command

logger = logging.getLogger("phone_mcp")

class UIElement:
    """Class representing a UI element with its properties and interaction methods
    
    This class handles parsing and storing UI element attributes from device UI dumps,
    calculating element coordinates, and providing methods to interact with the element.
    
    Attributes:
        data (dict): Raw element data dictionary
        text (str): Element text content
        resource_id (str): Element resource ID for identification
        class_name (str): Element class/type
        content_desc (str): Element content description (accessibility text)
        clickable (bool): Whether the element is marked as clickable
        bounds (str): Element boundary coordinates string in format "[x1,y1][x2,y2]"
        x1 (int): Left coordinate (if bounds successfully parsed)
        y1 (int): Top coordinate (if bounds successfully parsed)
        x2 (int): Right coordinate (if bounds successfully parsed)
        y2 (int): Bottom coordinate (if bounds successfully parsed)
        center_x (int): X coordinate of element center (if bounds successfully parsed)
        center_y (int): Y coordinate of element center (if bounds successfully parsed)
    """
    
    def __init__(self, element_data: Dict[str, Any]):
        """Initialize UI element
        
        Args:
            element_data (Dict[str, Any]): Dictionary containing element properties from UI dump
            
        Notes:
            Coordinate parsing failures are logged but don't raise exceptions.
            Check for existence of center_x/center_y attributes before attempting coordinate-based operations.
        """
        self.data = element_data or {}  # Ensure we have a dictionary even if None is passed
        self.text = self.data.get("text", "")
        self.resource_id = self.data.get("resource_id", "")
        self.class_name = self.data.get("class_name", "")
        self.content_desc = self.data.get("content_desc", "")
        self.clickable = self.data.get("clickable", False)
        self.bounds = self.data.get("bounds", "")
        
        # Parse boundaries to get coordinates
        if self.bounds and isinstance(self.bounds, str):
            try:
                coords = self.bounds.replace("[", "").replace("]", "").split(",")
                if len(coords) == 4:
                    self.x1 = int(coords[0])
                    self.y1 = int(coords[1])
                    self.x2 = int(coords[2])
                    self.y2 = int(coords[3])
                    self.center_x = (self.x1 + self.x2) // 2
                    self.center_y = (self.y1 + self.y2) // 2
            except Exception as e:
                logger.warning(f"Failed to parse element boundaries: {self.bounds}, error: {str(e)}")
        elif self.bounds and isinstance(self.bounds, dict):
            # If bounds is in dictionary format, try to extract coordinates from it
            try:
                if all(k in self.bounds for k in ["left", "top", "right", "bottom"]):
                    self.x1 = int(self.bounds.get("left", 0))
                    self.y1 = int(self.bounds.get("top", 0))
                    self.x2 = int(self.bounds.get("right", 0))
                    self.y2 = int(self.bounds.get("bottom", 0))
                    self.center_x = (self.x1 + self.x2) // 2
                    self.center_y = (self.y1 + self.y2) // 2
            except Exception as e:
                logger.warning(f"Failed to parse element boundaries from dictionary: {self.bounds}, error: {str(e)}")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert UI element to dictionary format for JSON serialization
        
        Returns:
            Dictionary containing all element attributes
        """
        result = {
            "text": self.text,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "content_desc": self.content_desc,
            "clickable": self.clickable,
            "bounds": self.bounds,
        }
        
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            result["center_x"] = self.center_x
            result["center_y"] = self.center_y
            
        return result
        
    async def tap(self) -> str:
        """Tap the center of this element
        
        Attempts to tap the center point of the element. This requires that the element's
        bounds have been successfully parsed during initialization.
        
        Returns:
            str: JSON string with operation result
        """
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            return await tap_screen(self.center_x, self.center_y)
        return json.dumps({"status": "error", "message": "Element does not have valid coordinates"})


async def get_screen_info(include_screenshot: bool = True, max_elements: int = 100) -> str:
    """Get detailed information about the current screen, including UI hierarchy and screenshot
    
    This function obtains comprehensive screen information by retrieving the UI hierarchy,
    taking a screenshot, and parsing all visible elements.
    
    Args:
        include_screenshot (bool, optional): Whether to include a base64-encoded screenshot. Defaults to True.
        max_elements (int, optional): Maximum number of elements to include in the result. Defaults to 100.
    
    Returns:
        str: JSON string containing screen information:
            {
                "status": "success" or "error",
                "message": "Success/Error message",
                "screen_size": {"width": int, "height": int},
                "all_elements_count": int,
                "clickable_elements_count": int,
                "text_elements_count": int,
                "text_elements": [
                    {"text": str, "bounds": str, "center_x": int, "center_y": int, ...}
                ],
                "clickable_elements": [
                    {"text": str, "bounds": str, "center_x": int, "center_y": int, ...}
                ],
                "timestamp": int
            }
    """
    try:
        # Get UI tree
        ui_dump = await dump_ui()
        ui_data = json.loads(ui_dump)
        
        # Get screen size
        size_result = await get_screen_size()
        screen_size = json.loads(size_result)
        
        # Default screen size if not available
        if not screen_size.get("width") or not screen_size.get("height"):
            screen_size = {"width": 1080, "height": 1920}  # Default fallback values
        
        # Get clickable elements
        clickable_result = await find_clickable_elements()
        clickable_data = json.loads(clickable_result)
        clickable_elements = clickable_data.get("elements", []) if clickable_data.get("status") == "success" else []
        
        # Extract text elements and process all elements
        text_elements = []
        all_elements = []
        
        if "elements" in ui_data:
            # Limit elements to prevent overflow
            element_list = ui_data["elements"][:max_elements] if len(ui_data["elements"]) > max_elements else ui_data["elements"]
            
            for elem_data in element_list:
                element = UIElement(elem_data)
                all_elements.append(element.to_dict())
                
                # If element has text, add to text elements list
                if element.text and element.text.strip():
                    text_element = {
                        "text": element.text,
                        "bounds": element.bounds
                    }
                    if hasattr(element, "center_x") and hasattr(element, "center_y"):
                        text_element["center_x"] = element.center_x
                        text_element["center_y"] = element.center_y
                    text_elements.append(text_element)
        
        # Take a screenshot for reference if needed
        screenshot_base64 = ""
        if include_screenshot:
            screenshot_result = await take_screenshot()
            screenshot_data = json.loads(screenshot_result)
            screenshot_base64 = screenshot_data.get("data", "") if screenshot_data.get("status") == "success" else ""
        
        # Build result
        result = {
            "status": "success",
            "message": "Successfully retrieved screen information",
            "screen_size": {
                "width": screen_size.get("width", 0),
                "height": screen_size.get("height", 0),
            },
            "all_elements_count": len(all_elements),
            "clickable_elements_count": len(clickable_elements),
            "text_elements_count": len(text_elements),
            "text_elements": text_elements,
            "clickable_elements": clickable_elements,
            "timestamp": int(time.time()),
        }
        
        # Add screenshot only if included
        if include_screenshot:
            result["screenshot"] = screenshot_base64
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error parsing UI information: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get screen information: {str(e)}"
        })


async def analyze_screen(include_screenshot: bool = False, max_elements: int = 50) -> str:
    """Analyze the current screen and provide structured information about UI elements
    
    This function captures the current screen state and returns a detailed analysis
    of the UI elements, their attributes, and suggests possible interactions.
    
    Args:
        include_screenshot (bool, optional): Whether to include base64-encoded screenshot in the result.
                                          Default is False to reduce response size.
        max_elements (int, optional): Maximum number of UI elements to process.
                                    Default is 50 to limit processing time and response size.
    
    Returns:
        str: JSON string with the analysis result containing:
            {
                "status": "success" or "error",
                "message": "Success/error message",
                "screen_size": {
                    "width": Width of the screen in pixels,
                    "height": Height of the screen in pixels
                },
                "screen_analysis": {
                    "text_elements": {
                        "all": [List of all text elements with coordinates],
                        "by_region": {
                            "top": [Text elements in the top of the screen],
                            "middle": [Text elements in the middle of the screen],
                            "bottom": [Text elements in the bottom of the screen]
                        }
                    },
                    "notable_clickables": [List of important clickable elements],
                    "ui_patterns": {
                        "has_bottom_nav": Whether screen has bottom navigation,
                        "has_top_bar": Whether screen has top app bar,
                        "has_dialog": Whether screen has a dialog showing,
                        "has_list_view": Whether screen has a scrollable list
                    }
                },
                "suggested_actions": [
                    {
                        "action": Action type (e.g., "tap_element"),
                        "element_text": Text of element to interact with,
                        "element_id": ID of element to interact with,
                        "coordinates": [x, y] coordinates for interaction,
                        "confidence": Confidence score (0-100)
                    }
                ]
            }
        
        If include_screenshot is True, the response will also include:
        {
            "screenshot": base64-encoded PNG image of the screen
        }
        
    Examples:
        # Basic screen analysis
        result = await analyze_screen()
        
        # Get screen analysis with screenshot included
        result_with_screenshot = await analyze_screen(include_screenshot=True)
        
        # Get detailed analysis including more elements
        detailed_result = await analyze_screen(max_elements=100)
    """
    try:
        # Get screen info as base for analysis
        screen_info_str = await get_screen_info(include_screenshot=include_screenshot, max_elements=max_elements)
        screen_info = json.loads(screen_info_str)
        
        if screen_info.get("status") != "success":
            return screen_info_str
        
        # Process text elements by screen region
        texts_by_region = {
            "top": [],
            "middle": [],
            "bottom": []
        }
        
        # Get screen height, with fallback to default
        screen_height = screen_info.get("screen_size", {}).get("height", 1920)
        if screen_height <= 0:
            screen_height = 1920  # Default value if invalid
            
        top_threshold = screen_height * 0.25
        bottom_threshold = screen_height * 0.75
        
        # Filter and organize text elements by region
        filtered_text_elements = []
        unique_texts = {}
        
        for text_elem in screen_info.get("text_elements", []):
            text = text_elem.get("text", "").strip()
            if text:
                # If text doesn't exist yet, or new element has coordinates while old doesn't
                if text not in unique_texts or (
                        "center_y" in text_elem and 
                        text_elem["center_y"] and 
                        not unique_texts[text].get("center_y")):
                    unique_texts[text] = text_elem
        
        filtered_text_elements = list(unique_texts.values())
        
        # Classify elements by screen region
        for text_elem in filtered_text_elements:
            y_pos = text_elem.get("center_y", 0)
            
            if y_pos < top_threshold:
                texts_by_region["top"].append(text_elem)
            elif y_pos > bottom_threshold:
                texts_by_region["bottom"].append(text_elem)
            else:
                texts_by_region["middle"].append(text_elem)
        
        # Identify UI patterns
        ui_patterns = []
        
        # Check if it's a list view
        if len(texts_by_region["middle"]) > 3:
            middle_texts = texts_by_region["middle"]
            y_positions = [t.get("center_y") for t in middle_texts if "center_y" in t]
            
            if y_positions and len(y_positions) > 1:
                y_diffs = [abs(y_positions[i] - y_positions[i-1]) for i in range(1, len(y_positions))]
                if y_diffs and max(y_diffs) - min(y_diffs) < 20:
                    ui_patterns.append("list_view")
        
        # Check if there's a bottom navigation bar
        bottom_clickables = []
        for e in screen_info.get("clickable_elements", []):
            try:
                bounds = e.get("bounds", "")
                if isinstance(bounds, str) and bounds:
                    y_value = int(bounds.split(",")[1].replace("]", ""))
                    if y_value > bottom_threshold:
                        bottom_clickables.append(e)
                elif isinstance(bounds, dict) and "top" in bounds:
                    if int(bounds["top"]) > bottom_threshold:
                        bottom_clickables.append(e)
            except (IndexError, ValueError):
                continue
                
        if len(bottom_clickables) >= 3:
            ui_patterns.append("bottom_navigation")
        
        # Predict possible actions
        suggested_actions = []
        
        # Suggest clicking obvious buttons
        for elem in screen_info.get("clickable_elements", []):
            if elem.get("text") and len(elem.get("text")) < 20:
                suggested_actions.append({
                    "action": "tap_element", 
                    "element_text": elem.get("text"),
                    "description": f"Click button: {elem.get('text')}"
                })
        
        # For list views, suggest scrolling
        if "list_view" in ui_patterns:
            suggested_actions.append({
                "action": "swipe", 
                "description": "Scroll down the list"
            })
        
        # Build list of notable clickable elements
        notable_clickables = []
        clickable_limit = min(10, len(screen_info.get("clickable_elements", [])))
        for e in screen_info.get("clickable_elements", [])[:clickable_limit]:
            try:
                clickable_item = {
                    "text": e.get("text", ""), 
                    "content_desc": e.get("content_desc", "")
                }
                
                # If the element already has calculated center point coordinates, use them directly
                if "center_x" in e and "center_y" in e:
                    clickable_item["center_x"] = e["center_x"]
                    clickable_item["center_y"] = e["center_y"]
                # Otherwise try to calculate from bounds
                elif "bounds" in e:
                    bounds = e["bounds"]
                    if isinstance(bounds, str):
                        coords = bounds.replace("[", "").replace("]", "").split(",")
                        if len(coords) == 4:
                            x1 = int(coords[0])
                            y1 = int(coords[1])
                            x2 = int(coords[2])
                            y2 = int(coords[3])
                            clickable_item["center_x"] = (x1 + x2) // 2
                            clickable_item["center_y"] = (y1 + y2) // 2
                    elif isinstance(bounds, dict) and all(k in bounds for k in ["left", "top", "right", "bottom"]):
                        x1 = int(bounds["left"])
                        y1 = int(bounds["top"])
                        x2 = int(bounds["right"])
                        y2 = int(bounds["bottom"])
                        clickable_item["center_x"] = (x1 + x2) // 2
                        clickable_item["center_y"] = (y1 + y2) // 2
                
                # Only add elements with center_x and center_y, or with meaningful text/content_desc
                if ("center_x" in clickable_item and "center_y" in clickable_item) or clickable_item["text"] or clickable_item["content_desc"]:
                    notable_clickables.append(clickable_item)
            except Exception:
                continue
        
        # Build AI-friendly output
        screen_analysis = {
            "status": "success",
            "message": "Successfully analyzed screen content",
            "screen_size": screen_info["screen_size"],
            "screen_analysis": {
                "text_elements": {
                    "total": len(filtered_text_elements),
                    "by_region": {
                        "top": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                                for t in texts_by_region["top"] if "center_x" in t and "center_y" in t],
                        "middle": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                                for t in texts_by_region["middle"] if "center_x" in t and "center_y" in t],
                        "bottom": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                                for t in texts_by_region["bottom"] if "center_x" in t and "center_y" in t]
                    },
                    "all_text": [t.get("text", "") for t in filtered_text_elements]
                },
                "ui_patterns": ui_patterns,
                "clickable_count": screen_info.get("clickable_elements_count", 0),
                "notable_clickables": notable_clickables
            },
            "suggested_actions": suggested_actions,
        }
        
        return json.dumps(screen_analysis, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error analyzing screen: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to analyze screen: {str(e)}"
        })


async def interact_with_screen(action: str, params: Dict[str, Any] = None) -> str:
    """Execute screen interaction actions
    
    Unified interface for screen interactions including tapping, swiping, key pressing, text input, and element search.
    
    Args:
        action (str): Action type, one of:
            - "tap": Tap screen at specified coordinates or on element with given text
            - "swipe": Swipe screen from one position to another
            - "key": Press a system key
            - "text": Input text
            - "find": Find UI element(s)
            - "wait": Wait for element to appear
            - "scroll": Scroll to find element
            
        params (Dict[str, Any]): Parameters dictionary with action-specific values:
            For "tap" action:
                - x (int): X coordinate to tap
                - y (int): Y coordinate to tap
                - element_text (str): Text of element to tap (alternative to x,y coordinates)
                - partial (bool, optional): Use partial matching when using element_text, defaults to True
            
            For "swipe" action:
                - x1 (int): Start X coordinate
                - y1 (int): Start Y coordinate
                - x2 (int): End X coordinate
                - y2 (int): End Y coordinate
                - duration (int, optional): Swipe duration in ms, defaults to 300
            
            For "key" action:
                - keycode (str/int): Key to press (e.g., "back", "home", "enter", or keycode number)
            
            For "text" action:
                - content (str): Text to input
            
            For "find" action:
                - method (str): Search method, one of: "text", "id", "content_desc", "class", "clickable"
                - value (str): Text/value to search for (not required for method="clickable")
                - partial (bool, optional): Use partial matching, defaults to True (for text/content_desc)
            
            For "wait" action:
                - method (str): Search method, same options as "find"
                - value (str): Text/value to search for
                - timeout (int, optional): Maximum wait time in seconds, defaults to 30
                - interval (float, optional): Check interval in seconds, defaults to 1.0
            
            For "scroll" action:
                - method (str): Search method, same options as "find"
                - value (str): Text/value to search for
                - direction (str, optional): Scroll direction, one of: "up", "down", "left", "right", defaults to "down"
                - max_swipes (int, optional): Maximum swipe attempts, defaults to 5
    
    Returns:
        str: JSON string with operation result containing:
            For successful operations:
                {
                    "status": "success",
                    "message": "Operation-specific success message",
                    ... (optional action-specific data)
                }
            
            For failed operations:
                {
                    "status": "error",
                    "message": "Error description"
                }
            
            Special cases:
                - find: Returns elements list containing matching elements with their properties
                - wait: Returns success when element found or error if timeout
                - scroll: Returns success when element found or error if not found after max attempts
    
    Examples:
        # Tap by coordinates
        result = await interact_with_screen("tap", {"x": 100, "y": 200})
        
        # Tap by element text
        result = await interact_with_screen("tap", {"element_text": "Login"})
        
        # Swipe down
        result = await interact_with_screen("swipe", 
                                           {"x1": 500, "y1": 300, 
                                            "x2": 500, "y2": 1200, 
                                            "duration": 300})
        
        # Input text
        result = await interact_with_screen("text", {"content": "Hello world"})
        
        # Press back key
        result = await interact_with_screen("key", {"keycode": "back"})
        
        # Find element by text
        result = await interact_with_screen("find", 
                                           {"method": "text", 
                                            "value": "Settings", 
                                            "partial": True})
        
        # Wait for element to appear
        result = await interact_with_screen("wait", 
                                           {"method": "text", 
                                            "value": "Success", 
                                            "timeout": 10,
                                            "interval": 0.5})
                                            
        # Scroll to find element
        result = await interact_with_screen("scroll", 
                                           {"method": "text", 
                                            "value": "Privacy Policy", 
                                            "direction": "down", 
                                            "max_swipes": 8})
    """
    # Debug logging to help track issues
    logger.debug(f"interact_with_screen called with action={action}, params type={type(params).__name__}")
    if params is not None:
        logger.debug(f"params content: {str(params)[:100]}{'...' if len(str(params)) > 100 else ''}")
    
    # Handle different types of params input to make function more robust
    if params is None:
        params = {}
    elif isinstance(params, str):
        # Try to parse JSON string
        try:
            params = json.loads(params)
            if not isinstance(params, dict):
                params = {"value": params}
        except json.JSONDecodeError:
            params = {"value": params}
    elif not isinstance(params, dict):
        # Handle other types by converting to a dictionary
        try:
            # Try to convert to dictionary if it's a mapping-like object
            params = dict(params)
        except (TypeError, ValueError):
            # If that fails, create a dict with a default key
            logger.error(f"params must be a dictionary, got {type(params).__name__}")
            params = {"value": str(params)}
    
    # Create a copy to avoid modifying the original
    params_copy = params.copy()
    
    # Ensure numeric parameters are properly converted
    try:
        # Convert integer parameters
        for key in ['x', 'y', 'x1', 'y1', 'x2', 'y2', 'duration', 'timeout', 'max_swipes']:
            if key in params_copy:
                try:
                    params_copy[key] = int(params_copy[key])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert '{key}' parameter to integer: {params_copy[key]}")
                    if key in ['duration', 'timeout', 'max_swipes']:
                        # Use reasonable defaults for these parameters
                        params_copy[key] = 300 if key == 'duration' else 30 if key == 'timeout' else 5
                    
        # Convert float parameters
        if 'interval' in params_copy:
            try:
                params_copy['interval'] = float(params_copy['interval'])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert 'interval' parameter to float: {params_copy['interval']}")
                params_copy['interval'] = 1.0  # Default interval
    except Exception as e:
        logger.error(f"Error converting parameter types: {str(e)}")
        
    try:
        if action == "tap":
            if "element_text" in params_copy:
                element_result = await find_element_by_text(
                    params_copy["element_text"], 
                    params_copy.get("partial", True)
                )
                element_data = json.loads(element_result)
                
                if element_data.get("status") == "success" and element_data.get("elements"):
                    element = UIElement(element_data["elements"][0])
                    return await element.tap()
                else:
                    return json.dumps({
                        "status": "error", 
                        "message": f"Could not find element with text '{params_copy['element_text']}'"
                    })
            elif "x" in params_copy and "y" in params_copy:
                return await tap_screen(params_copy["x"], params_copy["y"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing required tap parameters (either element_text or x,y coordinates)"
                })
                
        elif action == "swipe":
            if all(k in params_copy for k in ["x1", "y1", "x2", "y2"]):
                duration = params_copy.get("duration", 300)
                return await swipe_screen(
                    params_copy["x1"], params_copy["y1"], 
                    params_copy["x2"], params_copy["y2"], 
                    duration
                )
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing coordinates required for swipe"
                })
                
        elif action == "key":
            if "keycode" in params_copy:
                return await press_key(params_copy["keycode"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing key parameter"
                })
                
        elif action == "text":
            if "content" in params_copy:
                return await input_text(str(params_copy["content"]))
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing text content parameter"
                })
                
        elif action == "find":
            method = params_copy.get("method", "text")
            value = params_copy.get("value", "")
            
            if not value and method != "clickable":
                return json.dumps({
                    "status": "error", 
                    "message": "Finding element requires a search value"
                })
                
            if method == "text":
                return await find_element_by_text(value, params_copy.get("partial", True))
            elif method == "id":
                return await find_element_by_id(value)
            elif method == "content_desc":
                return await find_element_by_content_desc(value, params_copy.get("partial", True))
            elif method == "class":
                return await find_element_by_class(value)
            elif method == "clickable":
                return await find_clickable_elements()
            else:
                return json.dumps({
                    "status": "error", 
                    "message": f"Unsupported search method: {method}"
                })
                
        elif action == "wait":
            method = params_copy.get("method", "text")
            value = params_copy.get("value", "")
            timeout = params_copy.get("timeout", 30)
            interval = params_copy.get("interval", 1.0)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "Waiting for element requires a search value"
                })
                
            return await wait_for_element(method, value, timeout, interval)
            
        elif action == "scroll":
            method = params_copy.get("method", "text")
            value = params_copy.get("value", "")
            direction = params_copy.get("direction", "down")
            max_swipes = params_copy.get("max_swipes", 5)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "Scrolling to find requires a search value"
                })
                
            return await scroll_to_element(method, value, direction, max_swipes)
            
        else:
            return json.dumps({
                "status": "error", 
                "message": f"Unsupported interaction action: {action}"
            })
            
    except Exception as e:
        logger.error(f"Error executing interaction action {action}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Interaction operation failed: {str(e)}"
        })

async def launch_app_activity(package_name: str, activity_name: Optional[str] = None) -> str:
    """Launch an app using package name and optionally an activity name
    
    This function uses adb to start an application on the device either by package name
    or by specifying both package and activity. It provides reliable app launching across
    different Android devices and versions.
    
    Args:
        package_name (str): The package name of the app to launch (e.g., "com.android.contacts")
        activity_name (str, optional): The specific activity to launch. If not provided,
                                      launches the app's main activity. Defaults to None.
    
    Returns:
        str: JSON string with operation result:
            For successful operations:
                {
                    "status": "success",
                    "message": "Successfully launched <package_name>"
                }
            
            For failed operations:
                {
                    "status": "error",
                    "message": "Failed to launch app: <error details>"
                }
    
    Examples:
        # Launch an app using just the package name
        result = await launch_app_activity("com.android.contacts")
        
        # Launch a specific activity within an app
        result = await launch_app_activity("com.android.dialer", "com.android.dialer.DialtactsActivity")
        
        # Launch Android settings
        result = await launch_app_activity("com.android.settings")
    """
    try:
        if activity_name:
            # Launch specific activity
            cmd = f"adb shell am start -n {package_name}/{activity_name}"
        else:
            # Launch app's main activity
            cmd = f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully launched {package_name}"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to launch app: {output}"
            })
    except Exception as e:
        logger.error(f"Error launching app {package_name}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to launch app: {str(e)}"
        })

async def launch_intent(intent_action: str, intent_type: Optional[str] = None, extras: Optional[Dict[str, str]] = None) -> str:
    """Launch an activity using Android intent system
    
    This function allows launching activities using Android's intent system, which can be used
    to perform various actions like opening the contacts app in "add new contact" mode,
    opening URLs, or sharing content between apps.
    
    Args:
        intent_action (str): The action to perform (e.g., "android.intent.action.INSERT",
                          "android.intent.action.VIEW", "android.intent.action.SEND")
        intent_type (str, optional): The MIME type for the intent (e.g., "vnd.android.cursor.dir/contact",
                                  "text/plain", "image/jpeg"). Defaults to None.
        extras (Dict[str, str], optional): Extra data to pass with the intent as key-value pairs.
                                        Useful for pre-populating fields or passing data. Defaults to None.
    
    Returns:
        str: JSON string with operation result:
            For successful operations:
                {
                    "status": "success",
                    "message": "Successfully launched intent: <intent_action>"
                }
            
            For failed operations:
                {
                    "status": "error",
                    "message": "Failed to launch intent: <error details>"
                }
    
    Examples:
        # Open contacts app in "add new contact" mode
        extras = {"name": "John Doe", "phone": "1234567890"}
        result = await launch_intent(
            "android.intent.action.INSERT", 
            "vnd.android.cursor.dir/contact", 
            extras
        )
        
        # Open URL in browser
        result = await launch_intent(
            "android.intent.action.VIEW",
            None,
            {"uri": "https://www.example.com"}
        )
        
        # Share text
        result = await launch_intent(
            "android.intent.action.SEND",
            "text/plain",
            {"android.intent.extra.TEXT": "Hello world!"}
        )
    """
    try:
        # Construct base command
        cmd = f"adb shell am start -a {intent_action}"
        
        # Add type if provided
        if intent_type:
            cmd += f" -t {intent_type}"
        
        # Add extras if provided
        if extras:
            for key, value in extras.items():
                # Escape quotes in value
                value = value.replace('"', '\\"')
                cmd += f' --es {key} "{value}"'
        
        success, output = await run_command(cmd)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully launched intent: {intent_action}"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to launch intent: {output}"
            })
    except Exception as e:
        logger.error(f"Error launching intent {intent_action}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to launch intent: {str(e)}"
        })

async def create_contact(name: str, phone: str) -> str:
    """Create a new contact with the given name and phone number
    
    This function uses UI automation to create a new contact on the device. It:
    1. Opens the contact creation intent
    2. Pre-fills name and phone number fields
    3. Waits for the contact form to appear
    4. Analyzes the screen to find confirmation buttons
    5. Taps the confirmation button to save the contact
    
    Args:
        name (str): The contact's full name
        phone (str): The phone number for the contact
    
    Returns:
        str: JSON string with operation result containing:
            For successful operations:
                {
                    "status": "success",
                    "message": "Successfully created contact <name> with phone <phone>"
                }
            
            For partial success operations:
                {
                    "status": "partial_success",
                    "message": "Attempted to tap potential confirmation button location. Please verify contact creation."
                }
            
            For failed operations:
                {
                    "status": "error",
                    "message": "Error description"
                }
    
    Examples:
        # Create a contact with name and phone number
        result = await create_contact("John Doe", "123-456-7890")
        
        # Create a contact using a test phone number (recommended for testing)
        result = await create_contact("Test Contact", "10086")
            
    Note:
        When testing this feature, it's recommended to use 10086 as the test phone number.
        This is China Mobile's customer service number, which is suitable for testing
        environments and easy to recognize.
    """
    try:
        # Step 1: Launch the contact creation intent
        extras = {
            "name": name,
            "phone": phone
        }
        intent_result = await launch_intent(
            "android.intent.action.INSERT", 
            "vnd.android.cursor.dir/contact",
            extras
        )
        
        intent_data = json.loads(intent_result)
        if intent_data.get("status") != "success":
            return intent_result
        
        # Step 2: Wait for the contact form to appear
        await wait_for_element("text", "Contact", timeout=5)  # Wait for Contact form
        
        # Step 3: Analyze screen to find confirmation button
        screen_result = await analyze_screen()
        screen_data = json.loads(screen_result)
        
        if screen_data.get("status") != "success":
            return json.dumps({
                "status": "error",
                "message": "Failed to analyze screen to find confirmation button"
            })
        
        # Look for confirmation button - common patterns
        confirmation_buttons = ["Save", "Done", "Confirm", "OK", "✓", "√"]
        found_button = None
        
        # Check suggested actions first
        for action in screen_data.get("suggested_actions", []):
            if action.get("action") == "tap_element":
                text = action.get("element_text", "")
                if text in confirmation_buttons or any(btn in text for btn in confirmation_buttons):
                    found_button = text
                    break
        
        # If not found in suggested actions, search in all clickable elements
        if not found_button:
            clickables = screen_data.get("screen_analysis", {}).get("notable_clickables", [])
            for element in clickables:
                text = element.get("text", "")
                if text in confirmation_buttons or any(btn in text for btn in confirmation_buttons):
                    found_button = text
                    break
        
        # As a last resort, look for confirmation buttons in top-right corner
        if not found_button:
            # Try to tap top-right corner where save button is often located
            size = screen_data.get("screen_size", {})
            width = size.get("width", 1080)
            
            # Create tap action at approximately 90% of width and 10% of height
            tap_x = int(width * 0.9)
            tap_y = int(size.get("height", 1920) * 0.1)
            
            tap_result = await tap_screen(tap_x, tap_y)
            tap_data = json.loads(tap_result)
            
            return json.dumps({
                "status": "partial_success" if tap_data.get("status") == "success" else "error",
                "message": "Attempted to tap potential confirmation button location. Please verify contact creation."
            })
        
        # Step 4: Click the confirmation button if found
        if found_button:
            tap_result = await interact_with_screen("tap", {"element_text": found_button})
            tap_data = json.loads(tap_result)
            
            if tap_data.get("status") == "success":
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully created contact {name} with phone {phone}"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to tap confirmation button: {tap_data.get('message')}"
                })
        else:
            return json.dumps({
                "status": "error",
                "message": "Could not find confirmation button"
            })
    
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to create contact: {str(e)}"
        }) 