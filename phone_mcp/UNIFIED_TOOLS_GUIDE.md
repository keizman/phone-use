# Unified MCP Tools Guide

## Overview

The phone-use MCP has been refactored from 30+ individual tools into **8 unified tools** for better LLM tool selection and reduced complexity. Each tool consolidates related functionality with clear, descriptive prompts to help external LLMs choose the right tool.

## 8 Unified Tools

### 1. `phone_screen_interact` 
**PRIMARY SCREEN INTERACTION TOOL**
- **Purpose**: All screen-based interactions (tap, swipe, input, analysis)
- **Key Features**:
  - Visual element recognition using Omniparser
  - UUID-based element targeting
  - Automatic bias correction for media content
  - Coordinate-based fallback interactions
  - Screen analysis and element discovery

**Usage Examples**:
```json
{"action": "tap", "target": "Settings"}
{"action": "input_text", "target": "search box", "text": "hello"}
{"action": "swipe", "coordinates": "500,800,500,200"}
{"action": "analyze_only"}
```

### 2. `phone_app_control`
**APP MANAGEMENT TOOL**
- **Purpose**: Launch, stop, and manage applications
- **Key Features**:
  - Launch apps by name or package
  - Terminate/force stop apps
  - List installed applications
  - Get current active app

**Usage Examples**:
```json
{"action": "launch", "app_name": "Settings"}
{"action": "list_apps"}
{"action": "terminate", "package_name": "com.android.settings"}
```

### 3. `phone_system_control`
**SYSTEM CONTROL TOOL**
- **Purpose**: Device navigation and system operations
- **Key Features**:
  - Hardware key presses (home, back, menu, volume)
  - System navigation (home screen, settings, notifications)
  - Recent apps and quick settings access

**Usage Examples**:
```json
{"action": "go_home"}
{"action": "press_key", "key": "volume_up"}
{"action": "open_settings"}
```

### 4. `phone_file_operations`
**FILE OPERATIONS TOOL**
- **Purpose**: File management and app installation
- **Key Features**:
  - Install/uninstall APK files
  - Push/pull files to/from device
  - Take screenshots
  - Clear app cache and data

**Usage Examples**:
```json
{"action": "install", "apk_path": "/path/to/app.apk"}
{"action": "screenshot"}
{"action": "push", "source_path": "/local/file", "destination_path": "/sdcard/file"}
```

### 5. `phone_communication`
**COMMUNICATION TOOL**
- **Purpose**: Phone calls, SMS, and contacts
- **Key Features**:
  - Make and receive phone calls
  - Send SMS messages
  - Contact management
  - Call control (answer, hang up)

**Usage Examples**:
```json
{"action": "call", "phone_number": "1234567890"}
{"action": "sms", "phone_number": "1234567890", "message": "Hello"}
{"action": "hang_up"}
```

### 6. `phone_media_control`
**MEDIA CONTROL TOOL**
- **Purpose**: Media playback, recording, and camera
- **Key Features**:
  - Play audio/video files
  - Screen recording with duration control
  - Camera operations and photo capture
  - Media app control

**Usage Examples**:
```json
{"action": "play_media", "media_file": "/sdcard/music.mp3"}
{"action": "start_recording", "recording_time": 30}
{"action": "take_photo"}
```

### 7. `phone_web_browser`
**WEB BROWSER TOOL**
- **Purpose**: Web browsing and URL operations
- **Key Features**:
  - Open URLs in browser
  - Web search functionality
  - Browser navigation (back, forward, refresh)
  - Bookmark management

**Usage Examples**:
```json
{"action": "open_url", "url": "https://www.google.com"}
{"action": "search", "search_query": "weather today"}
{"action": "refresh"}
```

### 8. `phone_device_info`
**DEVICE INFO TOOL**
- **Purpose**: Device status and diagnostic information
- **Key Features**:
  - Connection status checking
  - System information retrieval
  - Battery, network, and storage status
  - Hardware diagnostics

**Usage Examples**:
```json
{"action": "check_connection"}
{"action": "get_system_info"}
{"action": "get_battery"}
```

## Tool Selection Guidelines for LLMs

### When to Use Each Tool:

1. **Screen Interactions** → `phone_screen_interact`
   - Tapping buttons, links, or UI elements
   - Typing text into fields
   - Swiping or scrolling gestures
   - Analyzing what's on screen

2. **App Management** → `phone_app_control`
   - Opening or closing apps
   - Checking what apps are installed
   - Finding the current active app

3. **System Navigation** → `phone_system_control`
   - Going to home screen
   - Pressing hardware buttons
   - Opening system settings
   - Accessing notifications

4. **File Operations** → `phone_file_operations`
   - Installing new apps
   - Taking screenshots
   - Transferring files
   - Managing app data

5. **Communication** → `phone_communication`
   - Making phone calls
   - Sending text messages
   - Managing contacts

6. **Media Tasks** → `phone_media_control`
   - Playing music or videos
   - Recording screen
   - Taking photos
   - Camera operations

7. **Web Activities** → `phone_web_browser`
   - Opening websites
   - Searching the web
   - Browser navigation

8. **Device Status** → `phone_device_info`
   - Checking if device is connected
   - Getting system information
   - Battery or network status

## Key Features

### Omniparser Integration
- Automatic visual element recognition
- UUID-based precise targeting
- Bias correction for media content
- Fallback to coordinate-based interaction

### Enhanced Prompts
- Clear tool descriptions with **bold priority markers**
- Detailed usage examples
- Parameter explanations
- Action categorization

### Consolidated Actions
- Multiple related actions per tool
- Unified parameter structure
- Consistent JSON response format
- Error handling across all tools

## Migration from Legacy Tools

The unified tools replace the following legacy tools:

**Screen Interaction Tools** → `phone_screen_interact`:
- `omniparser_analyze_screen`
- `omniparser_tap_element_by_uuid`
- `omniparser_execute_action_by_uuid`
- `android_tap_coordinates`
- `android_swipe_gesture`
- `android_input_text`
- `analyze_screen`
- `interact_with_screen`

**App Management Tools** → `phone_app_control`:
- `launch_app_activity`
- `list_installed_apps`
- `terminate_app`
- `force_stop_app`
- `get_current_window`

**System Tools** → `phone_system_control`:
- `go_to_home`
- `open_settings`
- `android_press_key`
- `get_app_shortcuts`

**File Tools** → `phone_file_operations`:
- `adb_install`
- `adb_uninstall`
- `adb_push`
- `adb_pull`
- `take_screenshot_and_save`
- `clear_app_data`
- `clear_cache_and_restart`

**Communication Tools** → `phone_communication`:
- Call-related functions
- SMS functions
- Contact management

**Media Tools** → `phone_media_control`:
- `start_screen_recording`
- `play_media`
- Camera functions

**Web Tools** → `phone_web_browser`:
- `open_url`
- Browser navigation

**Device Info Tools** → `phone_device_info`:
- `check_device_connection`
- System information functions

## Benefits

1. **Reduced Complexity**: 8 tools instead of 30+
2. **Better LLM Selection**: Clear, descriptive tool names and prompts
3. **Consolidated Functionality**: Related actions grouped logically
4. **Enhanced Prompts**: Detailed descriptions with usage examples
5. **Maintained Compatibility**: All original functionality preserved
6. **Improved Error Handling**: Consistent error responses across tools
7. **Better Documentation**: Clear usage patterns and examples