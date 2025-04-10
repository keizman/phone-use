# Phone MCP 插件

一个 MCP 手机控制插件，允许您通过 ADB 命令控制 Android 手机，连接任何人类。

## 在 Claude 和 Cursor 中使用 Phone MCP

### 安装
```bash
uvx phone-mcp
```

### Cursor 配置
在 `~/.cursor/mcp.json` 中配置：
```json
"phone-mcp": {
    "command": "uvx",
    "args": [
        "phone-mcp"
    ]
}
```

### 在 Claude 中使用
Claude 可以直接调用以下手机控制功能：

- **通话功能**：拨打电话、结束通话、接收来电
- **短信功能**：发送短信、接收短信
- **联系人功能**：访问手机联系人
- **媒体功能**：截屏、录屏、控制媒体播放
- **应用功能**：打开应用程序、设置闹钟
- **系统功能**：获取窗口信息、应用快捷方式、启动特定活动
- **地图功能**：搜索指定位置周边的POI信息

### 示例命令
在 Claude 对话中直接使用：
- 检查设备连接：`mcp_phone_mcp_check_device_connection`
- 拨打电话：`mcp_phone_mcp_call_number`
- 发送短信：`mcp_phone_mcp_send_text_message`
- 获取联系人：`mcp_phone_mcp_get_contacts`
- 截取屏幕：`mcp_phone_mcp_take_screenshot`
- 获取应用快捷方式：`mcp_phone_mcp_get_app_shortcuts`
- 获取窗口信息：`mcp_phone_mcp_get_current_window`
- 启动特定活动：`mcp_phone_mcp_launch_activity`
- 搜索POI信息：`mcp_amap_maps_maps_get_poi_info_by_location`

无需额外配置。只要正确安装和配置了 ADB，Claude 就可以直接控制您的 Android 设备。

## 安装

从 PyPI 安装：

```bash
pip install phone-mcp
```

或使用 UVX 安装：

```bash
uvx phone-mcp
```

## 要求

- Python 3.7+
- 启用 USB 调试的 Android 设备
- 在您的系统上安装并配置 ADB

## ADB 设置（必需）

本插件需要在您的计算机上安装 ADB（Android Debug Bridge）并正确连接到您的 Android 设备。

### 安装 ADB

1. **Windows**：
   - 从 Google 下载 [Platform Tools](https://developer.android.com/tools/releases/platform-tools)
   - 将 zip 文件解压到计算机上的某个位置（例如 `C:\android-sdk`）
   - 将 Platform Tools 目录添加到 PATH 环境变量

2. **macOS**：
   - 通过 Homebrew 安装：`brew install android-platform-tools`
   - 或从上述链接下载 Platform Tools

3. **Linux**：
   - Ubuntu/Debian：`sudo apt-get install adb`
   - Fedora：`sudo dnf install android-tools`
   - 或从上述链接下载 Platform Tools

### 连接您的 Android 设备

1. **启用 USB 调试**：
   - 在 Android 设备上，转到设置 > 关于手机
   - 点击"版本号"七次以启用开发者选项
   - 返回设置 > 系统 > 开发者选项
   - 启用"USB 调试"

2. **连接设备**：
   - 使用 USB 数据线将手机连接到计算机
   - 在手机上接受 USB 调试授权提示
   - 在终端/命令提示符中运行 `adb devices` 验证连接
   - 您应该看到您的设备列为"device"（而不是"unauthorized"或"offline"）

3. **故障排除**：
   - 如果您的设备显示为"unauthorized"，请检查手机上是否有提示
   - 如果未显示任何设备，请尝试：
     - 更换 USB 数据线或端口
     - 重启 ADB 服务器，运行 `adb kill-server` 然后 `adb start-server`
     - 安装制造商特定的 USB 驱动程序（Windows）

### 验证连接

在使用此插件之前，验证 ADB 能否检测到您的设备：

```bash
# 检查设备是否正确连接
adb devices

# 预期输出：
# List of devices attached
# XXXXXXXX    device
```

## 配置

插件包含几个可以自定义的配置选项：

### 国家代码

默认情况下，拨打电话或发送信息时使用 `+86`（中国）作为国家代码。您可以通过编辑 `config.py` 文件来更改：

```python
# 在 phone_mcp/config.py 中
DEFAULT_COUNTRY_CODE = "+1"  # 更改为您的国家代码（例如，美国为"+1"）
```

### 存储路径

截图和录制路径可以自定义：

```python
# 设备上的截图存储位置
SCREENSHOT_PATH = "/sdcard/Pictures/Screenshots/"

# 设备上的屏幕录制存储位置
RECORDING_PATH = "/sdcard/Movies/"
```

### 命令行为

超时和自动重试设置：

```python
# 等待命令完成的最长时间（秒）
COMMAND_TIMEOUT = 30

# 是否自动重试连接设备
AUTO_RETRY_CONNECTION = True

# 最大连接重试次数
MAX_RETRY_COUNT = 3
```

## 功能

- 拨打和接收电话
- 发送和接收短信
- 截屏和录屏
- 控制媒体播放
- 打开应用和设置闹钟
- 检查设备连接
- 访问和管理联系人

## 使用方法

### 作为 MCP 插件使用

当作为 MCP 插件使用时，功能将通过您的 MCP 界面可用。

### 命令行界面

该软件包还提供了命令行界面，用于直接访问手机功能：

```bash
# 检查设备连接（首先使用此命令验证设置）
phone-cli check

# 拨打电话
phone-cli call 10086

# 结束当前通话
phone-cli hangup

# 发送短信
phone-cli send-sms 10086 "来自命令行的问候"

# 查看/读取最近短信
phone-cli messages --limit 10

# 获取联系人
phone-cli contacts

# 截屏
phone-cli screenshot

# 录屏（默认30秒）
phone-cli record --duration 10

# 播放/暂停媒体
phone-cli media

# 启动应用
phone-cli app camera

# 设置闹钟
phone-cli alarm 7 30 --label "起床"

# 检查来电
phone-cli incoming

# 获取窗口信息
phone-cli window

# 获取应用快捷方式
phone-cli shortcuts --package com.android.calculator2

# 启动特定活动
phone-cli launch --component com.android.settings/.Settings\$WifiSettingsActivity
# 原始命令
phone-cli launch-activity --component com.android.settings/.Settings\$WifiSettingsActivity

# 地图API命令
# 搜索POI信息
phone-cli map-around 116.480053,39.987005 --keywords 餐厅 --radius 1000
# 获取POI信息（与map-around命令功能相同）
phone-cli get-poi 116.480053,39.987005 --keywords 餐厅 --radius 1000
```

## 可用工具

### 通话功能
- `call_number`：拨打电话
- `end_call`：结束当前通话
- `receive_incoming_call`：处理来电
- `check_device_connection`：检查设备是否连接

### 短信功能
- `send_text_message`：发送短信
- `receive_text_messages`：获取最近短信

### 联系人功能
- `get_contacts`：从手机获取联系人

### 媒体功能
- `take_screenshot`：截屏
- `start_screen_recording`：录屏
- `play_media`：控制媒体播放

### 应用功能
- `open_app`：启动应用
- `set_alarm`：创建闹钟

### 系统功能
- `get_current_window`：获取当前活动窗口信息
- `get_app_shortcuts`：获取特定或所有应用的快捷方式
- `launch_activity`：使用自定义意图启动特定应用活动

### 地图功能
- `around_search`：搜索指定位置周边的POI信息
- `get_poi_info_by_location`：获取POI详细信息，包括电话号码（在CLI中可通过`map-around`或`get-poi`命令使用）

## 开发

要为此项目做贡献：

1. 克隆仓库
2. 安装开发依赖：`pip install -e ".[dev]"`
3. 进行修改
4. 运行测试：`pytest`

## 许可证

Apache License, Version 2.0