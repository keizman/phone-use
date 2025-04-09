# Phone MCP Plugin

A phone control plugin for MCP that allows you to control your Android phone through ADB commands to connect any human.

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
phone-cli message 1234567890 "Hello from CLI"

# Check recent text messages
phone-cli messages

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

### Media Functions
- `take_screenshot`: Capture screen
- `start_screen_recording`: Record screen
- `play_media`: Control media playback

### App Functions
- `open_app`: Launch applications
- `set_alarm`: Create an alarm

## Development

To contribute to this project:

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Make your changes
4. Run tests: `pytest`

## License

MIT License 