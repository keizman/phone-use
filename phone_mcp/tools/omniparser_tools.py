"""
MCP Tools for Omniparser Integration
Provides MCP-compatible tool functions for visual UI element recognition and interaction
"""

import json
import logging
from typing import Dict, Any, Optional

from .omniparser_interface import (
    get_omniparser_client,
    get_screen_analyzer,
    get_interaction_manager
)
from ..core import run_command

logger = logging.getLogger("phone_mcp")


async def omniparser_analyze_screen(
    server_url: str = "http://100.122.57.128:9333",
    use_paddleocr: Optional[bool] = None,
    use_cache: bool = True
) -> str:
    """
    Analyze current screen using Omniparser for visual element recognition.
    
    This function captures a screenshot and uses Omniparser to identify UI elements with precise
    bounding boxes and content recognition. Each element gets a unique UUID for interaction.
    
    Args:
        server_url: Omniparser server URL (default: http://100.122.57.128:9333)
        use_paddleocr: True for PaddleOCR (all text), False for YOLO only (icons), None for server default
        use_cache: Whether to use cached analysis results (default: True)
        
    Returns:
        JSON string with analysis results containing:
        - status: "success" or "error"
        - message: Status message
        - elements: List of UI elements with UUID, type, bbox, content, interactivity
        - element_count: Total number of elements found
        - interactive_count: Number of interactive elements
        - text_count: Number of text elements
        - icon_count: Number of icon elements
        - screen_size: Screen dimensions
        - latency: Processing time
        
    Example:
        {
            "status": "success",
            "elements": [
                {
                    "uuid": "abc123",
                    "type": "text",
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                    "content": "Settings",
                    "interactivity": false,
                    "center_x": 0.2,
                    "center_y": 0.3
                }
            ],
            "element_count": 25,
            "interactive_count": 8
        }
    """
    try:
        # Get screen analyzer
        analyzer = get_screen_analyzer(server_url)
        
        # Check server health first
        if not await analyzer.client.health_check():
            return json.dumps({
                "status": "error",
                "message": f"Omniparser server at {server_url} is not available"
            })
        
        # Perform analysis
        result = await analyzer.capture_and_analyze_screen(
            use_paddleocr=use_paddleocr,
            use_cache=use_cache
        )
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Omniparser screen analysis failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to analyze screen: {str(e)}"
        })


async def omniparser_find_elements_by_content(
    content: str,
    partial_match: bool = True,
    server_url: str = "http://100.122.57.128:9333"
) -> str:
    """
    Find UI elements by content text using Omniparser.
    
    Args:
        content: Text content to search for
        partial_match: Whether to allow partial matches (default: True)
        server_url: Omniparser server URL
        
    Returns:
        JSON string with matching elements
    """
    try:
        analyzer = get_screen_analyzer(server_url)
        
        # Check server health
        if not await analyzer.client.health_check():
            return json.dumps({
                "status": "error",
                "message": f"Omniparser server at {server_url} is not available"
            })
        
        # Find elements
        elements = await analyzer.find_elements_by_content(content, partial_match)
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(elements)} elements matching '{content}'",
            "search_term": content,
            "partial_match": partial_match,
            "elements": [elem.to_dict() for elem in elements],
            "count": len(elements)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Element search failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to find elements: {str(e)}"
        })


async def omniparser_find_interactive_elements(
    server_url: str = "http://100.122.57.128:9333"
) -> str:
    """
    Find all interactive UI elements using Omniparser.
    
    Args:
        server_url: Omniparser server URL
        
    Returns:
        JSON string with interactive elements
    """
    try:
        analyzer = get_screen_analyzer(server_url)
        
        # Check server health
        if not await analyzer.client.health_check():
            return json.dumps({
                "status": "error",
                "message": f"Omniparser server at {server_url} is not available"
            })
        
        # Find interactive elements
        elements = await analyzer.find_interactive_elements()
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(elements)} interactive elements",
            "elements": [elem.to_dict() for elem in elements],
            "count": len(elements)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Interactive element search failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to find interactive elements: {str(e)}"
        })


async def omniparser_tap_element_by_uuid(
    uuid: str,
    bias: bool = False,
    server_url: str = "http://100.122.57.128:9333"
) -> str:
    """
    Tap UI element by UUID using Omniparser-identified coordinates.
    
    This function locates an element by its UUID (from previous analysis) and taps it at the
    calculated center coordinates with optional bias correction for program/video content.
    
    Args:
        uuid: Unique identifier of the element to tap
        bias: If True, apply upward bias correction for program/video content (default: False)
        server_url: Omniparser server URL
        
    Returns:
        JSON string with tap result
        
    Example:
        {
            "status": "success",
            "message": "Tapped element abc123 at (540, 960) (with bias correction)",
            "element": {
                "uuid": "abc123",
                "content": "四宫格视频",
                "type": "text"
            },
            "bias_applied": true
        }
        
    Note:
        Use bias=True when tapping on program/video content where the element name 
        appears below the actual clickable area. This is common in media applications 
        where the program title is displayed under the video thumbnail.
    """
    try:
        manager = get_interaction_manager(server_url)
        
        # Check server health
        if not await manager.analyzer.client.health_check():
            return json.dumps({
                "status": "error",
                "message": f"Omniparser server at {server_url} is not available"
            })
        
        # Tap element with bias correction
        result = await manager.tap_element_by_uuid(uuid, bias)
        
        return result
        
    except Exception as e:
        logger.error(f"Element tap failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to tap element: {str(e)}"
        })


async def omniparser_get_element_info(
    uuid: str,
    server_url: str = "http://100.122.57.128:9333"
) -> str:
    """
    Get detailed information about a UI element by UUID.
    
    Args:
        uuid: Unique identifier of the element
        server_url: Omniparser server URL
        
    Returns:
        JSON string with element information
    """
    try:
        manager = get_interaction_manager(server_url)
        
        # Check server health
        if not await manager.analyzer.client.health_check():
            return json.dumps({
                "status": "error",
                "message": f"Omniparser server at {server_url} is not available"
            })
        
        # Get element info
        result = await manager.get_element_info(uuid)
        
        return result
        
    except Exception as e:
        logger.error(f"Get element info failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get element info: {str(e)}"
        })


async def omniparser_get_current_focus_pkg_name() -> str:
    """
    Get the current focused package name using ADB.
    
    Returns:
        JSON string with current package name
    """
    try:
        # Get current activity
        success, output = await run_command("adb shell dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")
        
        if success:
            # Extract package name from output
            lines = output.strip().split('\n')
            for line in lines:
                if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                    # Extract package name from format like "com.android.settings/..."
                    parts = line.split()
                    for part in parts:
                        if '/' in part and '.' in part:
                            pkg_name = part.split('/')[0]
                            return json.dumps({
                                "status": "success",
                                "package_name": pkg_name,
                                "full_line": line.strip()
                            })
        
        return json.dumps({
            "status": "error",
            "message": "Could not determine current focus package"
        })
        
    except Exception as e:
        logger.error(f"Get focus package failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get focus package: {str(e)}"
        })


async def omniparser_clear_cache_and_restart(package_name: str) -> str:
    """
    Clear app cache and restart application.
    
    Args:
        package_name: Package name of the app to clear and restart
        
    Returns:
        JSON string with operation result
    """
    try:
        # Stop the app first
        stop_success, stop_output = await run_command(f"adb shell am force-stop {package_name}")
        
        if not stop_success:
            return json.dumps({
                "status": "error",
                "message": f"Failed to stop app: {stop_output}"
            })
        
        # Clear app cache
        clear_success, clear_output = await run_command(f"adb shell pm clear {package_name}")
        
        if not clear_success:
            return json.dumps({
                "status": "error",
                "message": f"Failed to clear cache: {clear_output}"
            })
        
        # Start the app again
        start_success, start_output = await run_command(f"adb shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
        
        if not start_success:
            return json.dumps({
                "status": "error",
                "message": f"Failed to restart app: {start_output}"
            })
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully cleared cache and restarted {package_name}",
            "operations": {
                "stop": stop_output,
                "clear": clear_output,
                "restart": start_output
            }
        })
        
    except Exception as e:
        logger.error(f"Clear cache and restart failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to clear cache and restart: {str(e)}"
        })


async def omniparser_get_screen_state() -> str:
    """
    Get comprehensive screen state information using Omniparser.
    
    This function provides a complete overview of the current screen state including:
    - Current focus package
    - All UI elements with UUIDs
    - Interactive elements summary
    - Screen positioning information
    
    Returns:
        JSON string with complete screen state
    """
    try:
        # Get current focus package
        focus_result = await omniparser_get_current_focus_pkg_name()
        focus_data = json.loads(focus_result)
        
        # Get screen analysis
        analysis_result = await omniparser_analyze_screen(use_paddleocr=True)
        analysis_data = json.loads(analysis_result)
        
        # Get interactive elements
        interactive_result = await omniparser_find_interactive_elements()
        interactive_data = json.loads(interactive_result)
        
        if analysis_data.get("status") == "success":
            return json.dumps({
                "status": "success",
                "message": "Screen state retrieved successfully",
                "focus_package": focus_data.get("package_name", "unknown"),
                "screen_analysis": analysis_data,
                "interactive_elements": interactive_data.get("elements", []),
                "summary": {
                    "total_elements": analysis_data.get("element_count", 0),
                    "interactive_count": analysis_data.get("interactive_count", 0),
                    "text_count": analysis_data.get("text_count", 0),
                    "icon_count": analysis_data.get("icon_count", 0),
                    "screen_size": analysis_data.get("screen_size", {}),
                    "has_focus_package": focus_data.get("status") == "success"
                }
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "Failed to get screen state",
                "focus_package": focus_data.get("package_name", "unknown"),
                "error_details": analysis_data.get("message", "Unknown error")
            })
        
    except Exception as e:
        logger.error(f"Get screen state failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get screen state: {str(e)}"
        })


async def omniparser_execute_action_by_uuid(
    uuid: str,
    action: str = "tap",
    bias: bool = False,
    server_url: str = "http://100.122.57.128:9333"
) -> str:
    """
    Execute action on UI element by UUID with optional bias correction.
    
    Args:
        uuid: Unique identifier of the element
        action: Action to perform ("tap", "long_press", "double_tap")
        bias: If True, apply upward bias correction for program/video content
        server_url: Omniparser server URL
        
    Returns:
        JSON string with action result
        
    Note:
        Use bias=True when interacting with program/video content where element names
        appear below the actual clickable area.
    """
    try:
        if action == "tap":
            return await omniparser_tap_element_by_uuid(uuid, bias, server_url)
        elif action == "long_press":
            # For long press, we need to get coordinates and perform long press
            manager = get_interaction_manager(server_url)
            element = await manager.find_element_by_uuid(uuid)
            
            if not element:
                return json.dumps({
                    "status": "error",
                    "message": f"Element with UUID {uuid} not found"
                })
            
            # Get screen coordinates with bias correction
            screen_width = manager.last_analysis.get("screen_size", {}).get("width", 1080)
            screen_height = manager.last_analysis.get("screen_size", {}).get("height", 1920)
            x, y = element.get_screen_coordinates(screen_width, screen_height, bias)
            
            # Perform long press using swipe with same start/end coordinates
            from .interactions import swipe_screen
            result = await swipe_screen(x, y, x, y, 1000)  # 1 second duration
            
            bias_info = " (with bias correction)" if bias else ""
            
            return json.dumps({
                "status": "success",
                "message": f"Long pressed element {uuid} at ({x}, {y}){bias_info}",
                "element": element.to_dict(),
                "bias_applied": bias,
                "action_result": result
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unsupported action: {action}"
            })
        
    except Exception as e:
        logger.error(f"Execute action failed: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to execute action: {str(e)}"
        })