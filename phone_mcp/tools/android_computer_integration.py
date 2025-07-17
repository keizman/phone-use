"""
Android Computer Integration for Phone MCP
Integrates android_computer.py functionality into the MCP system
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from ..core import run_command
from .media import take_screenshot

logger = logging.getLogger("phone_mcp")


class AndroidComputerIntegration:
    """
    Integration wrapper for android_computer.py functionality
    Provides MCP-compatible interface for Android device control
    """
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id or ""
        self.screen_width = 1080
        self.screen_height = 1920
        self._initialize_screen_size()
    
    def _initialize_screen_size(self):
        """Initialize screen size from device"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                task = loop.create_task(self._get_screen_size_async())
                # Note: Can't await here since we're in __init__
                # Will be updated on first use
            else:
                # Create new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                width, height = loop.run_until_complete(self._get_screen_size_async())
                self.screen_width = width
                self.screen_height = height
                loop.close()
        except Exception as e:
            logger.warning(f"Failed to initialize screen size: {e}")
            # Use default values
            self.screen_width = 1080
            self.screen_height = 1920
    
    async def _get_screen_size_async(self) -> Tuple[int, int]:
        """Get screen size asynchronously"""
        try:
            success, output = await run_command("adb shell wm size")
            if success:
                import re
                match = re.search(r'(\d+)x(\d+)', output)
                if match:
                    return int(match.group(1)), int(match.group(2))
        except Exception as e:
            logger.error(f"Failed to get screen size: {e}")
        return 1080, 1920
    
    async def tap_coordinates(self, x: int, y: int) -> str:
        """
        Tap at specific coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            JSON string with tap result
        """
        try:
            success, output = await run_command(f"adb shell input tap {x} {y}")
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Tapped at coordinates ({x}, {y})",
                    "coordinates": {"x": x, "y": y}
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to tap at coordinates: {output}",
                    "coordinates": {"x": x, "y": y}
                })
        except Exception as e:
            logger.error(f"Tap coordinates failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Tap coordinates error: {str(e)}"
            })
    
    async def long_press_coordinates(self, x: int, y: int, duration_ms: int = 1000) -> str:
        """
        Long press at specific coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration_ms: Duration in milliseconds
            
        Returns:
            JSON string with long press result
        """
        try:
            success, output = await run_command(f"adb shell input swipe {x} {y} {x} {y} {duration_ms}")
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Long pressed at coordinates ({x}, {y}) for {duration_ms}ms",
                    "coordinates": {"x": x, "y": y},
                    "duration_ms": duration_ms
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to long press at coordinates: {output}",
                    "coordinates": {"x": x, "y": y}
                })
        except Exception as e:
            logger.error(f"Long press coordinates failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Long press coordinates error: {str(e)}"
            })
    
    async def double_tap_coordinates(self, x: int, y: int, interval_ms: int = 100) -> str:
        """
        Double tap at specific coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            interval_ms: Interval between taps in milliseconds
            
        Returns:
            JSON string with double tap result
        """
        try:
            # First tap
            success1, output1 = await run_command(f"adb shell input tap {x} {y}")
            if not success1:
                return json.dumps({
                    "status": "error",
                    "message": f"First tap failed: {output1}"
                })
            
            # Wait interval
            await asyncio.sleep(interval_ms / 1000.0)
            
            # Second tap
            success2, output2 = await run_command(f"adb shell input tap {x} {y}")
            if not success2:
                return json.dumps({
                    "status": "error",
                    "message": f"Second tap failed: {output2}"
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Double tapped at coordinates ({x}, {y}) with {interval_ms}ms interval",
                "coordinates": {"x": x, "y": y},
                "interval_ms": interval_ms
            })
        except Exception as e:
            logger.error(f"Double tap coordinates failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Double tap coordinates error: {str(e)}"
            })
    
    async def swipe_gesture(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
        """
        Perform swipe gesture
        
        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration_ms: Swipe duration in milliseconds
            
        Returns:
            JSON string with swipe result
        """
        try:
            success, output = await run_command(f"adb shell input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Swiped from ({x1}, {y1}) to ({x2}, {y2}) in {duration_ms}ms",
                    "start_coordinates": {"x": x1, "y": y1},
                    "end_coordinates": {"x": x2, "y": y2},
                    "duration_ms": duration_ms
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to swipe: {output}",
                    "start_coordinates": {"x": x1, "y": y1},
                    "end_coordinates": {"x": x2, "y": y2}
                })
        except Exception as e:
            logger.error(f"Swipe gesture failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Swipe gesture error: {str(e)}"
            })
    
    async def scroll_screen(self, direction: str = "down", distance: int = 500) -> str:
        """
        Scroll screen in specified direction
        
        Args:
            direction: "up", "down", "left", "right"
            distance: Scroll distance in pixels
            
        Returns:
            JSON string with scroll result
        """
        try:
            # Update screen size
            self.screen_width, self.screen_height = await self._get_screen_size_async()
            
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            
            if direction == "up":
                x1, y1 = center_x, center_y + distance // 2
                x2, y2 = center_x, center_y - distance // 2
            elif direction == "down":
                x1, y1 = center_x, center_y - distance // 2
                x2, y2 = center_x, center_y + distance // 2
            elif direction == "left":
                x1, y1 = center_x + distance // 2, center_y
                x2, y2 = center_x - distance // 2, center_y
            elif direction == "right":
                x1, y1 = center_x - distance // 2, center_y
                x2, y2 = center_x + distance // 2, center_y
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Invalid scroll direction: {direction}"
                })
            
            return await self.swipe_gesture(x1, y1, x2, y2, 300)
            
        except Exception as e:
            logger.error(f"Scroll screen failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Scroll screen error: {str(e)}"
            })
    
    async def press_key(self, key: str) -> str:
        """
        Press system key
        
        Args:
            key: Key name (back, home, recent_apps, etc.)
            
        Returns:
            JSON string with key press result
        """
        try:
            key_mapping = {
                "back": "KEYCODE_BACK",
                "home": "KEYCODE_HOME",
                "recent_apps": "KEYCODE_APP_SWITCH",
                "menu": "KEYCODE_MENU",
                "power": "KEYCODE_POWER",
                "volume_up": "KEYCODE_VOLUME_UP",
                "volume_down": "KEYCODE_VOLUME_DOWN",
                "enter": "KEYCODE_ENTER",
                "escape": "KEYCODE_ESCAPE"
            }
            
            keycode = key_mapping.get(key.lower(), key)
            
            success, output = await run_command(f"adb shell input keyevent {keycode}")
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Pressed key: {key}",
                    "key": key,
                    "keycode": keycode
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to press key: {output}",
                    "key": key
                })
        except Exception as e:
            logger.error(f"Press key failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Press key error: {str(e)}"
            })
    
    async def input_text(self, text: str) -> str:
        """
        Input text using ADB
        
        Args:
            text: Text to input
            
        Returns:
            JSON string with input result
        """
        try:
            # Escape special characters
            escaped_text = text.replace(' ', '%s').replace("'", "\\'")
            
            success, output = await run_command(f"adb shell input text '{escaped_text}'")
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": f"Input text: {text}",
                    "text": text
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to input text: {output}",
                    "text": text
                })
        except Exception as e:
            logger.error(f"Input text failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Input text error: {str(e)}"
            })
    
    async def take_screenshot_android(self) -> str:
        """
        Take screenshot using android_computer.py style
        
        Returns:
            JSON string with screenshot result
        """
        try:
            # Use existing screenshot function
            return await take_screenshot()
        except Exception as e:
            logger.error(f"Take screenshot failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Take screenshot error: {str(e)}"
            })
    
    async def get_screen_info(self) -> str:
        """
        Get screen information
        
        Returns:
            JSON string with screen information
        """
        try:
            self.screen_width, self.screen_height = await self._get_screen_size_async()
            
            return json.dumps({
                "status": "success",
                "message": "Screen information retrieved",
                "screen_size": {
                    "width": self.screen_width,
                    "height": self.screen_height
                },
                "center_point": {
                    "x": self.screen_width // 2,
                    "y": self.screen_height // 2
                }
            })
        except Exception as e:
            logger.error(f"Get screen info failed: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Get screen info error: {str(e)}"
            })


# Global instance
_android_computer = None


def get_android_computer(device_id: Optional[str] = None) -> AndroidComputerIntegration:
    """Get or create Android computer integration instance"""
    global _android_computer
    if _android_computer is None:
        _android_computer = AndroidComputerIntegration(device_id)
    return _android_computer


# MCP Tool Functions

async def android_tap_coordinates(x: int, y: int, device_id: Optional[str] = None) -> str:
    """
    Tap at specific coordinates using Android computer integration.
    
    Args:
        x: X coordinate to tap
        y: Y coordinate to tap
        device_id: Optional device ID
        
    Returns:
        JSON string with tap result
    """
    computer = get_android_computer(device_id)
    return await computer.tap_coordinates(x, y)


async def android_long_press_coordinates(x: int, y: int, duration_ms: int = 1000, device_id: Optional[str] = None) -> str:
    """
    Long press at specific coordinates using Android computer integration.
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration_ms: Duration in milliseconds (default: 1000)
        device_id: Optional device ID
        
    Returns:
        JSON string with long press result
    """
    computer = get_android_computer(device_id)
    return await computer.long_press_coordinates(x, y, duration_ms)


async def android_double_tap_coordinates(x: int, y: int, interval_ms: int = 100, device_id: Optional[str] = None) -> str:
    """
    Double tap at specific coordinates using Android computer integration.
    
    Args:
        x: X coordinate
        y: Y coordinate
        interval_ms: Interval between taps in milliseconds (default: 100)
        device_id: Optional device ID
        
    Returns:
        JSON string with double tap result
    """
    computer = get_android_computer(device_id)
    return await computer.double_tap_coordinates(x, y, interval_ms)


async def android_swipe_gesture(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, device_id: Optional[str] = None) -> str:
    """
    Perform swipe gesture using Android computer integration.
    
    Args:
        x1: Start X coordinate
        y1: Start Y coordinate
        x2: End X coordinate
        y2: End Y coordinate
        duration_ms: Swipe duration in milliseconds (default: 300)
        device_id: Optional device ID
        
    Returns:
        JSON string with swipe result
    """
    computer = get_android_computer(device_id)
    return await computer.swipe_gesture(x1, y1, x2, y2, duration_ms)


async def android_scroll_screen(direction: str = "down", distance: int = 500, device_id: Optional[str] = None) -> str:
    """
    Scroll screen in specified direction using Android computer integration.
    
    Args:
        direction: Scroll direction ("up", "down", "left", "right")
        distance: Scroll distance in pixels (default: 500)
        device_id: Optional device ID
        
    Returns:
        JSON string with scroll result
    """
    computer = get_android_computer(device_id)
    return await computer.scroll_screen(direction, distance)


async def android_press_key(key: str, device_id: Optional[str] = None) -> str:
    """
    Press system key using Android computer integration.
    
    Args:
        key: Key name (back, home, recent_apps, menu, power, volume_up, volume_down, enter, escape)
        device_id: Optional device ID
        
    Returns:
        JSON string with key press result
    """
    computer = get_android_computer(device_id)
    return await computer.press_key(key)


async def android_input_text(text: str, device_id: Optional[str] = None) -> str:
    """
    Input text using Android computer integration.
    
    Args:
        text: Text to input
        device_id: Optional device ID
        
    Returns:
        JSON string with input result
    """
    computer = get_android_computer(device_id)
    return await computer.input_text(text)


async def android_get_screen_info(device_id: Optional[str] = None) -> str:
    """
    Get screen information using Android computer integration.
    
    Args:
        device_id: Optional device ID
        
    Returns:
        JSON string with screen information
    """
    computer = get_android_computer(device_id)
    return await computer.get_screen_info()