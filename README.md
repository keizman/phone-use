# Phone MCP Plugin

A phone control plugin for MCP that allows you to control your Android phone to connect any human.

[中文文档](README_zh.md)

## Using Phone MCP in Claude and Cursor

### Installation
```bash
uvx phone-mcp
```

### Cursor Configuration
Configure in `~/.cursor/mcp.json`:
```json
"phone-mcp": {
    "command": "uvx",
    "args": [
        "phone-mcp"
    ]
}
```

### Using in Claude
```json
"phone-mcp": {
    "command": "uvx",
    "args": [
        "phone-mcp"
    ]
}
```
Claude can directly call the following phone control functions:

- **Call Functions**: Make calls, end calls, receive incoming calls
- **Messaging Functions**: Send SMS, receive recent messages
- **Contact Functions**: Access phone contacts
- **Media Functions**: Take screenshots, record screen, control media playback
- **App Functions**: Open applications, set alarms
- **System Functions**: Get window info, app shortcuts, launch specific activities
- **Map Functions**: Search for POI information (including phone numbers) by location (requires AMap API key)

### Example Commands
Use directly in Claude conversations:
- Check device connection: `mcp_phone_mcp_check_device_connection`
- Make a phone call: `mcp_phone_mcp_call_number`
- Send a text message: `mcp_phone_mcp_send_text_message`
- Get contacts: `mcp_phone_mcp_get_contacts`
- Take a screenshot: `mcp_phone_mcp_take_screenshot`
- Get app shortcuts: `mcp_phone_mcp_get_app_shortcuts`
- Get window info: `mcp_phone_mcp_get_current_window`
- Launch specific activity: `mcp_phone_mcp_launch_activity`
- Search POIs by location: `mcp_amap_maps_maps_get_poi_info_by_location`

No additional configuration is needed. As long as ADB is properly installed and configured, Claude can directly control your Android device.

## Installation

Install the package from PyPI:

```bash
pip install phone-mcp
```

Or install with UVX:

```bash
uvx phone-mcp
```

## Requirements

- Python 3.7+
- Android device with USB debugging enabled
- ADB installed and configured on your system

## ADB Setup (Required)

This package requires ADB (Android Debug Bridge) to be installed on your computer and properly connected to your Android device.

### Installing ADB

1. **Windows**:
   - Download [Platform Tools](https://developer.android.com/tools/releases/platform-tools) from Google
   - Extract the zip file to a location on your computer (e.g., `C:\android-sdk`)
   - Add the Platform Tools directory to your PATH environment variable

2. **macOS**:
   - Install via Homebrew: `brew install android-platform-tools`
   - Or download Platform Tools from the link above

3. **Linux**:
   - Ubuntu/Debian: `sudo apt-get install adb`
   - Fedora: `sudo dnf install android-tools`
   - Or download Platform Tools from the link above

### Connecting Your Android Device

1. **Enable USB Debugging**:
   - On your Android device, go to Settings > About phone
   - Tap "Build number" seven times to enable Developer options
   - Go back to Settings > System > Developer options
   - Enable "USB debugging"

2. **Connect Device**:
   - Connect your phone to your computer with a USB cable
   - Accept the USB debugging authorization prompt on your phone
   - Verify the connection by running `adb devices` in your terminal/command prompt
   - You should see your device listed as "device" (not "unauthorized" or "offline")

3. **Troubleshooting**:
   - If your device shows as "unauthorized", check for a prompt on your phone
   - If no devices are shown, try:
     - Different USB cable or port
     - Restart ADB server with `adb kill-server` followed by `adb start-server`
     - Install manufacturer-specific USB drivers (Windows)

### Verifying Connection

Before using this package, verify that ADB can detect your device:

```bash
# Check if your device is properly connected
adb devices

# Expected output:
# List of devices attached
# XXXXXXXX    device
```

## Configuration

The plugin includes several configurable options that can be customized:

### Country Code

By default, the country code `+86` (China) is used when making calls or sending messages. You can change this by editing the `config.py` file:

```python
# In phone_mcp/config.py
DEFAULT_COUNTRY_CODE = "+1"  # Change to your country code (e.g., "+1" for US)
```

### Map API Key

To use location-based POI search features, you need to set an AMap API key:

```bash
# Set environment variable
export AMAP_MAPS_API_KEY="your_api_key_here"
```

The map features will only be enabled if this environment variable is set.

### Storage Paths

Screenshot and recording paths can be customized:

```python
# Screenshot storage location on the device
SCREENSHOT_PATH = "/sdcard/Pictures/Screenshots/"

# Screen recording storage location on the device
RECORDING_PATH = "/sdcard/Movies/"
```

### Command Behavior

Timeouts and auto-retry settings:

```python
# Maximum time (seconds) to wait for a command to complete
COMMAND_TIMEOUT = 30

# Whether to automatically retry connecting to the device
AUTO_RETRY_CONNECTION = True

# Maximum number of connection retry attempts
MAX_RETRY_COUNT = 3
```

## Features

- Make and receive phone calls
- Send and receive text messages
- Take screenshots and record screen
- Control media playback
- Open apps and set alarms
- Check device connection
- Access and manage contacts

## Usage

### Using as an MCP Plugin

When used as an MCP plugin, the functionality will be available through your MCP interface.

### Command Line Interface

The package also provides a command line interface for direct access to phone functions:

```bash
# Check device connection (use this first to verify setup)
phone-cli check

# Make a phone call
phone-cli call 1234567890

# End current call
phone-cli hangup

# Send a text message
phone-cli send-sms 1234567890 "Hello from CLI"

# Read/check recent text messages
phone-cli messages --limit 10

# Get contacts
phone-cli contacts

# Take a screenshot
phone-cli screenshot

# Record screen (default 30 seconds)
phone-cli record --duration 10

# Play/pause media
phone-cli media

# Launch an app
phone-cli app camera

# Set an alarm
phone-cli alarm 7 30 --label "Wake up"

# Check for incoming calls
phone-cli incoming

# Get window information
phone-cli window

# Get app shortcuts
phone-cli shortcuts --package com.android.calculator2

# Launch specific activity
phone-cli launch --component com.android.settings/.Settings\$WifiSettingsActivity
# Original command
phone-cli launch-activity --component com.android.settings/.Settings\$WifiSettingsActivity

# Map API commands (only available if AMAP_MAPS_API_KEY is set)
# Get POI information by location
phone-cli get-poi 116.480053,39.987005 --keywords 餐厅 --radius 1000
# Alias for get-poi command
phone-cli map-around 116.480053,39.987005 --keywords 餐厅 --radius 1000
```

## Available Tools

### Call Functions
- `call_number`: Make a phone call
- `end_call`: End the current call
- `receive_incoming_call`: Handle incoming calls
- `check_device_connection`: Check if a device is connected

### Messaging Functions
- `send_text_message`: Send an SMS
- `receive_text_messages`: Get recent messages

### Contact Functions
- `get_contacts`: Retrieve contacts from the phone

### Media Functions
- `take_screenshot`: Capture screen
- `start_screen_recording`: Record screen
- `play_media`: Control media playback

### App Functions
- `open_app`: Launch applications
- `set_alarm`: Create an alarm

### System Functions
- `get_current_window`: Get information about currently active window
- `get_app_shortcuts`: Get app shortcuts for specific or all packages
- `launch_activity`: Launch specific app activities with custom intents

### Map Functions
- `around_search`: Search for POIs around a location
- `get_poi_info_by_location`: Search for POI information including phone numbers by location (alias available as `map-around` in CLI)

## Development

To contribute to this project:

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Make your changes
4. Run tests: `pytest`

## License

Apache License, Version 2.0