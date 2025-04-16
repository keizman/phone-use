# -*- coding: utf-8 -*-
"""
Screen Analysis and Interaction Interface - Provides structured screen information and unified interaction methods
Integrates multiple tools, reduces redundant functionality, making it easier for models to understand and use
"""

import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

# Import base functionality modules
from .ui import dump_ui, find_element_by_text, find_element_by_id
from .ui_enhanced import (
    find_element_by_content_desc, find_element_by_class, 
    find_clickable_elements, wait_for_element, scroll_to_element
)
from .interactions import tap_screen, swipe_screen, press_key, input_text, get_screen_size
from .media import take_screenshot

logger = logging.getLogger("phone_mcp")

class UIElement:
    """Class representing a UI element, containing its properties and interaction methods
    
    Attributes:
        text (str): Element text content
        resource_id (str): Element resource ID
        class_name (str): Element class name
        content_desc (str): Element content description
        clickable (bool): Whether the element is clickable
        bounds (str): Element boundary coordinates string "[x1,y1][x2,y2]"
        x1, y1, x2, y2 (int): Boundary coordinate values
        center_x, center_y (int): Element center point coordinates
    
    Methods:
        to_dict(): Convert element to dictionary format
        tap(): Tap the center of the element
    """
    
    def __init__(self, element_data: Dict[str, Any]):
        """Initialize UI element
        
        Args:
            element_data: Dictionary containing element properties
        """
        self.data = element_data
        self.text = element_data.get("text", "")
        self.resource_id = element_data.get("resource_id", "")
        self.class_name = element_data.get("class_name", "")
        self.content_desc = element_data.get("content_desc", "")
        self.clickable = element_data.get("clickable", False)
        self.bounds = element_data.get("bounds", "")
        
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
        
        Returns:
            str: JSON string of operation result, containing status and message
        """
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            return await tap_screen(self.center_x, self.center_y)
        return json.dumps({"status": "error", "message": "Element does not have valid coordinates"})


async def get_screen_info() -> str:
    """Get detailed information about the current screen, including all visible elements, text, coordinates, etc.
    
    This function gets the complete UI hierarchy, parses all element attributes, and extracts text and clickable elements.
    
    Returns:
        str: Screen information in JSON format, containing:
            - status: Operation status ("success" or "error")
            - screen_size: Screen size (width, height)
            - all_elements_count: Total number of elements
            - clickable_elements_count: Number of clickable elements
            - text_elements_count: Number of text elements
            - text_elements: List of elements containing text
            - clickable_elements: List of clickable elements
            - timestamp: Time when information was collected
    
    Example:
        ```
        {
          "status": "success", 
          "screen_size": {"width": 1080, "height": 2340},
          "all_elements_count": 156,
          "text_elements": [
            {"text": "Settings", "bounds": "[52,1688][228,1775]", "center_x": 140, "center_y": 1732}
          ]
        }
        ```
    """
    # Get UI tree
    ui_dump = await dump_ui()
    
    try:
        ui_data = json.loads(ui_dump)
        
        # Get screen size
        size_result = await get_screen_size()
        screen_size = json.loads(size_result)
        
        # Get clickable elements
        clickable_result = await find_clickable_elements()
        clickable_elements = json.loads(clickable_result).get("elements", [])
        
        # Extract all text elements
        text_elements = []
        all_elements = []  # Ensure variable is initialized in all cases
        
        # Parse all elements
        if "elements" in ui_data:
            for elem_data in ui_data["elements"]:
                element = UIElement(elem_data)
                all_elements.append(element.to_dict())
                
                # If there is text, add to text elements list
                if element.text.strip():
                    text_element = {
                        "text": element.text,
                        "bounds": element.bounds
                    }
                    if hasattr(element, "center_x") and hasattr(element, "center_y"):
                        text_element["center_x"] = element.center_x
                        text_element["center_y"] = element.center_y
                    text_elements.append(text_element)
        
        result = {
            "status": "success",
            "screen_size": {
                "width": screen_size.get("width", 0),
                "height": screen_size.get("height", 0),
            },
            "all_elements_count": len(all_elements),
            "clickable_elements_count": len(clickable_elements),
            "text_elements_count": len(text_elements),
            "text_elements": text_elements,
            "clickable_elements": clickable_elements,
            "timestamp": time.time(),
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error parsing UI information: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Unable to get screen information: {str(e)}"
        }, ensure_ascii=False)


async def analyze_screen() -> str:
    """Analyze the current screen and provide structured information
    
    This function analyzes the current screen content, extracts useful information and organizes it by category, including:
    - Text elements classified by region (top/middle/bottom)
    - UI pattern detection (such as list view, bottom navigation bar, etc.)
    - Possible interaction suggestions
    
    Suitable for understanding screen content and deciding next steps.
    
    Returns:
        str: Screen analysis results in JSON format, containing:
            - status: Operation status ("success" or "error")
            - screen_size: Screen size
            - screen_analysis: Analysis results including text elements, UI patterns, clickable elements, etc.
            - suggested_actions: Suggested interaction operations
            - screenshot_path: Screenshot save path (if available)
    
    Example:
        ```
        {
          "status": "success",
          "screen_analysis": {
            "text_elements": {
              "top": [{"text": "Settings", "center_x": 540, "center_y": 89}],
              "middle": [{"text": "WLAN", "center_x": 270, "center_y": 614}],
              "bottom": [{"text": "OK", "center_x": 540, "center_y": 2200}]
            },
            "ui_patterns": ["list_view"],
            "notable_clickables": [...]
          },
          "suggested_actions": [
            {"action": "tap_element", "element_text": "OK"}
          ]
        }
        ```
    """
    screen_info_str = await get_screen_info()
    try:
        screen_info = json.loads(screen_info_str)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Unable to parse screen information JSON"})
    
    if screen_info.get("status") != "success":
        return screen_info_str
    
    # Screenshot for debugging/reference
    screenshot_result = await take_screenshot()
    screenshot_path = None
    if "success" in screenshot_result:
        screenshot_path = "./screen_snapshot.png"
    
    # Analyze text by screen region
    texts_by_region = {
        "top": [],
        "middle": [],
        "bottom": []
    }
    
    screen_height = screen_info["screen_size"]["height"]
    top_threshold = screen_height * 0.25
    bottom_threshold = screen_height * 0.75
    
    for text_elem in screen_info.get("text_elements", []):
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
    
    # Build list of clickable elements to return, ensuring safe coordinate parsing
    notable_clickables = []
    for e in screen_info.get("clickable_elements", [])[:10]:
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
            
            # Only add elements with center_x and center_y
            if "center_x" in clickable_item and "center_y" in clickable_item:
                notable_clickables.append(clickable_item)
        except Exception:
            continue
    
    # Build AI-friendly output
    screen_analysis = {
        "status": "success",
        "screen_size": screen_info["screen_size"],
        "screen_analysis": {
            "text_elements": {
                "total": screen_info["text_elements_count"],
                "by_region": {
                    "top": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["top"] if "center_x" in t and "center_y" in t],
                    "middle": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["middle"] if "center_x" in t and "center_y" in t],
                    "bottom": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["bottom"] if "center_x" in t and "center_y" in t]
                }
            },
            "ui_patterns": ui_patterns,
            "clickable_count": screen_info["clickable_elements_count"],
            "notable_clickables": notable_clickables
        },
        "suggested_actions": suggested_actions,
        "screenshot_path": screenshot_path,
    }
    
    return json.dumps(screen_analysis, ensure_ascii=False, indent=2)


async def interact_with_screen(action: str, params: Dict[str, Any]) -> str:
    """Execute screen interaction actions
    
    Unified interaction interface supporting multiple interaction methods, including tapping, swiping, key pressing, text input, etc.
    
    Args:
        action: Action type, can be one of:
            - "tap": Tap screen, requires coordinates or element text
            - "swipe": Swipe screen, requires start and end coordinates
            - "key": Press key, requires key code
            - "text": Input text, requires text content
            - "find": Find element, requires search method and value
            - "wait": Wait for element to appear, requires search method, value and timeout parameters
            - "scroll": Scroll to find element, requires search method, value and direction
        params: Action parameter dictionary, different parameters needed for different actions:
            - tap: element_text or x/y coordinates
            - swipe: x1, y1, x2, y2, optional duration
            - key: keycode
            - text: content
            - find: method, value
            - wait: method, value, timeout, interval
            - scroll: method, value, direction, max_swipes
    
    Returns:
        str: JSON string of operation result, containing status and message
    
    Example:
        ```python
        # Tap coordinates
        result = await interact_with_screen("tap", {"x": 100, "y": 200})
        
        # Tap text element
        result = await interact_with_screen("tap", {"element_text": "Login"})
        
        # Swipe screen
        result = await interact_with_screen("swipe", 
                                           {"x1": 500, "y1": 1000, 
                                            "x2": 500, "y2": 200, 
                                            "duration": 300})
        
        # Wait for element to appear
        result = await interact_with_screen("wait", 
                                           {"method": "text", 
                                            "value": "Success", 
                                            "timeout": 10})
        ```
    """
    try:
        if action == "tap":
            if "element_text" in params:
                element_result = await find_element_by_text(
                    params["element_text"], 
                    params.get("partial", True)
                )
                element_data = json.loads(element_result)
                
                if element_data.get("status") == "success" and element_data.get("elements"):
                    element = UIElement(element_data["elements"][0])
                    return await element.tap()
                else:
                    return json.dumps({
                        "status": "error", 
                        "message": f"Could not find element with text '{params['element_text']}'"
                    }, ensure_ascii=False)
            elif "x" in params and "y" in params:
                return await tap_screen(params["x"], params["y"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing valid tap parameters"
                }, ensure_ascii=False)
                
        elif action == "swipe":
            if all(k in params for k in ["x1", "y1", "x2", "y2"]):
                duration = params.get("duration", 300)
                return await swipe_screen(
                    params["x1"], params["y1"], 
                    params["x2"], params["y2"], 
                    duration
                )
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing coordinates required for swipe"
                }, ensure_ascii=False)
                
        elif action == "key":
            if "keycode" in params:
                return await press_key(params["keycode"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing key parameter"
                }, ensure_ascii=False)
                
        elif action == "text":
            if "content" in params:
                return await input_text(params["content"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Missing text content parameter"
                }, ensure_ascii=False)
                
        elif action == "find":
            method = params.get("method", "text")
            value = params.get("value", "")
            
            if not value and method != "clickable":
                return json.dumps({
                    "status": "error", 
                    "message": "Finding element requires a search value"
                }, ensure_ascii=False)
                
            if method == "text":
                return await find_element_by_text(value, params.get("partial", True))
            elif method == "id":
                return await find_element_by_id(value)
            elif method == "content_desc":
                return await find_element_by_content_desc(value, params.get("partial", True))
            elif method == "class":
                return await find_element_by_class(value)
            elif method == "clickable":
                return await find_clickable_elements()
            else:
                return json.dumps({
                    "status": "error", 
                    "message": f"Unsupported search method: {method}"
                }, ensure_ascii=False)
                
        elif action == "wait":
            method = params.get("method", "text")
            value = params.get("value", "")
            timeout = params.get("timeout", 30)
            interval = params.get("interval", 1.0)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "Waiting for element requires a search value"
                }, ensure_ascii=False)
                
            return await wait_for_element(method, value, timeout, interval)
            
        elif action == "scroll":
            method = params.get("method", "text")
            value = params.get("value", "")
            direction = params.get("direction", "down")
            max_swipes = params.get("max_swipes", 5)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "Scrolling to find requires a search value"
                }, ensure_ascii=False)
                
            return await scroll_to_element(method, value, direction, max_swipes)
            
        else:
            return json.dumps({
                "status": "error", 
                "message": f"Unsupported interaction action: {action}"
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error executing interaction action {action}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Interaction operation failed: {str(e)}"
        }, ensure_ascii=False) 