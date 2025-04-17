# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/your-package-name)

🌟 A powerful MCP plugin that lets you control your Android phone with ease through ADB commands.

[中文文档](README_zh.md)

## ⚡ Quick Start

### 📥 Installation
```bash
pip install phone-mcp
# or use uvx
uvx phone-mcp
```

### 🔧 Configuration

#### Cursor Setup
Configure in `~/.cursor/mcp.json`:
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

#### Claude Setup
Add to Claude configuration:
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

- 📞 **Call Functions**: Make calls, end calls, receive incoming calls
- 💬 **Messaging**: Send and receive SMS, get raw messages
- 👥 **Contacts**: Access phone contacts
- 📸 **Media**: Screenshots, screen recording, media control
- 📱 **Apps**: Launch applications, set alarms, list installed apps, terminate apps
- 🔧 **System**: Window info, app shortcuts
- 🗺️ **Maps**: Search POIs with phone numbers
- 🖱️ **UI Interaction**: Tap, swipe, type text, press keys
- 🔍 **UI Inspection**: Find elements by text, ID, class or description
- 🤖 **UI Automation**: Wait for elements, scroll to find elements, monitor UI changes
- 🧠 **Screen Analysis**: Structured screen information and unified interaction
- 🌐 **Web Browser**: Open URLs in device's default browser

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

### Communication
```bash
# Make a call
phone-cli call 1234567890

# End current call
phone-cli hangup

# Send SMS
phone-cli send-sms 1234567890 "Hello"

# Check messages
phone-cli messages --limit 10

# Get contacts
phone-cli contacts --limit 20
```

### Media & Apps
```bash
# Take screenshot
phone-cli screenshot

# Record screen
phone-cli record --duration 30

# Launch app
phone-cli app camera

# Close app
phone-cli close-app com.android.camera

# List installed apps (basic info, faster)
phone-cli list-apps

# List apps with pagination
phone-cli list-apps --page 1 --page-size 10

# List apps with detailed info (slower)
phone-cli list-apps --detailed

# Launch specific activity
phone-cli launch com.android.settings/.Settings

# Open URL in default browser
phone-cli open-url google.com
```

### Screen Analysis & Interaction
```bash
# Analyze current screen with structured information
phone-cli analyze-screen

# Unified interaction interface
phone-cli screen-interact <action> [parameters]

# Tap at coordinates
phone-cli screen-interact tap x=500 y=800

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

# Monitor UI changes
phone-cli monitor-ui --interval 1 --duration 60
```

### Location & Maps
```bash
# Search nearby POIs with phone numbers
phone-cli get-poi 116.480053,39.987005 --keywords restaurant --radius 1000
```

## 📚 Advanced Usage

### Screen-Driven Automation

The unified screen interaction interface allows intelligent agents to easily:

1. **Analyze the screen**: Get a structured analysis of UI elements and text
2. **Make decisions**: Based on detected UI patterns and available actions
3. **Execute interactions**: Through a consistent parameter system
4. **Monitor changes**: Continuously observe UI changes and respond automatically

## 📚 Documentation

For complete documentation and configuration details, visit our [GitHub repository](https://github.com/hao-cyber/phone-mcp).

## 📄 License

Apache License, Version 2.0