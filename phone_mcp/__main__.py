import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("phone_call")

# Import all tools
from .core import check_device_connection
from .tools.call import call_number, end_call, receive_incoming_call
from .tools.messaging import send_text_message, receive_text_messages
from .tools.media import take_screenshot, start_screen_recording, play_media
from .tools.apps import open_app, set_alarm
from .tools.contacts import get_contacts
from .tools.system import get_current_window, get_app_shortcuts, launch_activity

# Register all tools with MCP
mcp.tool()(call_number)
mcp.tool()(end_call)
mcp.tool()(check_device_connection)
mcp.tool()(send_text_message)
mcp.tool()(receive_text_messages)
mcp.tool()(take_screenshot)
mcp.tool()(start_screen_recording)
mcp.tool()(play_media)
mcp.tool()(open_app)
mcp.tool()(set_alarm)
mcp.tool()(receive_incoming_call)
mcp.tool()(get_contacts)
mcp.tool()(get_current_window)
mcp.tool()(get_app_shortcuts)
mcp.tool()(launch_activity)


def main():
    """Run the MCP server."""
    mcp.run(transport='stdio')


if __name__ == "__main__":
    # Initialize and run the server
    main()
