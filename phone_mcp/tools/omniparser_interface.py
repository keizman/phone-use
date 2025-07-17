"""
Omniparser Interface Module for Phone MCP
Provides integration with Omniparser server for visual UI element recognition
"""

import asyncio
import base64
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field

import requests
from PIL import Image
import tempfile
import os

from ..core import run_command
from .media import take_screenshot
from .interactions import tap_screen, swipe_screen

logger = logging.getLogger("phone_mcp")


class ParseRequest(BaseModel):
    """Request model for Omniparser server communication"""
    base64_image: str = Field(..., description="Base64 encoded image data")
    use_paddleocr: Optional[bool] = Field(
        None, 
        description="True=PaddleOCR (all text elements), False=YOLO only (icons), None=server default"
    )


@dataclass
class OmniElement:
    """Represents a UI element identified by Omniparser"""
    uuid: str
    type: str  # "text", "icon", etc.
    bbox: List[float]  # [x1, y1, x2, y2] in normalized coordinates
    interactivity: bool
    content: str
    source: str
    
    @property
    def center_x(self) -> float:
        """Get center X coordinate (normalized)"""
        return (self.bbox[0] + self.bbox[2]) / 2
    
    @property
    def center_y(self) -> float:
        """Get center Y coordinate (normalized)"""
        return (self.bbox[1] + self.bbox[3]) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "uuid": self.uuid,
            "type": self.type,
            "bbox": self.bbox,
            "interactivity": self.interactivity,
            "content": self.content,
            "source": self.source,
            "center_x": self.center_x,
            "center_y": self.center_y
        }
    
    def get_screen_coordinates(self, screen_width: int, screen_height: int, bias: bool = False) -> Tuple[int, int]:
        """Convert normalized coordinates to actual screen coordinates
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            bias: If True, apply upward bias for program/video content (default: False)
        
        Returns:
            Tuple of (x, y) coordinates in pixels
        """
        x = int(self.center_x * screen_width)
        y = int(self.center_y * screen_height)
        
        # Apply bias correction for program/video content
        if bias:
            # Calculate bias as approximately 1cm upward
            # Assuming standard phone DPI of ~400, 1cm ≈ 40 pixels
            bias_pixels = int(screen_height * 0.02)  # 2% of screen height as bias
            y = max(0, y - bias_pixels)  # Ensure y doesn't go below 0
        
        return x, y


class OmniparserClient:
    """Client for communicating with Omniparser server"""
    
    def __init__(self, server_url: str = "http://100.122.57.128:9333"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
    
    async def parse_screen(self, base64_image: str, use_paddleocr: Optional[bool] = None) -> Dict[str, Any]:
        """Parse screen image using Omniparser server"""
        try:
            parse_request = ParseRequest(
                base64_image=base64_image,
                use_paddleocr=use_paddleocr
            )
            
            parse_url = f"{self.server_url}/parse/"
            
            payload = parse_request.dict(exclude_none=True)
            
            logger.info(f"Sending parse request to {parse_url}")
            
            response = self.session.post(
                parse_url,
                json=payload,
                timeout=90
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Omniparser request failed: {e}")
            raise Exception(f"Failed to parse screen: {str(e)}")
        except Exception as e:
            logger.error(f"Omniparser parsing error: {e}")
            raise Exception(f"Omniparser error: {str(e)}")
    
    async def parse_screen_file(self, image_path: str, use_paddleocr: Optional[bool] = None) -> Dict[str, Any]:
        """Parse screen image file using Omniparser server"""
        try:
            parse_url = f"{self.server_url}/parse/file/"
            
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                
                # Add use_paddleocr parameter if specified
                data = {}
                if use_paddleocr is not None:
                    data['use_paddleocr'] = use_paddleocr
                
                response = self.session.post(
                    parse_url,
                    files=files,
                    data=data,
                    timeout=120
                )
                
                response.raise_for_status()
                return response.json()
                
        except requests.RequestException as e:
            logger.error(f"Omniparser file request failed: {e}")
            raise Exception(f"Failed to parse screen file: {str(e)}")
        except Exception as e:
            logger.error(f"Omniparser file parsing error: {e}")
            raise Exception(f"Omniparser file error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Omniparser server is healthy"""
        try:
            probe_url = f"{self.server_url}/probe/"
            response = self.session.get(probe_url, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Omniparser health check failed: {e}")
            return False


class OmniparserScreenAnalyzer:
    """Enhanced screen analyzer using Omniparser for visual element recognition"""
    
    def __init__(self, omniparser_client: OmniparserClient):
        self.client = omniparser_client
        self._screen_cache = {}
        self._cache_timeout = 5.0  # Cache for 5 seconds
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions using ADB"""
        try:
            success, output = await run_command("adb shell wm size")
            if success:
                match = re.search(r'(\d+)x(\d+)', output)
                if match:
                    return int(match.group(1)), int(match.group(2))
            return 1080, 1920  # Default fallback
        except Exception:
            return 1080, 1920
    
    async def capture_and_analyze_screen(self, 
                                       use_paddleocr: Optional[bool] = None,
                                       use_cache: bool = True) -> Dict[str, Any]:
        """Capture screenshot and analyze using Omniparser"""
        try:
            # Check cache first
            cache_key = f"screen_analysis_{use_paddleocr}"
            current_time = time.time()
            
            if use_cache and cache_key in self._screen_cache:
                cached_data, timestamp = self._screen_cache[cache_key]
                if current_time - timestamp < self._cache_timeout:
                    logger.info("Using cached screen analysis")
                    return cached_data
            
            # Take screenshot
            screenshot_result = await take_screenshot()
            screenshot_data = json.loads(screenshot_result)
            
            if screenshot_data.get("status") != "success":
                raise Exception(f"Failed to take screenshot: {screenshot_data.get('message', 'Unknown error')}")
            
            base64_image = screenshot_data.get("data", "")
            if not base64_image:
                raise Exception("No image data in screenshot result")
            
            # Parse with Omniparser
            parse_result = await self.client.parse_screen(base64_image, use_paddleocr)
            
            # Get screen dimensions
            screen_width, screen_height = await self.get_screen_size()
            
            # Process elements
            elements = []
            parsed_content = parse_result.get("parsed_content_list", [])
            
            for item in parsed_content:
                element = OmniElement(
                    uuid=item.get("uuid", ""),
                    type=item.get("type", ""),
                    bbox=item.get("bbox", []),
                    interactivity=item.get("interactivity", False),
                    content=item.get("content", ""),
                    source=item.get("source", "")
                )
                elements.append(element)
            
            result = {
                "status": "success",
                "message": "Screen analyzed successfully with Omniparser",
                "timestamp": current_time,
                "screen_size": {"width": screen_width, "height": screen_height},
                "elements": [elem.to_dict() for elem in elements],
                "element_count": len(elements),
                "interactive_count": len([e for e in elements if e.interactivity]),
                "text_count": len([e for e in elements if e.type == "text"]),
                "icon_count": len([e for e in elements if e.type == "icon"]),
                "latency": parse_result.get("latency", 0),
                "raw_omniparser_result": parse_result
            }
            
            # Cache the result
            if use_cache:
                self._screen_cache[cache_key] = (result, current_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to analyze screen: {str(e)}",
                "timestamp": time.time()
            }
    
    async def find_elements_by_content(self, content: str, partial_match: bool = True) -> List[OmniElement]:
        """Find elements by content text"""
        try:
            analysis_result = await self.capture_and_analyze_screen()
            if analysis_result.get("status") != "success":
                return []
            
            elements = []
            for elem_data in analysis_result.get("elements", []):
                element = OmniElement(
                    uuid=elem_data["uuid"],
                    type=elem_data["type"],
                    bbox=elem_data["bbox"],
                    interactivity=elem_data["interactivity"],
                    content=elem_data["content"],
                    source=elem_data["source"]
                )
                
                if partial_match:
                    if content.lower() in element.content.lower():
                        elements.append(element)
                else:
                    if element.content.lower() == content.lower():
                        elements.append(element)
            
            return elements
            
        except Exception as e:
            logger.error(f"Error finding elements by content: {e}")
            return []
    
    async def find_interactive_elements(self) -> List[OmniElement]:
        """Find all interactive elements"""
        try:
            analysis_result = await self.capture_and_analyze_screen()
            if analysis_result.get("status") != "success":
                return []
            
            elements = []
            for elem_data in analysis_result.get("elements", []):
                if 1: # set for all ele is activable elem_data["interactivity"]:
                    element = OmniElement(
                        uuid=elem_data["uuid"],
                        type=elem_data["type"],
                        bbox=elem_data["bbox"],
                        interactivity=elem_data["interactivity"],
                        content=elem_data["content"],
                        source=elem_data["source"]
                    )
                    elements.append(element)
            
            return elements
            
        except Exception as e:
            logger.error(f"Error finding interactive elements: {e}")
            return []


class OmniparserInteractionManager:
    """Manager for UUID-based element interactions"""
    
    def __init__(self, analyzer: OmniparserScreenAnalyzer):
        self.analyzer = analyzer
        self.last_analysis = None
        self.last_analysis_time = 0
    
    async def refresh_analysis(self, force: bool = False) -> bool:
        """Refresh screen analysis if needed"""
        current_time = time.time()
        if force or not self.last_analysis or (current_time - self.last_analysis_time) > 3.0:
            self.last_analysis = await self.analyzer.capture_and_analyze_screen()
            self.last_analysis_time = current_time
            return self.last_analysis.get("status") == "success"
        return self.last_analysis.get("status") == "success"
    
    async def find_element_by_uuid(self, uuid: str) -> Optional[OmniElement]:
        """Find element by UUID"""
        try:
            await self.refresh_analysis()
            
            if not self.last_analysis or self.last_analysis.get("status") != "success":
                return None
            
            for elem_data in self.last_analysis.get("elements", []):
                if elem_data["uuid"] == uuid:
                    return OmniElement(
                        uuid=elem_data["uuid"],
                        type=elem_data["type"],
                        bbox=elem_data["bbox"],
                        interactivity=elem_data["interactivity"],
                        content=elem_data["content"],
                        source=elem_data["source"]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding element by UUID: {e}")
            return None
    
    async def tap_element_by_uuid(self, uuid: str, bias: bool = False) -> str:
        """Tap element by UUID with optional bias correction
        
        Args:
            uuid: Element UUID to tap
            bias: If True, apply upward bias for program/video content
        """
        try:
            element = await self.find_element_by_uuid(uuid)
            if not element:
                return json.dumps({
                    "status": "error",
                    "message": f"Element with UUID {uuid} not found"
                })
            
            if not element.interactivity:
                return json.dumps({
                    "status": "warning",
                    "message": f"Element {uuid} is not marked as interactive, tapping anyway"
                })
            
            # Get screen coordinates
            screen_width = self.last_analysis.get("screen_size", {}).get("width", 1080)
            screen_height = self.last_analysis.get("screen_size", {}).get("height", 1920)
            
            x, y = element.get_screen_coordinates(screen_width, screen_height, bias)
            
            # Perform tap
            tap_result = await tap_screen(x, y)
            
            bias_info = " (with bias correction)" if bias else ""
            
            return json.dumps({
                "status": "success",
                "message": f"Tapped element {uuid} at ({x}, {y}){bias_info}",
                "element": element.to_dict(),
                "bias_applied": bias,
                "tap_result": tap_result
            })
            
        except Exception as e:
            logger.error(f"Error tapping element by UUID: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to tap element {uuid}: {str(e)}"
            })
    
    async def get_element_info(self, uuid: str) -> str:
        """Get detailed information about an element"""
        try:
            element = await self.find_element_by_uuid(uuid)
            if not element:
                return json.dumps({
                    "status": "error",
                    "message": f"Element with UUID {uuid} not found"
                })
            
            screen_width = self.last_analysis.get("screen_size", {}).get("width", 1080)
            screen_height = self.last_analysis.get("screen_size", {}).get("height", 1920)
            
            x, y = element.get_screen_coordinates(screen_width, screen_height)
            
            return json.dumps({
                "status": "success",
                "element": element.to_dict(),
                "screen_coordinates": {"x": x, "y": y},
                "screen_size": {"width": screen_width, "height": screen_height}
            })
            
        except Exception as e:
            logger.error(f"Error getting element info: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to get element info: {str(e)}"
            })


# Global instances
_omniparser_client = None
_screen_analyzer = None
_interaction_manager = None


def get_omniparser_client(server_url: str = "http://100.122.57.128:9333") -> OmniparserClient:
    """Get or create Omniparser client instance"""
    global _omniparser_client
    if _omniparser_client is None:
        _omniparser_client = OmniparserClient(server_url)
    return _omniparser_client


def get_screen_analyzer(server_url: str = "http://100.122.57.128:9333") -> OmniparserScreenAnalyzer:
    """Get or create screen analyzer instance"""
    global _screen_analyzer
    if _screen_analyzer is None:
        client = get_omniparser_client(server_url)
        _screen_analyzer = OmniparserScreenAnalyzer(client)
    return _screen_analyzer


def get_interaction_manager(server_url: str = "http://100.122.57.128:9333") -> OmniparserInteractionManager:
    """Get or create interaction manager instance"""
    global _interaction_manager
    if _interaction_manager is None:
        analyzer = get_screen_analyzer(server_url)
        _interaction_manager = OmniparserInteractionManager(analyzer)
    return _interaction_manager