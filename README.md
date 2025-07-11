# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/phone-mcp)

🌟 A powerful MCP plugin that lets you control your Android phone with ease through ADB commands.

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

## 📱 Device Requirements

- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and configured
- Device connected via USB or network ADB
- Device screen unlocked for UI operations
- Proper ADB permissions configured
