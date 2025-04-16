# 📱 Phone MCP Plugin
![Downloads](https://pepy.tech/badge/your-package-name)

🌟 一个强大的 MCP 手机控制插件，让您轻松通过 ADB 命令控制 Android 手机。

## ⚡ 快速开始

### 📥 安装
```bash
uvx phone-mcp
```

### 🎯 主要功能

- 📞 **通话功能**：拨打电话、结束通话、接收来电
- 💬 **短信功能**：发送短信、接收短信
- 👥 **联系人功能**：访问手机联系人
- 📸 **媒体功能**：截屏、录屏、控制媒体播放
- 📱 **应用功能**：打开应用程序、设置闹钟
- 🔧 **系统功能**：获取窗口信息、应用快捷方式
- 🗺️ **地图功能**：搜索周边POI信息

### 🛠️ 系统要求

- Python 3.7+
- 启用 USB 调试的 Android 设备
- ADB 工具

### 📋 基本命令
```bash
# 检查设备连接
phone-cli check

# 拨打电话
phone-cli call 10086

# 发送短信
phone-cli send-sms 10086 "Hello"

# 截屏
phone-cli screenshot

# 录屏
phone-cli record

# 打开应用
phone-cli app camera
```

### 🌐 地图功能
```bash
# 搜索周边POI
phone-cli map-around 116.480053,39.987005 --keywords 餐厅 --radius 1000
```

## 📚 详细文档

完整文档和配置说明请访问我们的 [GitHub 仓库](https://github.com/hao-cyber/phone-mcp)。

## 📄 许可证

Apache License, Version 2.0