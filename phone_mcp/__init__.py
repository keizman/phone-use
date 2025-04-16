"""Phone MCP plugin package."""

from .__main__ import mcp, main
from .cli import main as cli_main

__version__ = "0.2.1"
__all__ = ["mcp", "main", "cli_main"]
