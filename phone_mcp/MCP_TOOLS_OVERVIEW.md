# Phone MCP Tools Overview

## Global Capabilities & Common Workflows

This document provides a comprehensive overview of phone_mcp tools and their common usage patterns to help LLMs efficiently accomplish multi-step tasks.

### Quick Reference for Common Workflows

#### 🔄 App Management Workflows

**1. Get Current App → Clear Cache → Restart**
```
1. get_current_window() → extract package_name
2. clear_app_data(package_name) → clear cache/data
3. launch_app_activity(package_name) → restart app
```

**2. One-Step Cache Clear & Restart**
```
1. get_current_window() → extract package_name
2. clear_cache_and_restart(package_name) → clear & restart in one step
```

**3. Force Restart Without Data Loss**
```
1. get_current_window() → extract package_name
2. force_restart_app(package_name) → stop & restart keeping data
```

#### 📱 Device Control Workflows

**1. Take Screenshot → Analyze → Act**
```
1. take_screenshot_and_save(path) → capture current state
2. analyze_screen() → understand screen content
3. interact_with_screen(action) → perform actions
```

**2. Monitor UI Changes**
```
1. mcp_monitor_ui_changes() → wait for specific changes
2. analyze_screen() → verify expected state
3. interact_with_screen() → continue workflow
```

## Tool Categories

### 📊 System Information & Current State
- **get_current_window()** - Get current app package name & window info
- **list_installed_apps()** - List all installed applications
- **adb_list_packages()** - List packages with filtering options
- **check_device_connection()** - Verify device connectivity

### 🔧 App Management & Control
- **launch_app_activity()** - Start apps or specific activities
- **clear_app_data()** - Clear app cache/data
- **force_stop_app()** - Force stop running apps
- **clear_cache_and_restart()** - Clear data and restart (combined)
- **force_restart_app()** - Force stop and restart (no data loss)
- **adb_install()** - Install APK files
- **adb_uninstall()** - Uninstall applications

### 🖼️ Screen Interaction & Analysis
- **take_screenshot_and_save()** - Capture screen to file
- **analyze_screen()** - AI-powered screen analysis
- **interact_with_screen()** - Perform taps, swipes, text input
- **mcp_monitor_ui_changes()** - Wait for UI changes

### 📁 File Operations
- **adb_pull()** - Download files from device
- **adb_push()** - Upload files to device

### 🏠 Navigation & System Actions
- **go_to_home()** - Navigate to home screen
- **open_settings()** - Open Android Settings
- **open_url()** - Open URLs in browser

### 🎵 Media & Recording
- **start_screen_recording()** - Record screen activity
- **play_media()** - Play media files

### 📍 Location & Maps (if API available)
- **get_phone_numbers_from_poi()** - Get POI contact info

## Best Practices for LLMs

### 1. **Always Check Device Connection First**
Most tools automatically check device connection, but for workflows start with `check_device_connection()`.

### 2. **Extract Package Names from get_current_window()**
When working with the current app, use `get_current_window()` to get the package name, then use it in subsequent operations.

### 3. **Use Combined Tools for Efficiency**
- Use `clear_cache_and_restart()` instead of separate clear + launch
- Use `force_restart_app()` for restart without data loss

### 4. **Handle JSON Responses**
All tools return JSON responses. Parse the `status` field to check success/failure.

### 5. **Common Parameter Patterns**
- `package_name`: Use format like "com.example.app" 
- `package_component`: Use format like "com.example.app/.MainActivity"
- `device_id`: Optional, only needed for multi-device scenarios

## Example Scenarios

### Scenario 1: "Clear current app's cache and restart it"
```
Step 1: get_current_window()
Step 2: Parse JSON response to get package_name
Step 3: clear_cache_and_restart(package_name)
```

### Scenario 2: "Take screenshot and analyze what's on screen"
```
Step 1: take_screenshot_and_save("/tmp/screen.png")
Step 2: analyze_screen()
```

### Scenario 3: "Install APK and launch the app"
```
Step 1: adb_install("/path/to/app.apk")
Step 2: Extract package name from install response
Step 3: launch_app_activity(package_name)
```

### Scenario 4: "Restart frozen app without losing data"
```
Step 1: get_current_window()
Step 2: force_restart_app(package_name)
```

## Tool Return Formats

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

### get_current_window() Response
```json
{
  "package_name": "com.example.app",
  "current_focus": "Window details",
  "activity_name": ".MainActivity",
  "screen_state": "on"
}
```

## Quick Decision Tree

**Need to work with current app?**
→ Start with `get_current_window()`

**Need to clear app data?**
→ Use `clear_cache_and_restart()` for full reset
→ Use `force_restart_app()` to restart without data loss

**Need to interact with screen?**
→ Use `analyze_screen()` first to understand content
→ Then use `interact_with_screen()` for actions

**Need to install/manage apps?**
→ Use `adb_install()` / `adb_uninstall()` / `list_installed_apps()`

**Need to wait for UI changes?**
→ Use `mcp_monitor_ui_changes()` with specific conditions

This overview enables LLMs to quickly identify the right tools and workflows for any phone automation task.