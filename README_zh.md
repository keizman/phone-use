# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/your-package-name)

🌟 一个强大的 MCP 手机控制插件，让您轻松通过 ADB 命令控制 Android 手机。

[English Documentation](README.md)

## ⚡ 快速开始

### 📥 安装
```bash
pip install phone-mcp
# 或使用 uvx
uvx phone-mcp
```

### 🔧 配置说明

#### Cursor 配置
在 `~/.cursor/mcp.json` 中配置：
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

#### Claude 配置
在 Claude 配置中添加：
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

使用方法：
- 在 Claude 对话中直接使用命令，例如：
  ```
   帮我给联系人hao打电话
  ```

⚠️ 使用前请确保：
- ADB 已正确安装并配置
- Android 设备已启用 USB 调试
- 设备已通过 USB 连接到电脑

## 🎯 主要功能

- 📞 **通话功能**：拨打电话、结束通话、接收来电
- 💬 **短信功能**：发送短信、接收短信、获取原始短信
- 👥 **联系人功能**：访问手机联系人
- 📸 **媒体功能**：截屏、录屏、控制媒体播放
- 📱 **应用功能**：打开应用程序、设置闹钟、列出已安装应用、关闭应用
- 🔧 **系统功能**：获取窗口信息、应用快捷方式
- 🗺️ **地图功能**：搜索周边带电话号码的POI信息
- 🖱️ **UI交互**：点击、滑动、输入文本、按键操作
- 🔍 **UI检查**：通过文本、ID、类名或描述查找元素
- 🤖 **UI自动化**：等待元素出现、滚动查找元素、监控UI变化
- 🧠 **屏幕分析**：结构化屏幕信息和统一交互接口
- 🌐 **浏览器功能**：在设备默认浏览器中打开URL

## 🛠️ 系统要求

- Python 3.7+
- 启用 USB 调试的 Android 设备
- ADB 工具

## 📋 基本命令

### 设备与连接
```bash
# 检查设备连接
phone-cli check

# 获取屏幕尺寸
phone-cli screen-interact find method=clickable
```

### 通讯
```bash
# 拨打电话
phone-cli call 10086

# 结束当前通话
phone-cli hangup

# 发送短信
phone-cli send-sms 10086 "你好"

# 查看短信
phone-cli messages --limit 10

# 获取联系人
phone-cli contacts --limit 20
```

### 媒体与应用
```bash
# 截屏
phone-cli screenshot

# 录屏
phone-cli record --duration 30

# 打开应用
phone-cli app camera

# 关闭应用
phone-cli close-app com.android.camera

# 列出已安装应用（基本信息，速度更快）
phone-cli list-apps

# 分页显示应用列表
phone-cli list-apps --page 1 --page-size 10

# 显示应用详细信息（速度较慢）
phone-cli list-apps --detailed

# 启动特定活动
phone-cli launch com.android.settings/.Settings

# 在默认浏览器中打开网页
phone-cli open-url google.com
```

### 屏幕分析与UI交互
```bash
# 分析当前屏幕并提供结构化信息
phone-cli analyze-screen

# 统一交互接口
phone-cli screen-interact <动作> [参数]

# 通过坐标点击
phone-cli screen-interact tap x=500 y=800

# 滑动手势（向下滚动）
phone-cli screen-interact swipe x1=500 y1=1000 x2=500 y2=200 duration=300

# 按键操作
phone-cli screen-interact key keycode=back

# 输入文本
phone-cli screen-interact text content="你好世界"

# 查找元素
phone-cli screen-interact find method=text value="登录" partial=true

# 等待元素出现
phone-cli screen-interact wait method=text value="成功" timeout=10

# 滚动查找元素
phone-cli screen-interact scroll method=text value="设置" direction=down max_swipes=5

# 监控UI变化
phone-cli monitor-ui --interval 1 --duration 60
```

### 位置与地图
```bash
# 搜索周边带电话号码的POI信息
phone-cli get-poi 116.480053,39.987005 --keywords 餐厅 --radius 1000
```

## 📚 高级用法

### 屏幕驱动的自动化

统一屏幕交互接口使智能代理能够轻松地：

1. **分析屏幕**：获取UI元素和文本的结构化分析
2. **做出决策**：基于检测到的UI模式和可用操作
3. **执行交互**：通过一致的参数系统
4. **监控变化**：持续观察UI变化并自动响应

## 📚 详细文档

完整文档和配置说明请访问我们的 [GitHub 仓库](https://github.com/hao-cyber/phone-mcp)。

## 📄 许可证

Apache License, Version 2.0