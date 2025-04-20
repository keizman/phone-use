"""Phone MCP plugin package."""

from .__main__ import mcp, main
from .cli import main as cli_main

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("phone-mcp")
except ImportError:
    __version__ = "0.0.0"  # fallback
__all__ = ["mcp", "main", "cli_main"]
