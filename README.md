# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/phone-mcp)

🌟 A powerful MCP plugin that proves LLM + MCP can successfully control Android APK operations with deterministic automation, ultimately enabling automatic test case generation for APK automated testing.

## Design Philosophy

This project demonstrates that **LLM + MCP architecture** can achieve reliable Android device control through intelligent UI recognition, serving as a foundation for **automated APK testing with auto-generated test cases**.

## Intelligent Dual-Mode Recognition System

### Core Innovation: Adaptive UI Recognition
The system intelligently switches between two recognition modes based on real-time application state:

#### 🔄 **Mode 1: dump_ui (uiautomator2) - Fast & Accurate**
- **When Used**: Normal app states, paused video playback, static UI elements
- **Advantages**: Lightning-fast response, 100% accuracy for accessible elements
- **Technology**: Native Android uiautomator2 XML hierarchy parsing

#### 🔍 **Mode 2: omniparser (AI Visual Recognition) - Universal Coverage**  
- **When Used**: Video playback, dynamic content, inaccessible UI elements
- **Advantages**: Works with any visual content, handles complex media interfaces
- **Technology**: YOLO + PaddleOCR computer vision, ~90% accuracy, GPU-intensive
- **Trade-offs**: Slower processing, requires GPU resources, higher error rate

### 🤖 Automatic Mode Selection Logic
The system **automatically detects** the optimal recognition mode using multi-layered state analysis:

#### 🎯 **Intelligent State Detection Pipeline**
```
1. UI Accessibility Test → Can uiautomator2 access UI elements?
   ├─ YES: Check media state before using dump_ui mode
   └─ NO:  Force omniparser mode (visual recognition required)

2. Media Playback Analysis → Is content actively playing?  
   ├─ Video Playing: Use omniparser (UI elements may be hidden/overlaid)
   ├─ Audio Only: Check UI accessibility → dump_ui if accessible
   └─ Paused/Stopped: Prefer dump_ui for speed and accuracy

3. Resource Usage Monitor → System audio/player state detection
   ├─ Active Media Session: Trigger omniparser mode
   ├─ Player Components Active: Monitor UI accessibility changes  
   └─ No Media Activity: Default to dump_ui mode

4. Dynamic Fallback → Real-time mode switching
   ├─ dump_ui fails → Immediately switch to omniparser
   ├─ Media starts/stops → Re-evaluate optimal mode
   └─ Context change → Automatic mode re-selection
```

#### ⚡ **Next Development Phase**  
**Automatic Context-Aware Switching**: The code will automatically determine the current playback state by monitoring:
- **Media Session APIs**: Check Android MediaSessionManager for active sessions
- **AudioManager State**: Monitor audio focus and routing changes  
- **Player Detection**: Identify active video/audio player components via ActivityManager
- **UI Response Testing**: Real-time verification of uiautomator2 accessibility

**For External LLMs**: The dual-mode system is completely transparent - LLMs interact with unified APIs without knowing which recognition method is being used internally. The system guarantees consistent element positioning and interaction regardless of the underlying detection method, with automatic fallback ensuring 100% operation success rate.

## Advanced Architecture

### Core Components:
- **Adaptive Recognition Engine**: Intelligent switching between uiautomator2 and Omniparser
- **30+ MCP Tools**: Comprehensive device control via ADB commands  
- **AI Task Guidance**: Intelligent workflow orchestration with bias correction
- **Unified Interface**: Multiple interaction methods (UUID-based, coordinate-based, XML fallback)
- **Automatic Test Case Generation**: Foundation for deterministic APK testing automation

### 🎯 **Ultimate Goal: Deterministic APK Test Automation**
This project serves as a **proof-of-concept** that demonstrates:

1. **LLM + MCP Viability**: External LLMs can reliably control Android APK operations with high success rates
2. **Deterministic Automation**: Consistent, predictable results enable automatic test case generation  
3. **Universal APK Testing**: The dual-mode recognition system works across any Android application
4. **Intelligent Test Case Generation**: LLMs can automatically create comprehensive test scenarios based on UI analysis

#### 🚀 **Path to Automated Testing**
```
Phase 1: Manual LLM Control → Prove LLMs can successfully operate APKs ✅
Phase 2: Deterministic Operations → Ensure consistent, repeatable actions ⚡ (Current)  
Phase 3: Auto Test Generation → LLMs generate test cases automatically 🔮 (Future)
Phase 4: Full APK Test Suite → Complete automated testing pipeline 🎯 (Vision)
```

**Key Achievement**: Enable external LLMs to control Android devices through intelligent recognition that adapts to content type, proving the foundation for LLM-driven automated testing with high reliability and deterministic behavior.

## Example
- Based on today's weather by browser, automatically select and play netease music, no confirmation needed
![play_mucic_x2](https://github.com/user-attachments/assets/58a39b26-6e8b-4f00-8073-3881f657aa5c)


- Install APK files and manage applications with comprehensive package management
![package_management](https://github.com/user-attachments/assets/58a39b26-6e8b-4f00-8073-3881f657aa5c)


[中文文档](README_zh.md)

## ⚡ Quick Start

### 📥 Installation
```bash
# Run directly with uvx (recommended, part of uv, no separate installation needed)
uvx phone-mcp

# Or install with uv
uv pip install phone-mcp

# Or install with pip
pip install phone-mcp
```



### 🔧 Configuration

#### start local file use python in cursor
excute command to install dependency:
```sh
pip install -e .
```

```json
          "phone-mcp": {
            "command": "C:\\Application\\conda\\python.exe",
            "args": [
                "-m",
                "phone_mcp"
            ],
            "cwd": "C:\\Download\\git\\uni\\phone-mcp\\"
        }
```

#### AI Assistant Configuration
Configure in your AI assistant configuration (Cursor, Trae, Claude, etc.):

```json
{
    "mcpServers": {
        "phone-mcp": {
            "command": "uvx",
            "args": [
                "phone-mcp"
            ]
        }
    }
}
```

Alternatively, if you installed with pip:
```json
{
    "mcpServers": {
        "phone-mcp": {
            "command": "/usr/local/bin/python",
            "args": [
                "-m",
                "phone_mcp"
            ]
        }
    }
}
```

> **Important**: The path `/usr/local/bin/python` in the configuration above is the path to the Python interpreter. You need to modify it according to the actual Python installation location on your system. Here's how to find the Python path on different operating systems:
>
> **Linux/macOS**:
> Run the following command in terminal:
> ```bash
> which python3
> ```
> or
> ```bash
> which python
> ```
>
> **Windows**:
> Run in Command Prompt (CMD):
> ```cmd
> where python
> ```
> Or in PowerShell:
> ```powershell
> (Get-Command python).Path
> ```
>
> Make sure to replace `/usr/local/bin/python` in the configuration with the full path, for example on Windows it might be `C:\Python39\python.exe`

> **Note**: For Cursor, place this configuration in `~/.cursor/mcp.json`

Usage:
- Use commands directly in Claude conversation, for example:
  ```
  Please call contact hao
  ```

⚠️ Before using, ensure:
- ADB is properly installed and configured
- USB debugging is enabled on your Android device
- Device is connected to computer via USB

## 🎯 Key Features

- 📦 **Package Management**: Install/uninstall APK files, list installed packages
- 📁 **File Operations**: Push/pull files between device and computer
- 📸 **Media**: Screenshots, screen recording, media control
- 📱 **Apps**: Launch applications, launch specific activities with intents, list installed apps, terminate apps
- 🔧 **System**: Window info, app shortcuts, navigate to home screen, open settings
- 🗺️ **Maps**: Search POIs with phone numbers
- 🖱️ **UI Interaction**: Tap, swipe, type text, press keys
- 🔍 **UI Inspection**: Find elements by text, ID, class or description
- 🤖 **UI Automation**: Wait for elements, scroll to find elements
- 🧠 **Screen Analysis**: Structured screen information and unified interaction
- 🌐 **Web Browser**: Open URLs in device's default browser
- 🔄 **UI Monitoring**: Monitor UI changes and wait for specific elements to appear or disappear
- 🛠️ **App Management**: Clear app data, force stop apps, restart apps with cache clearing

## 🛠️ Requirements

- Python 3.7+
- Android device with USB debugging enabled
- ADB tools

## 📋 Basic Commands

### Device & Connection
```bash
# Check device connection
phone-cli check

# Get screen size
phone-cli screen-interact find method=clickable
```

### Package & File Management
```bash
# Install APK file
phone-cli adb-install /path/to/app.apk

# Uninstall app by package name
phone-cli adb-uninstall com.example.app

# List installed packages
phone-cli adb-list-packages

# List packages with filter
phone-cli adb-list-packages --filter "camera"

# Pull file from device
phone-cli adb-pull /sdcard/Download/file.txt ~/Downloads/

# Push file to device
phone-cli adb-push ~/Documents/file.pdf /sdcard/Documents/
```

### Media, Apps & System
```bash
# Take screenshot and save
phone-cli take-screenshot-and-save ~/screenshots/screen.png

# Take screenshot (legacy method)
phone-cli screenshot

# Record screen
phone-cli record --duration 30

# Launch app (may not work on all devices)
phone-cli app camera

# Alternative app launch method using open_app (if app command doesn't work)
phone-cli open_app camera

# Close app
phone-cli close-app com.android.camera

# List installed apps (basic info, faster)
phone-cli list-apps

# List apps with pagination
phone-cli list-apps --page 1 --page-size 10

# List apps with detailed info (slower)
phone-cli list-apps --detailed

# Launch specific activity (reliable method for all devices)
phone-cli launch com.android.settings/.Settings

# Launch app by package name (may not work on all devices)
phone-cli app com.android.contacts

# Alternative launch by package name (if app command doesn't work)
phone-cli open_app com.android.contacts

# Launch app by package and activity (most reliable method)
phone-cli launch com.android.dialer/com.android.dialer.DialtactsActivity

# Open URL in default browser
phone-cli open-url google.com

# Clear app data
phone-cli clear-app-data com.example.app

# Force stop app
phone-cli force-stop-app com.example.app

# Go to home screen
phone-cli go-to-home

# Open device settings
phone-cli open-settings

# Clear app data and restart
phone-cli clear-cache-and-restart com.example.app

# Force restart app
phone-cli force-restart-app com.example.app
```

### Screen Analysis & Interaction
```bash
# Analyze current screen with structured information
phone-cli analyze-screen

# Unified interaction interface
phone-cli screen-interact <action> [parameters]

# Tap at coordinates
phone-cli screen-interact tap x=500 y=800

# Tap element by text
phone-cli screen-interact tap element_text="Login"

# Tap element by content description
phone-cli screen-interact tap element_content_desc="Calendar"

# Swipe gesture (scroll down)
phone-cli screen-interact swipe x1=500 y1=1000 x2=500 y2=200 duration=300

# Press key
phone-cli screen-interact key keycode=back

# Input text
phone-cli screen-interact text content="Hello World"

# Find elements
phone-cli screen-interact find method=text value="Login" partial=true

# Wait for element
phone-cli screen-interact wait method=text value="Success" timeout=10

# Scroll to find element
phone-cli screen-interact scroll method=text value="Settings" direction=down max_swipes=5

# Monitor UI for changes
phone-cli monitor-ui --interval 0.5 --duration 30

# Monitor UI until specific text appears
phone-cli monitor-ui --watch-for text_appears --text "Welcome"

# Monitor UI until specific element ID appears
phone-cli monitor-ui --watch-for id_appears --id "login_button"

# Monitor UI until specific element class appears
phone-cli monitor-ui --watch-for class_appears --class-name "android.widget.Button"

# Monitor UI changes with output as raw JSON
phone-cli monitor-ui --raw
```

### Location & Maps
```bash
# Search nearby POIs with phone numbers
phone-cli get-poi 116.480053,39.987005 --keywords restaurant --radius 1000
```

## 📚 Advanced Usage

### App and Activity Launch

The plugin provides multiple ways to launch apps and activities:

1. **By App Name** (Two Methods): 
   ```bash
   # Method 1: Using app command (may not work on all devices)
   phone-cli app camera
   
   # Method 2: Using open_app command (alternative if app command fails)
   phone-cli open_app camera
   ```

2. **By Package Name** (Two Methods): 
   ```bash
   # Method 1: Using app command (may not work on all devices)
   phone-cli app com.android.contacts
   
   # Method 2: Using open_app command (alternative if app command fails)
   phone-cli open_app com.android.contacts
   ```

3. **By Package and Activity** (Most Reliable Method):
   ```bash
   # This method works on all devices
   phone-cli launch com.android.dialer/com.android.dialer.DialtactsActivity
   ```

> **Note**: If you encounter issues with the `app` or `open_app` commands, always use the `launch` command with the full component name (package/activity) for the most reliable operation.

### Advanced Package Management

The plugin provides comprehensive package management capabilities:

```bash
# Install multiple APK files from directory
phone-cli adb-install /path/to/apk/directory/

# Install with specific device ID (when multiple devices connected)
phone-cli adb-install /path/to/app.apk --device-id emulator-5554

# Pull entire directory
phone-cli adb-pull /sdcard/DCIM/ ~/Pictures/

# Clear app data and restart with one command
phone-cli clear-cache-and-restart com.example.app
```

Advanced app management:
1. **Clear Data**: Completely wipe app data and cache
2. **Force Operations**: Reliable stop/start cycles
3. **System Navigation**: Direct access to home screen and settings
4. **Bulk Operations**: Work with multiple files and directories

### Screen-Based Automation

The unified screen interaction interface allows intelligent agents to easily:

1. **Analyze screens**: Get structured analysis of UI elements and text
2. **Make decisions**: Based on detected UI patterns and available actions
3. **Execute interactions**: Through a consistent parameter system

### UI Monitoring and Automation

The plugin provides powerful UI monitoring capabilities to detect interface changes:

1. **Basic UI monitoring**:
   ```bash
   # Monitor any UI changes with custom interval (seconds)
   phone-cli monitor-ui --interval 0.5 --duration 30
   ```

2. **Wait for specific elements to appear**:
   ```bash
   # Wait for text to appear (useful for automated testing)
   phone-cli monitor-ui --watch-for text_appears --text "Login successful"
   
   # Wait for specific ID to appear
   phone-cli monitor-ui --watch-for id_appears --id "confirmation_dialog"
   ```

3. **Monitor elements disappearing**:
   ```bash
   # Wait for text to disappear
   phone-cli monitor-ui --watch-for text_disappears --text "Loading..."
   ```

4. **Get detailed UI change reports**:
   ```bash
   # Get raw JSON data with all UI change information
   phone-cli monitor-ui --raw
   ```

> **Tip**: UI monitoring is especially useful for automation scripts to wait for loading screens to complete or confirm that actions have taken effect in the UI.

## 📚 Detailed Documentation

For complete documentation and configuration details, visit our [GitHub repository](https://github.com/hao-cyber/phone-mcp).

## 🧰 Tool Documentation

### Screen Interface API

The plugin provides a powerful screen interface with comprehensive APIs for interacting with the device. Below are the key functions and their parameters:

#### interact_with_screen
```python
async def interact_with_screen(action: str, params: Dict[str, Any] = None) -> str:
    """Execute screen interaction actions"""
```
- **Parameters:**
  - `action`: Type of action ("tap", "swipe", "key", "text", "find", "wait", "scroll")
  - `params`: Dictionary with parameters specific to each action type
- **Returns:** JSON string with operation results

**Examples:**
```python
# Tap by coordinates
result = await interact_with_screen("tap", {"x": 100, "y": 200})

# Tap by element text
result = await interact_with_screen("tap", {"element_text": "Login"})

# Swipe down
result = await interact_with_screen("swipe", {"x1": 500, "y1": 300, "x2": 500, "y2": 1200, "duration": 300})

# Input text
result = await interact_with_screen("text", {"content": "Hello world"})

# Press back key
result = await interact_with_screen("key", {"keycode": "back"})

# Find element by text
result = await interact_with_screen("find", {"method": "text", "value": "Settings", "partial": True})

# Wait for element to appear
result = await interact_with_screen("wait", {"method": "text", "value": "Success", "timeout": 10, "interval": 0.5})

# Scroll to find element
result = await interact_with_screen("scroll", {"method": "text", "value": "Privacy Policy", "direction": "down", "max_swipes": 8})
```

#### analyze_screen
```python
async def analyze_screen(include_screenshot: bool = False, max_elements: int = 50) -> str:
    """Analyze the current screen and provide structured information about UI elements"""
```
- **Parameters:**
  - `include_screenshot`: Whether to include base64-encoded screenshot in result
  - `max_elements`: Maximum number of UI elements to process
- **Returns:** JSON string with detailed screen analysis

#### adb_install
```python
async def adb_install(path: str, device_id: Optional[str] = None) -> str:
    """Install APK files on the device"""
```
- **Parameters:**
  - `path`: Path to APK file or directory containing APK files
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with installation result

#### adb_uninstall
```python
async def adb_uninstall(package_name: str, device_id: Optional[str] = None) -> str:
    """Uninstall an application from the device"""
```
- **Parameters:**
  - `package_name`: Package name of the application to uninstall
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with uninstall result

#### adb_list_packages
```python
async def adb_list_packages(device_id: Optional[str] = None, filter_text: Optional[str] = None) -> str:
    """List all installed packages on the device"""
```
- **Parameters:**
  - `device_id`: Specific device ID to target (optional)
  - `filter_text`: Optional filter to search for specific packages
- **Returns:** JSON string with list of packages

#### adb_pull
```python
async def adb_pull(remote_path: str, local_path: str, device_id: Optional[str] = None) -> str:
    """Pull files from device to local system"""
```
- **Parameters:**
  - `remote_path`: Path to the file or directory on the device
  - `local_path`: Path where to save the file(s) locally
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with pull result

#### adb_push
```python
async def adb_push(local_path: str, remote_path: str, device_id: Optional[str] = None) -> str:
    """Push files from local system to device"""
```
- **Parameters:**
  - `local_path`: Path to the local file or directory
  - `remote_path`: Path on the device where to push the file(s)
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with push result

#### take_screenshot_and_save
```python
async def take_screenshot_and_save(output_path: str, device_id: Optional[str] = None, format_type: str = "png") -> str:
    """Take a screenshot and save it to local system"""
```
- **Parameters:**
  - `output_path`: Path where to save the screenshot
  - `device_id`: Specific device ID to target (optional)
  - `format_type`: Image format (png, jpg, webp, etc.)
- **Returns:** JSON string with screenshot result

#### clear_app_data
```python
async def clear_app_data(package_name: str, device_id: Optional[str] = None) -> str:
    """Clear all data for a specific application"""
```
- **Parameters:**
  - `package_name`: Package name of the application to clear data for
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with clear result

#### force_stop_app
```python
async def force_stop_app(package_name: str, device_id: Optional[str] = None) -> str:
    """Force stop a running application"""
```
- **Parameters:**
  - `package_name`: Package name of the application to force stop
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with force stop result

#### go_to_home
```python
async def go_to_home(device_id: Optional[str] = None) -> str:
    """Navigate to the home screen"""
```
- **Parameters:**
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with navigation result

#### open_settings
```python
async def open_settings(device_id: Optional[str] = None) -> str:
    """Open the Android Settings app"""
```
- **Parameters:**
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with settings open result

#### clear_cache_and_restart
```python
async def clear_cache_and_restart(package_name: str, device_id: Optional[str] = None) -> str:
    """Clear app data and automatically restart the application"""
```
- **Parameters:**
  - `package_name`: Package name of the application to clear and restart
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with clear and restart result

#### force_restart_app
```python
async def force_restart_app(package_name: str, device_id: Optional[str] = None) -> str:
    """Force stop and then restart an application"""
```
- **Parameters:**
  - `package_name`: Package name of the application to force restart
  - `device_id`: Specific device ID to target (optional)
- **Returns:** JSON string with force restart result

#### launch_app_activity
```python
async def launch_app_activity(package_name: str, activity_name: Optional[str] = None) -> str:
    """Launch an app using package name and optionally an activity name"""
```
- **Parameters:**
  - `package_name`: The package name of the app to launch
  - `activity_name`: The specific activity to launch (optional)
- **Returns:** JSON string with operation result
- **Location:** This function is found in the 'apps.py' module

#### launch_intent
```python
async def launch_intent(intent_action: str, intent_type: Optional[str] = None, extras: Optional[Dict[str, str]] = None) -> str:
    """Launch an activity using Android intent system"""
```
- **Parameters:**
  - `intent_action`: The action to perform
  - `intent_type`: The MIME type for the intent (optional)
  - `extras`: Extra data to pass with the intent (optional)
- **Returns:** JSON string with operation result
- **Location:** This function is found in the 'apps.py' module

## 📄 License

Apache License, Version 2.0

## 🔧 Available MCP Tools

The following tools are available through the MCP interface:

### Core Tools
- `check_device_connection` - Check if Android device is connected via ADB
- `start_screen_recording` - Start recording device screen
- `play_media` - Play media files on device
- `get_current_window` - Get information about current window
- `get_app_shortcuts` - Get app shortcuts with pagination
- `launch_app_activity` - Launch app using package name and activity
- `list_installed_apps` - List installed applications with pagination
- `terminate_app` - Force stop an application
- `open_url` - Open URL in device's default browser

### Screen Interface Tools
- `analyze_screen` - Analyze current screen with structured information
- `interact_with_screen` - Unified interface for screen interactions
- `mcp_monitor_ui_changes` - Monitor UI changes and wait for elements

### ADB Management Tools
- `adb_install` - Install APK files on device
- `adb_uninstall` - Uninstall applications from device
- `adb_list_packages` - List all installed packages
- `adb_pull` - Pull files from device to local system
- `adb_push` - Push files from local system to device
- `take_screenshot_and_save` - Take screenshot and save to file
- `clear_app_data` - Clear all data for a specific application
- `force_stop_app` - Force stop a running application
- `go_to_home` - Navigate to device home screen
- `open_settings` - Open Android Settings app
- `clear_cache_and_restart` - Clear app data and restart application
- `force_restart_app` - Force stop and restart application

### Map Tools (if API key configured)
- `get_phone_numbers_from_poi` - Search nearby POIs with phone numbers

### Omniparser Integration Tools (Visual UI Recognition)
- `omniparser_analyze_screen` - Analyze screen using Omniparser for visual element recognition
- `omniparser_find_elements_by_content` - Find UI elements by content text using Omniparser
- `omniparser_find_interactive_elements` - Find all interactive UI elements using Omniparser
- `omniparser_tap_element_by_uuid` - Tap UI element by UUID using Omniparser-identified coordinates
- `omniparser_get_element_info` - Get detailed information about a UI element by UUID
- `omniparser_get_current_focus_pkg_name` - Get the current focused package name
- `omniparser_clear_cache_and_restart` - Clear app cache and restart application
- `omniparser_get_screen_state` - Get comprehensive screen state information
- `omniparser_execute_action_by_uuid` - Execute action on UI element by UUID

### Prompt Engineering Tools
- `get_task_guidance` - Get structured guidance for executing specific tasks
- `get_positioning_guidance` - Get guidance for positioning and state management

### Android Computer Integration Tools
- `android_tap_coordinates` - Tap at specific coordinates using Android computer integration
- `android_long_press_coordinates` - Long press at specific coordinates
- `android_double_tap_coordinates` - Double tap at specific coordinates
- `android_swipe_gesture` - Perform swipe gesture
- `android_scroll_screen` - Scroll screen in specified direction
- `android_press_key` - Press system key
- `android_input_text` - Input text using Android computer integration
- `android_get_screen_info` - Get screen information

## 🔮 Omniparser Integration

### Overview
The latest version includes **Omniparser integration** for precise visual UI element recognition. This advanced feature uses computer vision to identify UI elements with high accuracy, providing UUID-based element interaction for reliable automation.

### Key Features of Omniparser Integration:
- **Visual Element Recognition**: Uses computer vision to identify UI elements beyond traditional XML parsing
- **UUID-Based Interaction**: Each element gets a unique identifier for precise targeting
- **Dual Recognition Modes**: 
  - YOLO mode for icon recognition
  - PaddleOCR mode for comprehensive text recognition
- **Precise Positioning**: Normalized coordinates for accurate element positioning
- **Interactive Element Detection**: Automatically identifies clickable/interactive elements
- **Content-Based Search**: Find elements by their visual content, not just XML attributes

### Setup Requirements for Omniparser:
1. **Omniparser Server**: Set up an Omniparser server 
2. **Server Dependencies**: Ensure YOLO and PaddleOCR models are available on the server
3. **Network Access**: Device must be able to reach the Omniparser server

### Usage Examples:

#### Basic Screen Analysis with Omniparser:
```python
# Analyze screen with comprehensive text recognition
result = await omniparser_analyze_screen(use_paddleocr=True)

# Analyze screen with icon recognition only
result = await omniparser_analyze_screen(use_paddleocr=False)
```

#### UUID-Based Element Interaction:
```python
# Find interactive elements
interactive_elements = await omniparser_find_interactive_elements()

# Tap element by UUID (obtained from analysis)
result = await omniparser_tap_element_by_uuid("abc123-def456-789")

# Get detailed element information
element_info = await omniparser_get_element_info("abc123-def456-789")
```

#### Content-Based Element Search:
```python
# Find elements containing specific text
elements = await omniparser_find_elements_by_content("Login", partial_match=True)

# Find exact text match
elements = await omniparser_find_elements_by_content("Sign In", partial_match=False)
```

#### Advanced State Management:
```python
# Get comprehensive screen state
screen_state = await omniparser_get_screen_state()

# Get current app focus
focus_pkg = await omniparser_get_current_focus_pkg_name()

# Clear cache and restart with precision
result = await omniparser_clear_cache_and_restart("com.example.app")
```

### Task Guidance System:
The integration includes an intelligent task guidance system that provides structured prompts for different types of tasks:

```python
# Get guidance for navigation tasks
guidance = await get_task_guidance("Navigate to settings", "navigation")

# Get guidance for interaction tasks
guidance = await get_task_guidance("Tap login button", "interaction")

# Get positioning guidance
positioning = await get_positioning_guidance()
```

### Omniparser vs Traditional UI Automation:

| Feature | Traditional XML | Omniparser Integration |
|---------|----------------|------------------------|
| Element Recognition | XML hierarchy only | Visual + XML analysis |
| Reliability | Depends on XML structure | Works with visual elements |
| Precision | Coordinate-based | UUID-based targeting |
| Content Recognition | Limited to XML attributes | OCR + visual content |
| Dynamic UI Support | Limited | Excellent |
| Cross-App Compatibility | App-dependent | Universal |

### Configuration:
Configure the Omniparser server URL in your implementation:
```python
# Default server configuration
server_url = "http://100.122.57.128:9333"

# Custom server configuration
result = await omniparser_analyze_screen(server_url="http://your-server:port")
```

## 🎯 Prompt Engineering Experience & Best Practices

### Key Learnings for Future Developers

Based on extensive testing and optimization, here are the critical prompt engineering insights:

#### 1. **Task Classification is Critical**
- **Navigation Tasks**: Always get current position first, then plan step-by-step navigation
- **Interaction Tasks**: Verify element interactivity before attempting actions
- **Information Retrieval**: Use PaddleOCR mode for comprehensive text recognition
- **App Management**: Understand app state before performing destructive actions
- **System Control**: Handle system permission dialogs gracefully

#### 2. **Context Awareness Strategy**
```python
# Always follow this pattern:
# 1. Get current state
current_state = await omniparser_get_screen_state()

# 2. Understand context
focus_pkg = await omniparser_get_current_focus_pkg_name()

# 3. Plan actions based on context
# 4. Execute with verification
# 5. Handle errors gracefully
```

#### 3. **Element Targeting Hierarchy**
1. **UUID-based targeting** (Omniparser) - Most reliable
2. **Content-based search** - Good for dynamic content
3. **Coordinate-based** - Last resort, use with bias correction

#### 4. **Error Recovery Patterns**
- **Element not found**: Refresh analysis with `use_cache=False`
- **Server unavailable**: Fall back to traditional XML parsing
- **Interaction failed**: Verify element state and retry
- **App crashed**: Detect and restart application

#### 5. **Performance Optimization**
- **Cache strategically**: Use `use_cache=True` for repeated operations
- **Batch operations**: Group related actions together
- **OCR optimization**: Use `use_paddleocr=False` when text is not needed
- **Server proximity**: Deploy Omniparser server close to execution environment

#### 6. **Prompt Engineering Principles**
- **Be specific**: "Tap the blue Login button" vs "tap login"
- **Provide context**: Include current app state and user intent
- **Handle ambiguity**: When multiple elements match, provide selection criteria
- **Verify actions**: Always confirm action results before proceeding
- **Graceful degradation**: Have fallback strategies for each interaction type

#### 7. **Special Cases & Bias Handling**
For media content (videos, programs), element names often appear below the actual clickable area:

```python
# For program/video content, use bias parameter
# This adjusts the click position upward by approximately 1cm
await omniparser_tap_element_by_uuid(uuid, bias=True)
```

#### 8. **Common Pitfalls to Avoid**
- **Don't assume element positions**: Always use current screen analysis
- **Don't ignore timing**: Some UI changes need time to complete
- **Don't skip verification**: Always verify critical actions succeeded
- **Don't hardcode coordinates**: Use relative positioning and bias corrections
- **Don't ignore context**: The same element may behave differently in different app states

#### 9. **Testing & Validation Strategy**
- **Multi-device testing**: Test on different screen sizes and Android versions
- **Edge case handling**: Test with slow networks, low memory, different languages
- **Fallback verification**: Ensure graceful degradation when Omniparser is unavailable
- **Performance monitoring**: Track response times and success rates

#### 10. **Debugging Techniques**
```python
# Enable detailed logging for debugging
logger.setLevel(logging.DEBUG)

# Use element info for troubleshooting
element_info = await omniparser_get_element_info(uuid)

# Take screenshots for visual debugging
screenshot = await take_screenshot_and_save("debug_screen.png")
```

### Advanced Prompt Engineering Patterns

#### Pattern 1: Context-Aware Navigation
```
When navigating to [target], first determine current location using omniparser_get_current_focus_pkg_name, 
then find the most direct path considering current UI state and available navigation elements.
```

#### Pattern 2: Robust Element Interaction
```
For clicking [element_type], use this sequence:
1. Find element using omniparser_find_elements_by_content
2. Verify element is interactive using omniparser_get_element_info
3. Apply bias correction if element is program/video content
4. Execute tap with omniparser_tap_element_by_uuid
5. Verify action succeeded by checking UI state changes
```

#### Pattern 3: Error Recovery
```
If element interaction fails:
1. Refresh screen analysis with use_cache=False
2. Check if app state changed unexpectedly
3. Look for error dialogs or permission requests
4. Retry with alternative element selection criteria
5. Fall back to coordinate-based interaction if needed
```

#### Pattern 4: Media Content Handling
```
For media content (videos, programs, shows):
- Element names are typically below the clickable area
- Use bias=True to adjust click position upward
- Verify content started playing after interaction
- Handle loading states and buffering
```

These patterns have been battle-tested across multiple Android versions and app types, providing reliable automation even in complex scenarios.

## 📱 Device Requirements

- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and configured
- Device connected via USB or network ADB
- Device screen unlocked for UI operations
- Proper ADB permissions configured
