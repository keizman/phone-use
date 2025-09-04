## Do not use emoji, it's prevent use in code
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

This is a **phone-mcp** plugin that provides MCP (Model Context Protocol) integration for controlling Android devices via ADB commands. The project has been enhanced with **Omniparser visual recognition** for precise UI element interaction and advanced automation capabilities.

### Core Components

**Main Entry Points:**
- `phone_mcp/__main__.py` - MCP server entry point with comprehensive tool registration
- `phone_mcp/cli.py` - Command-line interface
- `phone_mcp/core.py` - Core ADB command execution and device connection logic

**🔥 Advanced Visual Recognition Tools (phone_mcp/tools/):**
- `omniparser_interface.py` - **Core Omniparser integration** with visual element recognition
- `omniparser_tools.py` - **MCP-compatible Omniparser functions** for precise UI interaction
- `prompt_engineering.py` - **AI task guidance system** with bias detection and positioning help
- `android_computer_integration.py` - Enhanced Android automation with coordinate fallback

**Traditional Tool Modules:**
- `adb_tools.py` - File operations, APK installation, system controls
- `apps.py` - App launching and management  
- `media.py` - Screenshots, screen recording
- `screen_interface.py` - Basic screen interaction and analysis
- `ui_monitor.py` - UI change monitoring and automation
- `system.py` - System information and device management
- `maps.py` - Location-based services and POI search
- `interactions.py` - Unified interaction interface

**Configuration:**
- `phone_mcp/config.py` - Timeout settings and retry configuration

### 🎯 Key Features & Capabilities

#### Visual Recognition & Precise Interaction
- **Omniparser Integration**: Uses computer vision (YOLO + PaddleOCR) for visual UI element recognition
- **UUID-based Element Targeting**: Each UI element gets unique identifier for precise interaction
- **Bias Correction**: Automatic correction for media content where titles appear below clickable areas
- **Fallback System**: Coordinate-based interaction when visual recognition fails

#### AI-Enhanced Automation
- **Task Guidance System**: Intelligent prompts for different automation scenarios
- **Bias Detection**: Automatic detection of when bias correction is needed
- **Positioning Guidance**: Smart recommendations for element interaction strategies
- **Context-Aware Interactions**: Adapts interaction approach based on content type

#### Tool Architecture
- **30+ MCP Tools**: Comprehensive coverage of phone control functions
- **Layered Functionality**: Professional visual tools + basic ADB operations + helper functions
- **Server Integration**: Omniparser server communication (default: http://100.122.57.128:9333)

### Key Design Patterns

1. **Visual-First Approach**: Prioritize Omniparser visual recognition over coordinate-based interaction
2. **UUID-Based Targeting**: Use unique identifiers for reliable element interaction across screen changes
3. **Async/Await Pattern**: All operations are asynchronous using `asyncio`
4. **Tool Modularity**: Specialized tools for different aspects (visual, traditional, AI-guidance)
5. **Error Handling**: Comprehensive error handling with multiple fallback strategies
6. **Bias Correction Algorithm**: Smart offset calculation for media content interaction
7. **Server-Client Architecture**: External Omniparser server for heavy visual processing

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

The plugin exposes comprehensive phone control capabilities through MCP tools, allowing AI assistants to:

#### 🎯 Visual Recognition & Smart Interaction
- **Omniparser Screen Analysis**: `omniparser_analyze_screen()` - Computer vision-based UI element recognition
- **UUID-based Element Interaction**: `omniparser_tap_element_by_uuid()` - Precise element targeting
- **Smart Action Execution**: `omniparser_execute_action_by_uuid()` - Context-aware interactions with bias correction
- **Element Discovery**: `omniparser_find_elements_by_content()` - Content-based element finding

#### 🤖 AI Task Guidance
- **Task-Specific Guidance**: `get_task_guidance()` - Intelligent prompts for different automation scenarios  
- **Positioning Recommendations**: `get_positioning_guidance()` - Smart interaction strategies
- **Bias Correction Advice**: `get_bias_recommendation()` - Auto-detection of media content interaction needs

#### 📱 Traditional Phone Controls
- **App Management**: Launch, terminate, list applications
- **System Control**: Home, back, settings, notifications
- **File Operations**: Install APKs, push/pull files, screenshots
- **Communication**: Phone calls, SMS, contacts
- **Media Control**: Screen recording, camera, media playback

#### 🔧 Enhanced Automation
- **Coordinate Fallback**: Traditional tap/swipe when visual recognition fails
- **UI Monitoring**: Wait for elements, monitor changes
- **Device Management**: Connection status, system info

### 🚀 Usage Priorities for AI Assistants

1. **Screen Interaction Priority**: 
   - First: Use `omniparser_analyze_screen()` for visual analysis
   - Then: Use `omniparser_tap_element_by_uuid()` for precise interaction
   - Fallback: Use coordinate-based `android_tap_coordinates()` if needed

2. **Content Interaction**:
   - Media content: Always consider `get_bias_recommendation()` first
   - Text elements: Use content-based finding with `omniparser_find_elements_by_content()`
   - Interactive elements: Use `omniparser_find_interactive_elements()`

3. **Task Guidance**:
   - Before complex tasks: Call `get_task_guidance()` for intelligent workflow suggestions
   - For positioning challenges: Use `get_positioning_guidance()`

Each tool returns structured JSON responses for reliable programmatic interaction. The system maintains compatibility with both modern visual recognition and traditional ADB-based automation.

## 🔧 Recent Optimizations & Tool Management

### Tool Consolidation Strategy

The project currently has **30+ MCP tools** which may cause tool selection difficulties for external LLMs. A **smart layered consolidation approach** has been designed:

#### 📊 Tool Prioritization Framework
```
【核心专业层】★★★ - Keep Independent (High Priority)
- omniparser_analyze_screen (Visual analysis core)
- omniparser_tap_element_by_uuid (Precision interaction core) 
- omniparser_execute_action_by_uuid (Advanced interaction)
- get_task_guidance (AI guidance core)

【常用功能层】★★ - Smart Consolidation (Medium Priority)
- Basic ADB operations (tap/swipe/input) → phone_basic_interaction
- App management (launch/stop/list) → phone_app_management  
- System controls (keys/settings) → phone_system_control

【辅助工具层】★ - Merge Similar Functions (Low Priority)
- File operations → phone_file_operations
- Device info/debug → phone_info_and_debug
```

#### 🎯 Optimization Principles
1. **Preserve Omniparser Specialization**: Never dilute visual recognition capabilities
2. **Enhance Tool Prompts**: Use clear priority markers (★★★) and decision guidance
3. **Maintain Professional Tools**: Keep AI guidance and visual tools independent
4. **Smart Merging**: Only combine functionally similar basic operations
5. **LLM Selection Guidance**: Provide clear "when to use" instructions

#### 📝 Enhanced Prompt Strategy
- **Bold Priority Markers**: ★★★ PRIMARY TOOL, ★★ SECONDARY, ★ HELPER
- **Decision Trees**: "For screen interaction → use Omniparser first"
- **Usage Scenarios**: Clear "when to use this tool" descriptions
- **Capability Boundaries**: Explicit tool limitation explanations

### Alternative Unified Tools Architecture

A **unified tools system** (`unified_tools.py`) has been created as an alternative approach that consolidates functionality into 8 comprehensive tools while preserving all capabilities. This can be activated if simpler tool selection is preferred over specialized tool preservation.