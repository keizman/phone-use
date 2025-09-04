"""
Advertisement detection and automatic removal system for phone_mcp
"""
import asyncio
import json
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple
from ..core import run_command

logger = logging.getLogger("phone_mcp")


def detect_ad_elements(ui_data: dict) -> dict:
    """
    Detect if current screen contains advertisement using confidence-based algorithm.
    
    Detection algorithm with confidence scoring:
    - Element count <10: +20% confidence
    - "ad" keyword in resource_id/name/text/class_name: +30% confidence  
    - "close" related controls: +25% confidence
    - Close element is clickable: +15% confidence
    - AD and close elements distance proximity: +10% confidence
    
    Args:
        ui_data: UI dump data containing elements
        
    Returns:
        dict: {
            "confidence": int,  # 0-100 percentage
            "close_element": dict or None,
            "ad_elements": list,
            "reasoning": str
        }
    """
    if not isinstance(ui_data, dict) or "elements" not in ui_data:
        return {
            "confidence": 0,
            "close_element": None,
            "ad_elements": [],
            "reasoning": "Invalid UI data"
        }
    
    elements = ui_data.get("elements", [])
    total_elements = len(elements)
    confidence = 0
    reasoning_parts = []
    
    ad_elements = []
    close_element = None
    
    # Rule 1: Element count analysis (+20% if <10 elements)
    if total_elements < 10:
        confidence += 20
        reasoning_parts.append(f"Few elements ({total_elements}<10)")
    
    # Analyze each element
    for element in elements:
        resource_id = element.get("resource_id", "").lower()
        name = element.get("name", "").lower()
        text = element.get("text", "").lower()
        class_name = element.get("class_name", "").lower()
        clickable = element.get("clickable", False)
        
        # Rule 2: Check for "ad" keywords (+30%)
        ad_keywords = ["ad", "advertisement", "banner", "mivad"]
        for keyword in ad_keywords:
            if any(keyword in field for field in [resource_id, name, text, class_name]):
                if element not in ad_elements:
                    ad_elements.append(element)
                    confidence = min(confidence + 30, 100)
                    reasoning_parts.append(f"Found ad keyword '{keyword}'")
                break
        
        # Rule 3: Check for close button (+25% base, +15% if clickable)
        close_keywords = ["close", "dismiss", "cancel", "mivclose", "×", "✕"]
        for keyword in close_keywords:
            if any(keyword in field for field in [resource_id, name, text, class_name]):
                close_element = element
                confidence = min(confidence + 25, 100)
                reasoning_parts.append(f"Found close keyword '{keyword}'")
                
                # Rule 4: Close element clickability (+15%)
                if clickable:
                    confidence = min(confidence + 15, 100)
                    reasoning_parts.append("Close element is clickable")
                break
    
    # Rule 5: Distance analysis (+10% if ad and close elements are close)
    if ad_elements and close_element:
        for ad_elem in ad_elements:
            if _calculate_element_distance(ad_elem, close_element) < 500:  # pixels
                confidence = min(confidence + 10, 100)
                reasoning_parts.append("Ad and close elements are proximate")
                break
    
    return {
        "confidence": confidence,
        "close_element": close_element,
        "ad_elements": ad_elements,
        "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "No ad indicators found"
    }


def _calculate_element_distance(elem1: dict, elem2: dict) -> float:
    """Calculate distance between two UI elements using their center coordinates."""
    try:
        x1, y1 = elem1.get("center_x", 0), elem1.get("center_y", 0)
        x2, y2 = elem2.get("center_x", 0), elem2.get("center_y", 0)
        
        # Convert normalized coordinates to pixels if needed
        if x1 <= 1 and y1 <= 1:
            x1, y1 = x1 * 1080, y1 * 1920
        if x2 <= 1 and y2 <= 1:
            x2, y2 = x2 * 1080, y2 * 1920
            
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    except (TypeError, ValueError):
        return float('inf')


async def auto_close_ads(ui_data: dict, max_attempts: int = 3, auto_threshold: int = 90, warning_threshold: int = 70) -> dict:
    """
    Automatically detect and close advertisements with retry mechanism.
    
    Args:
        ui_data: Current UI dump data
        max_attempts: Maximum number of ad closure attempts (default: 3)
        auto_threshold: Confidence threshold for automatic closing (default: 90%)
        warning_threshold: Confidence threshold for user warning (default: 70%)
        
    Returns:
        dict: {
            "ads_closed": int,
            "final_ui_data": dict,
            "attempts": list,
            "warning": str or None
        }
    """
    attempts = []
    ads_closed = 0
    current_ui = ui_data
    
    for attempt in range(max_attempts):
        ad_detection = detect_ad_elements(current_ui)
        confidence = ad_detection["confidence"]
        
        attempt_info = {
            "attempt": attempt + 1,
            "confidence": confidence,
            "reasoning": ad_detection["reasoning"]
        }
        attempts.append(attempt_info)
        
        # Check if confidence is below auto-close threshold
        if confidence < auto_threshold:
            attempt_info["action"] = "skipped - confidence too low"
            break
            
        close_element = ad_detection["close_element"]
        if not close_element:
            attempt_info["action"] = "failed - no close element found"
            break
            
        # Attempt to close the ad
        success = await _tap_close_element(close_element)
        if success:
            ads_closed += 1
            attempt_info["action"] = "successfully closed ad"
            
            # Wait for UI to update
            await asyncio.sleep(1.5)
            
            # Get new UI state
            new_ui_data = await _refresh_ui_state()
            if new_ui_data:
                current_ui = new_ui_data
            else:
                attempt_info["refresh_error"] = "failed to get new UI state"
                break
        else:
            attempt_info["action"] = "failed to tap close element"
            break
    
    # Check final state for warning
    final_detection = detect_ad_elements(current_ui)
    warning = None
    if final_detection["confidence"] >= warning_threshold:
        warning = "Possible unremoved ads detected. Please check and close before continuing task execution."
    
    return {
        "ads_closed": ads_closed,
        "final_ui_data": current_ui,
        "attempts": attempts,
        "warning": warning
    }


async def _tap_close_element(close_element: dict) -> bool:
    """Tap the close element and return success status."""
    try:
        center_x = close_element.get("center_x", 0)
        center_y = close_element.get("center_y", 0)
        
        if not center_x or not center_y:
            return False
            
        # Convert normalized coordinates to screen coordinates if needed
        if center_x <= 1 and center_y <= 1:
            center_x = int(center_x * 1080)  # Assume 1080 width
            center_y = int(center_y * 1920)  # Assume 1920 height
        
        tap_cmd = f"adb shell input tap {center_x} {center_y}"
        success, output = await run_command(tap_cmd)
        
        if success:
            logger.info(f"Successfully tapped close element at ({center_x}, {center_y})")
        else:
            logger.warning(f"Failed to tap close element: {output}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error tapping close element: {e}")
        return False


async def _refresh_ui_state() -> Optional[dict]:
    """Get fresh UI state after ad closure attempt."""
    try:
        # Get new UI dump
        dump_cmd = "adb shell uiautomator dump /dev/stdout"
        success, xml_output = await run_command(dump_cmd)
        
        if not success:
            return None
            
        # Parse XML and extract elements
        root = ET.fromstring(xml_output)
        elements = []
        
        def extract_element_info(node):
            bounds_str = node.attrib.get('bounds', '[0,0][0,0]')
            coords = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
            
            if len(coords) >= 2:
                x1, y1 = map(int, coords[0])
                x2, y2 = map(int, coords[1])
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
            else:
                center_x = center_y = 0
                x1 = y1 = x2 = y2 = 0
            
            return {
                "name": node.attrib.get('resource-id', '') or node.attrib.get('text', ''),
                "text": node.attrib.get('text', ''),
                "resource_id": node.attrib.get('resource-id', ''),
                "class_name": node.attrib.get('class', ''),
                "clickable": node.attrib.get('clickable', 'false').lower() == 'true',
                "center_x": center_x,
                "center_y": center_y,
                "bounds": [x1, y1, x2, y2]
            }
        
        # Recursively extract all elements
        def extract_all(node):
            elements.append(extract_element_info(node))
            for child in node:
                extract_all(child)
        
        extract_all(root)
        
        return {
            "status": "success",
            "total_count": len(elements),
            "elements": elements
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh UI state: {e}")
        return None