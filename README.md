# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/your-package-name)

🌟 A powerful MCP plugin that lets you control your Android phone with ease through ADB commands.

[中文文档](README_zh.md)

## ⚡ Quick Start

### 📥 Installation
```bash
uvx phone-mcp
```

### 🎯 Key Features

- 📞 **Call Functions**: Make calls, end calls, receive incoming calls
- 💬 **Messaging**: Send and receive SMS
- 👥 **Contacts**: Access phone contacts
- 📸 **Media**: Screenshots, screen recording, media control
- 📱 **Apps**: Launch applications, set alarms
- 🔧 **System**: Window info, app shortcuts
- 🗺️ **Maps**: Search POIs with phone numbers

### 🛠️ Requirements

- Python 3.7+
- Android device with USB debugging enabled
- ADB tools

### 📋 Basic Commands
```bash
# Check device connection
phone-cli check

# Make a call
phone-cli call 1234567890

# Send SMS
phone-cli send-sms 1234567890 "Hello"

# Take screenshot
phone-cli screenshot

# Record screen
phone-cli record

# Launch app
phone-cli app camera
```

### 🌐 Map Features
```bash
# Search nearby POIs
phone-cli map-around 116.480053,39.987005 --keywords restaurant --radius 1000
```

## 📚 Documentation

For complete documentation and configuration details, visit our [GitHub repository](https://github.com/hao-cyber/phone-mcp).

## 📄 License

Apache License, Version 2.0