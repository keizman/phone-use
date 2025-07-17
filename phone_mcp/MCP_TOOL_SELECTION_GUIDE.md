# MCP Tool Selection Guide for LLMs

## 🎯 Quick Decision Tree

```
Need to interact with screen elements?
├─ YES → START with omniparser_analyze_screen ★★★★
│   ├─ Elements found? → omniparser_tap_element_by_uuid ★★★★
│   ├─ Complex actions? → omniparser_execute_action_by_uuid ★★★
│   └─ Omniparser fails? → phone_screen_interact ★★★ (coordinate mode)
│
├─ App lifecycle management? → phone_app_control ★★
├─ System navigation/settings? → phone_system_control ★★
├─ Communication (calls/SMS)? → phone_communication ★★
├─ File operations? → phone_file_operations ★
├─ Media/recording? → phone_media_control ★
├─ Web browsing? → phone_web_browser ★
├─ Device diagnostics? → phone_device_info ★
│
└─ Complex automation task? → get_task_guidance ★★★ FIRST
```

## 🔥 Priority Tool Classification

### ★★★★ CORE PROFESSIONAL TOOLS - Always Use First
These tools leverage advanced computer vision and AI for precise interactions:

1. **`omniparser_analyze_screen`** - PRIMARY VISUAL ANALYSIS
   - **Always start here** for any screen interaction
   - Provides visual context and element identification
   - Returns UUIDs for precise element targeting

2. **`omniparser_tap_element_by_uuid`** - PRECISION INTERACTION
   - Use after screen analysis for precise element clicking
   - Automatic bias correction for media content
   - Most reliable way to interact with UI elements

### ★★★ ADVANCED PROFESSIONAL TOOLS
3. **`omniparser_execute_action_by_uuid`** - COMPLEX INTERACTIONS
   - For long_press, double_tap, advanced gestures
   - Use when simple tap is insufficient

4. **`get_task_guidance`** - AI TASK ORCHESTRATION
   - Use before complex automation workflows
   - Provides intelligent step-by-step guidance

### ★★ SECONDARY FUNCTION TOOLS
5. **`phone_screen_interact`** - UNIFIED SCREEN FALLBACK
   - Use when Omniparser unavailable
   - Coordinate-based interactions
   - Secondary option after Omniparser tools

6. **`phone_app_control`** - APP MANAGEMENT
   - Launch, terminate, list applications
   - App lifecycle operations

7. **`phone_system_control`** - SYSTEM OPERATIONS
   - Navigation keys, settings, notifications
   - System-level controls

8. **`phone_communication`** - CALLS & MESSAGING
   - Phone calls, SMS, contact management
   - Communication functions

### ★ AUXILIARY SUPPORT TOOLS
9. **`phone_file_operations`** - FILE MANAGEMENT
   - File transfers, APK installation
   - Storage operations

10. **`phone_media_control`** - MEDIA FUNCTIONS
    - Media playback, recording, camera
    - Content creation

11. **`phone_web_browser`** - WEB OPERATIONS
    - URL opening, web search
    - Browser controls

12. **`phone_device_info`** - DEVICE DIAGNOSTICS
    - Connection status, system info
    - Device health monitoring

## 📋 Usage Guidelines

### For Screen Interactions (Most Common):
1. **ALWAYS** call `omniparser_analyze_screen` first
2. **THEN** use `omniparser_tap_element_by_uuid` with returned UUID
3. **FALLBACK** to `phone_screen_interact` if Omniparser fails
4. **NEVER** use coordinate-based tools without trying Omniparser first

### For Complex Automation:
1. **START** with `get_task_guidance` for workflow planning
2. **FOLLOW** the recommended step sequence
3. **USE** appropriate tools based on task type

### For Media Content:
1. **CONSIDER** bias correction for video/program titles
2. **USE** `omniparser_tap_element_by_uuid` with `bias=True`
3. **DETECT** bias requirements using content analysis

### Error Handling:
1. **CHECK** Omniparser server availability first
2. **FALLBACK** to coordinate-based interactions
3. **RETRY** with different parameters if needed

## 🚀 Optimization Strategies

### Tool Selection Hierarchy:
```
Visual Recognition > Coordinate Interaction > Basic Commands
Professional Tools > General Tools > Helper Tools
AI-Guided > Manual > Fallback
```

### Performance Best Practices:
1. **Visual First**: Always try Omniparser before coordinates
2. **Context Aware**: Use analysis results for subsequent actions
3. **Batch Operations**: Group related actions efficiently
4. **Error Recovery**: Implement fallback strategies

### Common Patterns:
- **Screen Analysis → Element Interaction → Verification**
- **Task Guidance → Workflow Execution → Result Checking**
- **Media Detection → Bias Correction → Precise Interaction**

## 🛠️ Tool Boundaries

### What Each Tool Should Handle:
- **Omniparser Tools**: Visual recognition, precise interaction
- **Unified Tools**: Fallback operations, coordinate-based actions
- **Specialized Tools**: Domain-specific operations (files, media, etc.)
- **AI Tools**: Task planning, bias detection, workflow guidance

### What NOT to Mix:
- Don't use basic tools when Omniparser is available
- Don't skip analysis for complex screen interactions
- Don't use file tools for screen operations
- Don't use media tools for system operations

## 📊 Success Metrics

### Tool Selection Success:
- **Primary tools used first**: >80% of screen interactions
- **Fallback usage**: <20% of operations
- **Task completion rate**: >90% with proper tool selection
- **Error rate**: <5% with guided tool usage

### Performance Indicators:
- **Analysis before action**: Always for screen tasks
- **UUID-based targeting**: Preferred over coordinates
- **Bias correction**: Applied for media content
- **Workflow guidance**: Used for complex tasks

This guide ensures optimal tool selection for reliable, efficient phone automation through intelligent prioritization and clear usage boundaries.