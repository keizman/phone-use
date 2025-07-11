# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests with pytest
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_phone_functionality.py

# Run tests with asyncio mode (already configured in pytest.ini)
pytest tests/test_phone_mcp.py
```

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Run the MCP server directly
python -m phone_mcp

# Run the CLI tool
phone-cli check
```

### Package Build
```bash
# Build wheel package
python setup.py bdist_wheel

# Build source distribution
python setup.py sdist
```

## Architecture Overview

This is a **phone-mcp** plugin that provides MCP (Model Context Protocol) integration for controlling Android devices via ADB commands. The project enables AI assistants to interact with Android phones through a structured API.

### Core Components

**Main Entry Points:**
- `phone_mcp/__main__.py` - MCP server entry point
- `phone_mcp/cli.py` - Command-line interface
- `phone_mcp/core.py` - Core ADB command execution and device connection logic

**Tool Modules (phone_mcp/tools/):**
- `call.py` - Phone call management (make calls, hang up, answer calls)
- `messaging.py` - SMS functionality (send/receive messages)
- `contacts.py` - Contact management with UI automation
- `apps.py` - App launching and management
- `media.py` - Screenshots, screen recording
- `screen_interface.py` - Screen interaction and analysis
- `ui.py` - Basic UI interactions (tap, swipe, input)
- `ui_enhanced.py` - Advanced UI element finding and interaction
- `ui_monitor.py` - UI change monitoring and automation
- `system.py` - System information and device management
- `maps.py` - Location-based services and POI search
- `interactions.py` - Unified interaction interface

**Configuration:**
- `phone_mcp/config.py` - Timeout settings and retry configuration

### Key Design Patterns

1. **Async/Await Pattern**: All ADB operations are asynchronous using `asyncio.create_subprocess_shell()`
2. **Command Abstraction**: `core.py` provides `run_command()` for executing ADB commands with timeout handling
3. **Tool Modularity**: Each phone feature is separated into its own tool module
4. **Error Handling**: Comprehensive error handling with retry mechanisms for device connections
5. **UI Automation**: Uses ADB UI dump and element parsing for automated interactions

### Testing Strategy

- **pytest** with asyncio support (configured in pytest.ini)
- Test files follow `test_*.py` pattern
- Tests include device functionality, MCP integration, and map services
- Async tests use pytest-asyncio with auto mode

### Device Requirements

- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and configured
- Device connected via USB or network ADB

### MCP Integration

The plugin exposes phone control capabilities through MCP tools, allowing AI assistants to:
- Execute phone calls and SMS operations
- Control apps and system functions
- Perform screen interactions and UI automation
- Monitor UI changes and wait for specific elements
- Analyze screen content and make intelligent decisions

Each tool returns structured JSON responses for reliable programmatic interaction.