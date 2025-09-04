# phone_mcp Usage Examples & Tool Call Chains

## Quick Start Guide

### Basic Tool Call Pattern
```
1. dump_ui() → Get screen state (auto-closes ads)
2. find_element_by_text() → Locate target element
3. tap_element() → Interact with element
```

## Example 1: Launch App and Play Content

**Task**: "打开包名 com.mobile.brasiltvmobile 播放节目 '西语手机端720资源02'"

### Tool Call Chain:
```json
[
  {
    "tool": "phone_app_control",
    "params": {
      "action": "launch_app",
      "package_name": "com.mobile.brasiltvmobile"
    },
    "purpose": "Launch the Brasil TV app"
  },
  {
    "tool": "dump_ui",
    "params": {},
    "purpose": "Get screen state after app launch (auto-detects and closes ads)"
  },
  {
    "tool": "find_element_by_text",
    "params": {
      "text": "西语手机端720资源02",
      "use_paddleocr": true
    },
    "purpose": "Search for the specific Spanish program"
  },
  {
    "tool": "tap_element",
    "params": {
      "target": "西语手机端720资源02",
      "bias": true
    },
    "purpose": "Tap the program (bias=true for media content)"
  }
]
```

### Expected Flow:
1. App launches → UI analysis → Ads auto-closed if detected
2. Program search → Text recognition finds target
3. Content tap → Video starts playing

## Example 2: Handle Complex TV App Navigation

**Task**: Navigate to channel grid and select content

### Tool Call Chain:
```json
[
  {
    "tool": "dump_ui",
    "params": {},
    "purpose": "Analyze current screen state"
  },
  {
    "tool": "get_tv_app_guidance", 
    "params": {
      "target_action": "四宫格跳转频道"
    },
    "purpose": "Get TV-specific navigation guidance"
  },
  {
    "tool": "find_element_by_text",
    "params": {
      "text": "频道",
      "use_paddleocr": true
    },
    "purpose": "Find channel navigation"
  },
  {
    "tool": "tap_element",
    "params": {
      "target": "频道",
      "bias": true
    },
    "purpose": "Navigate to channel grid"
  }
]
```

## Example 3: Error Recovery Pattern

**Task**: Handle failed operations with automatic retry

### Tool Call Chain:
```json
[
  {
    "tool": "dump_ui",
    "params": {},
    "purpose": "Get initial state"
  },
  {
    "tool": "find_element_by_text",
    "params": {
      "text": "target_content"
    },
    "purpose": "Try to find element"
  },
  {
    "tool": "phone_system_control",
    "params": {
      "action": "back"
    },
    "purpose": "Go back if element not found (dismiss modals)"
  },
  {
    "tool": "dump_ui",
    "params": {},
    "purpose": "Re-analyze after modal dismissal"
  },
  {
    "tool": "find_element_by_text",
    "params": {
      "text": "target_content"
    },
    "purpose": "Retry finding element"
  }
]
```

## Key Usage Patterns

### 🎯 Smart UI Interaction Priority
```
High Priority (★★★★★):
- dump_ui() → Always use first for screen analysis
- find_element_by_text() → Primary element search method
- tap_element() → Primary interaction method

Medium Priority (★★★):
- get_tv_app_guidance() → For TV app specific tasks
- phone_app_control() → App lifecycle management

Fallback (★★):
- phone_system_control() → System navigation as backup
```

### 🔄 Common Workflows

#### App Launch Workflow:
```
phone_app_control(action="launch_app", package_name="com.example.app")
↓
dump_ui() [auto-closes ads if detected]
↓
find_element_by_text(text="target")
↓
tap_element(target="target", bias=true if media content)
```

#### Content Search Workflow:
```
dump_ui()
↓
find_element_by_text(text="search", use_paddleocr=true)
↓ 
tap_element(target="search")
↓
phone_screen_interact(action="input_text", text="search_query")
```

#### Error Recovery Workflow:
```
Operation Fails
↓
phone_system_control(action="back") [dismiss modals]
↓
dump_ui() [re-analyze]
↓
Retry operation
```

## Parameter Guidelines

### Required Parameters by Tool:

#### phone_app_control:
```json
{
  "action": "launch_app|terminate|list_apps|get_current",
  "package_name": "required for launch_app/terminate",
  "app_name": "alternative to package_name for launch_app"
}
```

#### dump_ui:
```json
{
  "filter_package": "optional - filter by specific app"
}
```

#### find_element_by_text:
```json
{
  "text": "required - text to search for",
  "use_paddleocr": "true for Chinese/complex text"
}
```

#### tap_element:
```json
{
  "target": "required - text or UUID of element",
  "bias": "true for media content (节目, 视频, etc.)"
}
```

## Best Practices

### ✅ Do:
- Always use dump_ui() first to understand screen state
- Use bias=true for media content (programs, videos)
- Enable PaddleOCR for Chinese text recognition
- Let system auto-close ads (happens in dump_ui())
- Use specific package names when possible

### ❌ Avoid:
- Skipping screen analysis before interaction
- Using coordinates directly (use element targeting)
- Ignoring bias correction for media content
- Manual ad handling (system auto-handles)

## Troubleshooting

### Element Not Found:
1. Check if ads are blocking (system auto-handles)
2. Try phone_system_control(action="back") to dismiss modals
3. Re-run dump_ui() to refresh screen state
4. Enable use_paddleocr=true for better text recognition

### App Launch Issues:
1. Verify package name with phone_app_control(action="list_apps")
2. Check device connection
3. Try force restart if app is frozen

### Content Interaction Issues:
1. Use bias=true for media content
2. Check element.clickable property
3. Try alternative element targeting (UUID vs text)

## Complete Example: Brasil TV Automation

```json
{
  "task": "Open Brasil TV and play specific content",
  "steps": [
    {
      "step": 1,
      "tool": "phone_app_control", 
      "params": {"action": "launch_app", "package_name": "com.mobile.brasiltvmobile"},
      "expected": "App opens to main screen"
    },
    {
      "step": 2,
      "tool": "dump_ui",
      "params": {},
      "expected": "Screen analysis complete, ads auto-closed if present"
    },
    {
      "step": 3, 
      "tool": "find_element_by_text",
      "params": {"text": "西语手机端720资源02", "use_paddleocr": true},
      "expected": "Target program found in UI elements"
    },
    {
      "step": 4,
      "tool": "tap_element", 
      "params": {"target": "西语手机端720资源02", "bias": true},
      "expected": "Program starts playing"
    }
  ],
  "fallback_actions": [
    "If program not visible: scroll or navigate to program list",
    "If ads appear: system auto-handles via dump_ui()", 
    "If tap fails: retry with different element targeting"
  ]
}
```

This approach provides clear, actionable guidance for external LLMs to successfully automate Android device interactions.