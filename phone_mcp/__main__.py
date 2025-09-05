#!/usr/bin/env python3
"""
Phone MCP Server - Android Device Control via MCP Protocol
"""
import asyncio
import sys
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phone_mcp")

# Create server instance
server = Server("phone_mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available phone MCP tools"""
    tools = [
        # ★HIGHEST PRIORITY - Unified UI Tools
        Tool(
            name="dump_ui",
            description="★INTELLIGENT SCREEN ANALYSIS - Analyze current screen with automatic method selection (Omniparser visual + XML fallback)",
            inputSchema={
                "type": "object",
                "properties": {
                    "use_omniparser": {"type": "boolean", "description": "Force use of Omniparser visual analysis"},
                    "use_cache": {"type": "boolean", "description": "Use cached analysis if available"}
                },
                "required": []
            }
        ),
        Tool(
            name="find_element_by_text",
            description="★SMART TEXT SEARCH - Find UI elements by text content with intelligent matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to search for"},
                    "partial_match": {"type": "boolean", "description": "Allow partial text matching"}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="find_element_by_id",
            description="RESOURCE ID SEARCH - Find UI elements by resource ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {"type": "string", "description": "Android resource ID to search for"}
                },
                "required": ["resource_id"]
            }
        ),
        Tool(
            name="tap_element",
            description="★INTELLIGENT ELEMENT TAP - Tap UI elements with support for UUID, coordinates, and bias correction",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {"type": "string", "description": "UUID of element from Omniparser"},
                    "x": {"type": "number", "description": "X coordinate"},
                    "y": {"type": "number", "description": "Y coordinate"},
                    "bias_correction": {"type": "object", "description": "Bias correction parameters"}
                },
                "required": []
            }
        ),
        
        # CORE PROFESSIONAL TOOLS
        Tool(
            name="omniparser_analyze_screen",
            description="PRIMARY VISUAL ANALYSIS - Advanced computer vision screen analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_url": {"type": "string", "description": "Omniparser server URL"},
                    "use_paddleocr": {"type": "boolean", "description": "Use PaddleOCR for text recognition"}
                },
                "required": []
            }
        ),
        Tool(
            name="omniparser_tap_element_by_uuid",
            description="PRECISION INTERACTION - Tap elements using Omniparser UUID",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {"type": "string", "description": "UUID from Omniparser analysis"}
                },
                "required": ["uuid"]
            }
        ),
        
        # COMMON FUNCTION TOOLS
        Tool(
            name="phone_screen_interact",
            description="UNIFIED SCREEN INTERACTION - Comprehensive screen interaction capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action to perform (tap, swipe, scroll, etc.)"},
                    "parameters": {"type": "object", "description": "Action parameters (optional)"},
                    "target": {"type": "string", "description": "Element to interact with"},
                    "coordinates": {"type": "string", "description": "Direct coordinates as 'x,y'"},
                    "text": {"type": "string", "description": "Text to input (for input_text action)"},
                    "use_omniparser": {"type": "boolean", "description": "Use visual element recognition"},
                    "delay_seconds": {"type": "number", "description": "Delay after action in seconds"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="phone_app_control",
            description="★★ APP MANAGEMENT - Control Android applications",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "App action (start, stop, install, etc.)"},
                    "package_name": {"type": "string", "description": "Android package name"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="phone_system_control",
            description="★★ SYSTEM CONTROL - Android system operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "System action"},
                    "parameters": {"type": "object", "description": "Action parameters"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="get_usage_examples", 
            description="USAGE GUIDANCE - Get usage examples and tool call chains for common tasks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with proper error handling"""
    try:
        logger.info(f"Calling tool: {name} with args: {arguments}")
        
        # Import tools dynamically to avoid startup issues
        if name == "dump_ui":
            from .tools.ui import dump_ui
            result = await dump_ui(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "find_element_by_text":
            from .tools.ui import find_element_by_text
            result = await find_element_by_text(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "find_element_by_id":
            from .tools.ui import find_element_by_id
            result = await find_element_by_id(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "tap_element":
            from .tools.ui import tap_element
            result = await tap_element(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "omniparser_analyze_screen":
            from .tools.omniparser_tools import omniparser_analyze_screen
            result = await omniparser_analyze_screen(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "omniparser_tap_element_by_uuid":
            from .tools.omniparser_tools import omniparser_tap_element_by_uuid
            result = await omniparser_tap_element_by_uuid(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "phone_screen_interact":
            from .tools.unified_tools import phone_screen_interact
            result = await phone_screen_interact(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "phone_app_control":
            from .tools.unified_tools import phone_app_control
            result = await phone_app_control(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "phone_system_control":
            from .tools.unified_tools import phone_system_control
            result = await phone_system_control(**arguments)
            return [TextContent(type="text", text=result)]
            
        elif name == "get_usage_examples":
            from .tools.prompt_engineering import get_usage_examples
            result = await get_usage_examples(**arguments)
            return [TextContent(type="text", text=result)]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except ImportError as e:
        error_msg = f"Failed to import tool {name}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]

async def main():
    """Run the MCP server with stdio transport"""
    try:
        logger.info("🎯 Starting Phone MCP Server with Unified UI Interface")
        
        # Run the server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())