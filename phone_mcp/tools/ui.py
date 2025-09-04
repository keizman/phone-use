"""UI inspection functions for Phone MCP.
This module provides functions to inspect and interact with UI elements on the device.
Uses intelligent method selection with unified interface - external LLM cannot perceive
the underlying technology (XML parsing vs Omniparser visual recognition).
"""

import asyncio
import json
import re
import os
import tempfile
import xml.etree.ElementTree as ET
import logging
from typing import Optional
from ..core import run_command, check_device_connection
from .ad_detector import auto_close_ads

logger = logging.getLogger("phone_mcp")

# Lazy import to avoid circular dependencies
_ui_scheduler = None

def _get_scheduler():
    """Get UI scheduler with lazy initialization"""
    global _ui_scheduler
    if _ui_scheduler is None:
        try:
            from .enhanced_ui_extractor import get_ui_scheduler
            _ui_scheduler = get_ui_scheduler()
        except ImportError:
            logger.warning("Enhanced UI scheduler not available, using XML fallback")
            _ui_scheduler = False
    return _ui_scheduler


async def dump_ui(filter_package: Optional[str] = None) -> str:
    """Dump the current UI hierarchy from the device.
    
    This function captures the current UI state of the device screen and returns
    it in a structured format. Uses intelligent method selection automatically.
    
    Args:
        filter_package: Optional package name to filter elements
    
    Returns:
        str: JSON string containing:
            {
                "status": "success" or "error",
                "total_count": int,
                "elements": [
                    {
                        "uuid": str,
                        "name": str,
                        "text": str,
                        "package": str,
                        "resource_id": str,
                        "class_name": str,
                        "clickable": bool,
                        "center_x": float,
                        "center_y": float,
                        "bounds": [float]
                    },
                    ...
                ]
            }
    """
    # Try intelligent extraction first
    scheduler = _get_scheduler()
    if scheduler:
        try:
            result = await scheduler.get_screen_elements(filter_package)
            
            # Clean up internal details for external LLM
            data = json.loads(result)
            if data.get("status") == "success":
                # Remove internal technical details that LLM doesn't need to see
                cleaned_data = {
                    "status": "success",
                    "total_count": data.get("total_count", 0),
                    "elements": []
                }
                
                for element in data.get("elements", []):
                    cleaned_element = {
                        "uuid": element.get("uuid"),
                        "name": element.get("name", ""),
                        "text": element.get("text", ""),
                        "package": element.get("package", ""),
                        "resource_id": element.get("resource_id", ""),
                        "class_name": element.get("class_name", ""),
                        "clickable": element.get("clickable", False),
                        "center_x": element.get("center_x", 0),
                        "center_y": element.get("center_y", 0),
                        "bounds": element.get("bounds", [])
                    }
                    cleaned_data["elements"].append(cleaned_element)
                
                # Auto-detect and close ads before returning to user
                ad_result = await auto_close_ads(cleaned_data, max_attempts=3)
                
                # Always use final UI data (whether ads were closed or not)
                final_ui = ad_result["final_ui_data"]
                
                # Add ad processing information
                if ad_result["ads_closed"] > 0:
                    logger.info(f"Auto-closed {ad_result['ads_closed']} advertisements")
                    final_ui["ad_removal"] = {
                        "ads_closed": ad_result["ads_closed"],
                        "attempts": len(ad_result["attempts"]),
                        "auto_processed": True
                    }
                
                # Add warning if ads still detected
                if ad_result.get("warning"):
                    final_ui["ad_detection"] = {
                        "warning": ad_result["warning"],
                        "manual_action_needed": True
                    }
                
                return json.dumps(final_ui, indent=2)
            else:
                return result
        except Exception as e:
            logger.warning(f"Intelligent extraction failed, using XML fallback: {e}")
    
    # Fallback to XML-only extraction
    return await _dump_ui_xml_fallback(filter_package)


async def _dump_ui_xml_fallback(filter_package: Optional[str] = None) -> str:
    """XML-only UI dump for fallback when enhanced extraction fails"""
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        logger.error("Device not connected or not ready")
        return connection_status

    # Create temp file path
    try:
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "ui_dump.xml")
    except Exception as e:
        error_msg = f"Failed to create temp file: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)

    # Execute UI dump on device
    cmd = "adb shell uiautomator dump"
    success, output = await run_command(cmd)

    if not success:
        error_msg = f"UI dump failed: {output}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)

    # Get dump file path
    match = re.search(r"UI hierchary dumped to: (.*\\.xml)", output)
    if not match:
        error_msg = "Could not find dump file path"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)
        
    device_file_path = match.group(1)

    # Pull file from device
    cmd = f"adb pull {device_file_path} {temp_file}"
    success, output = await run_command(cmd)
    
    if not success:
        error_msg = f"Could not pull dump file from device: {output}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)

    # Parse XML file
    try:
        tree = ET.parse(temp_file)
        root = tree.getroot()
        
        elements = []
        for elem in root.iter():
            package = elem.attrib.get('package', '')
            
            # Apply package filter if specified
            if filter_package and filter_package not in package:
                continue
                
            # Parse bounds if available
            bounds = elem.attrib.get('bounds', '')
            center_x, center_y, normalized_bounds = 0.5, 0.5, [0, 0, 1, 1]
            
            if bounds:
                try:
                    bounds = bounds.replace('][', ',').replace('[', '').replace(']', '')
                    coords = bounds.split(',')
                    if len(coords) == 4:
                        x1, y1, x2, y2 = map(int, coords)
                        # Normalize coordinates (assuming common screen size)
                        screen_w, screen_h = 1080, 1920
                        center_x = ((x1 + x2) / 2) / screen_w
                        center_y = ((y1 + y2) / 2) / screen_h
                        normalized_bounds = [x1/screen_w, y1/screen_h, x2/screen_w, y2/screen_h]
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse element boundaries: {bounds}, error: {str(e)}")
            
            element_data = {
                "uuid": f"xml_{len(elements)}",
                "name": elem.attrib.get('resource-id', '') or elem.attrib.get('text', '') or elem.attrib.get('class', ''),
                "text": elem.attrib.get('text', ''),
                "package": package,
                "resource_id": elem.attrib.get('resource-id', ''),
                "class_name": elem.attrib.get('class', ''),
                "clickable": elem.attrib.get('clickable', 'false').lower() == 'true',
                "center_x": center_x,
                "center_y": center_y,
                "bounds": normalized_bounds
            }
            
            elements.append(element_data)
        
        # Prepare initial UI data
        ui_data = {
            "status": "success",
            "total_count": len(elements),
            "elements": elements
        }
        
        # Auto-detect and close ads before returning to user
        ad_result = await auto_close_ads(ui_data, max_attempts=3)
        
        # Always use final UI data (whether ads were closed or not)
        final_ui = ad_result["final_ui_data"]
        
        # Add ad processing information
        if ad_result["ads_closed"] > 0:
            logger.info(f"Auto-closed {ad_result['ads_closed']} advertisements (XML fallback mode)")
            final_ui["ad_removal"] = {
                "ads_closed": ad_result["ads_closed"],
                "attempts": len(ad_result["attempts"]),
                "auto_processed": True,
                "mode": "xml_fallback"
            }
        
        # Add warning if ads still detected
        if ad_result.get("warning"):
            final_ui["ad_detection"] = {
                "warning": ad_result["warning"],
                "manual_action_needed": True,
                "mode": "xml_fallback"
            }
        
        return json.dumps(final_ui, indent=2)
        
    except ET.ParseError as e:
        error_msg = f"Failed to parse XML file: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)
    except Exception as e:
        error_msg = f"Error processing UI dump: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        }, indent=2)
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {str(e)}")


async def find_element_by_text(text: str, partial_match: bool = True) -> str:
    """Find UI element by text content.

    Args:
        text: Text to search for
        partial_match: If True, find elements containing the text. If False,
                      only exact matches are returned.

    Returns:
        str: JSON string with matching elements
    """
    # Try intelligent search first
    scheduler = _get_scheduler()
    if scheduler:
        try:
            result = await scheduler.find_elements_by_text(text, partial_match)
            
            # Clean up internal details for external LLM
            data = json.loads(result)
            if data.get("status") == "success":
                cleaned_elements = []
                for element in data.get("elements", []):
                    cleaned_element = {
                        "uuid": element.get("uuid"),
                        "name": element.get("name", ""),
                        "text": element.get("text", ""),
                        "package": element.get("package", ""),
                        "resource_id": element.get("resource_id", ""),
                        "class_name": element.get("class_name", ""),
                        "clickable": element.get("clickable", False),
                        "center_x": element.get("center_x", 0),
                        "center_y": element.get("center_y", 0),
                        "bounds": element.get("bounds", [])
                    }
                    cleaned_elements.append(cleaned_element)
                
                return json.dumps({
                    "status": "success",
                    "query": text,
                    "partial_match": partial_match,
                    "count": len(cleaned_elements),
                    "elements": cleaned_elements
                }, indent=2)
            else:
                return result
        except Exception as e:
            logger.warning(f"Intelligent search failed, using fallback: {e}")
    
    # Fallback to XML-based search
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response  # Return error from dump_ui

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_text = element.get("text", "")
            element_name = element.get("name", "")

            if partial_match:
                if text.lower() in element_text.lower() or text.lower() in element_name.lower():
                    matches.append(element)
            else:
                if element_text == text or element_name == text:
                    matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": text,
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


async def find_element_by_id(resource_id: str, package_name: Optional[str] = None) -> str:
    """Find UI element by resource ID.

    Args:
        resource_id: Resource ID to search for
        package_name: Package name to limit search to

    Returns:
        str: JSON string with matching elements
    """
    # Get UI dump with package filter
    dump_response = await dump_ui(filter_package=package_name)

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response  # Return error from dump_ui

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_id = element.get("resource_id", "")
            element_package = element.get("package", "")
            element_name = element.get("name", "")

            # Check if ID matches in resource_id or name, and package filter
            id_match = (resource_id in element_id or resource_id in element_name)
            package_match = (package_name is None or package_name in element_package)
            
            if id_match and package_match:
                matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": resource_id,
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


async def tap_element(element_json: str = None, uuid: str = None, bias: bool = False) -> str:
    """Tap on a UI element using either element JSON or UUID.

    Args:
        element_json: JSON representation of the element with bounds (legacy support)
        uuid: Element UUID for precise targeting (preferred method)
        bias: Apply bias correction for media content (auto-detected)

    Returns:
        str: Success or error message
    """
    try:
        # Prefer UUID-based targeting if available
        if uuid:
            scheduler = _get_scheduler()
            if scheduler:
                try:
                    result = await scheduler.tap_element_by_uuid(uuid, bias)
                    
                    # Clean up internal details for external LLM
                    data = json.loads(result)
                    if data.get("status") == "success":
                        return json.dumps({
                            "status": "success",
                            "message": f"Successfully tapped element {uuid}",
                            "uuid": uuid,
                            "bias_applied": data.get("bias_applied", bias)
                        }, indent=2)
                    else:
                        return result
                except Exception as e:
                    logger.warning(f"UUID-based tap failed, falling back to coordinate tap: {e}")
        
        # Legacy element_json support or fallback
        if not element_json:
            return json.dumps({
                "status": "error",
                "message": "Either element_json or uuid must be provided"
            })
        
        element = json.loads(element_json)
        
        # Try to get center coordinates directly
        center_x = element.get("center_x")
        center_y = element.get("center_y")
        
        if not center_x or not center_y:
            # Try to parse from bounds
            bounds = element.get("bounds", [])
            if len(bounds) >= 4:
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
            else:
                # Parse from legacy bounds string
                bounds_str = element.get("bounds", "")
                if bounds_str and isinstance(bounds_str, str):
                    bounds_match = re.match(r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", bounds_str)
                    if bounds_match:
                        x1, y1, x2, y2 = map(int, bounds_match.groups())
                        center_x = (x1 + x2) / 1080  # Normalize to screen width
                        center_y = (y1 + y2) / 1920  # Normalize to screen height

        if not center_x or not center_y:
            return json.dumps({
                "status": "error",
                "message": "Could not determine element coordinates"
            })

        # Convert normalized coordinates to actual screen coordinates
        actual_x = int(center_x * 1080) if center_x <= 1 else int(center_x)
        actual_y = int(center_y * 1920) if center_y <= 1 else int(center_y)
        
        # Apply bias correction if needed
        if bias:
            actual_y = max(0, actual_y - int(1920 * 0.02))  # Move up 2% of screen height

        # Perform tap using ADB
        success, output = await run_command(f"adb shell input tap {actual_x} {actual_y}")
        
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Successfully tapped at ({actual_x}, {actual_y})",
                "coordinates": {"x": actual_x, "y": actual_y},
                "bias_applied": bias
            }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": f"Tap failed: {output}"
            })

    except json.JSONDecodeError:
        return json.dumps({
            "status": "error",
            "message": "Invalid element JSON format"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error tapping element: {str(e)}"
        })