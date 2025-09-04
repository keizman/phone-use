# Bias Correction Examples for Program/Video Content

This document provides specific examples of how to use the bias correction feature for program/video content interaction.

## Overview

The bias correction feature addresses a common issue in media applications where program/video titles appear **below** the actual clickable area. This is especially common in:
- Video streaming apps
- TV program guides
- Media content browsers
- Grid-style video layouts (四宫格视频)

## When to Use Bias Correction

### Content Keywords That Require Bias
- **Chinese**: 节目, 视频, 四宫格视频, 电视剧, 电影, 综艺, 直播, 播放, 观看, 收看, 点播
- **English**: program, video, show, episode, movie, tv, play, stream, channel

### Visual Patterns That Require Bias
- Grid layouts with thumbnails and titles below
- Video cards with title text underneath
- Program listings with descriptions below images
- Media content where text appears under clickable areas

## Usage Examples

### Example 1: Video App Navigation
```python
# 1. Enter video app
await omniparser_get_current_focus_pkg_name()  # Get current app

# 2. Find video content
elements = await omniparser_find_elements_by_content("四宫格视频", partial_match=True)

# 3. Check if bias is needed
bias_rec = await get_bias_recommendation("四宫格视频")
# Returns: {"requires_bias": true, "recommendation": "Use bias=True when tapping this element"}

# 4. Tap with bias correction
if elements:
    uuid = elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(uuid, bias=True)
```

### Example 2: Program Selection
```python
# Find program content
programs = await omniparser_find_elements_by_content("电视剧", partial_match=True)

# For each program, apply bias correction
for program in programs:
    uuid = program["uuid"]
    content = program["content"]
    
    # Check if bias is needed
    needs_bias = detect_bias_requirement(content)
    
    if needs_bias:
        await omniparser_tap_element_by_uuid(uuid, bias=True)
    else:
        await omniparser_tap_element_by_uuid(uuid, bias=False)
```

### Example 3: Complete Video Playback Flow
```python
async def play_video_with_bias_correction():
    """Complete example of video playback with bias correction"""
    
    # Step 1: Get current screen state
    screen_state = await omniparser_get_screen_state()
    
    # Step 2: Find video content
    video_elements = await omniparser_find_elements_by_content("视频", partial_match=True)
    
    for video in video_elements:
        uuid = video["uuid"]
        content = video["content"]
        
        # Step 3: Check if bias correction is needed
        bias_rec = await get_bias_recommendation(content)
        bias_needed = json.loads(bias_rec)["requires_bias"]
        
        print(f"Video: {content}, Bias needed: {bias_needed}")
        
        # Step 4: Tap with appropriate bias setting
        if bias_needed:
            result = await omniparser_tap_element_by_uuid(uuid, bias=True)
            print(f"Tapped with bias: {result}")
        else:
            result = await omniparser_tap_element_by_uuid(uuid, bias=False)
            print(f"Tapped without bias: {result}")
        
        # Step 5: Verify playback started
        await asyncio.sleep(2)  # Wait for playback to start
        
        # Check if video is playing
        current_screen = await omniparser_analyze_screen()
        # Look for playback indicators
        
        break  # Exit after first video for example
```

## Technical Details

### Bias Calculation
The bias correction applies an upward offset to the calculated tap coordinates:
- **Calculation**: `y_offset = screen_height * 0.02` (2% of screen height)
- **Typical offset**: ~40 pixels on a 1920px high screen
- **Direction**: Upward (y coordinate reduced)

### Bias Correction Formula
```python
def apply_bias_correction(x, y, screen_height):
    bias_pixels = int(screen_height * 0.02)
    y_corrected = max(0, y - bias_pixels)
    return x, y_corrected
```

## MCP Tool Integration

### New Tool Functions with Bias Support
- `omniparser_tap_element_by_uuid(uuid, bias=False)` - Tap with optional bias
- `omniparser_execute_action_by_uuid(uuid, action, bias=False)` - Execute action with bias
- `get_bias_recommendation(content, element_type=None)` - Get bias recommendation

### Prompt Engineering Integration
The system automatically detects when bias should be applied and provides guidance:

```python
# Get task guidance that includes bias recommendations
guidance = await get_task_guidance("点击四宫格视频进行播放", "interaction")
# Returns structured guidance including bias correction recommendations
```

## Common Scenarios

### Scenario 1: TV Program Guide
```python
# Find TV programs
programs = await omniparser_find_elements_by_content("电视剧", partial_match=True)

# Apply bias for program selection
for program in programs:
    # Program titles are typically below the clickable thumbnail
    await omniparser_tap_element_by_uuid(program["uuid"], bias=True)
```

### Scenario 2: Video Streaming Grid
```python
# Find videos in grid layout
videos = await omniparser_find_elements_by_content("四宫格视频", partial_match=True)

# Grid layouts typically have titles below thumbnails
for video in videos:
    await omniparser_tap_element_by_uuid(video["uuid"], bias=True)
```

### Scenario 3: Movie Selection
```python
# Find movies
movies = await omniparser_find_elements_by_content("电影", partial_match=True)

# Movie titles are usually below poster images
for movie in movies:
    await omniparser_tap_element_by_uuid(movie["uuid"], bias=True)
```

## Best Practices

### 1. Always Check Bias Requirement
```python
# Before tapping, check if bias is needed
bias_rec = await get_bias_recommendation(element_content)
bias_needed = json.loads(bias_rec)["requires_bias"]
```

### 2. Use Proper Error Handling
```python
try:
    result = await omniparser_tap_element_by_uuid(uuid, bias=True)
    if "success" in result:
        print("Video tapped successfully with bias correction")
    else:
        # Retry without bias if needed
        result = await omniparser_tap_element_by_uuid(uuid, bias=False)
except Exception as e:
    print(f"Error tapping video element: {e}")
```

### 3. Verify Actions After Bias Correction
```python
# After tapping with bias, verify the action succeeded
await omniparser_tap_element_by_uuid(uuid, bias=True)
await asyncio.sleep(1)  # Wait for UI response

# Check if expected UI changes occurred
new_screen = await omniparser_analyze_screen()
# Verify playback started or navigation occurred
```

## Troubleshooting

### Issue: Bias correction not working
**Solution**: Adjust bias calculation or use coordinate-based fallback
```python
# If bias correction fails, try coordinate-based approach
if not success_with_bias:
    # Get element coordinates and manually adjust
    element_info = await omniparser_get_element_info(uuid)
    # Apply custom offset based on specific app behavior
```

### Issue: Element not found after bias application
**Solution**: Verify element detection and screen state
```python
# Refresh screen analysis
await omniparser_analyze_screen(use_cache=False)
# Re-find elements
elements = await omniparser_find_elements_by_content(content)
```

### Issue: Bias applied to wrong element type
**Solution**: Use content-based detection
```python
# Use the built-in detection function
if detect_bias_requirement(element_content):
    await omniparser_tap_element_by_uuid(uuid, bias=True)
else:
    await omniparser_tap_element_by_uuid(uuid, bias=False)
```

## Integration with LLM Prompts

### Prompt Template for LLM
```
When tapping on program/video content:
1. Check if the content contains keywords like 节目, 视频, 四宫格视频, 电视剧, 电影
2. If yes, use bias=True in omniparser_tap_element_by_uuid
3. If no, use bias=False (default)

Example:
- "点击四宫格视频播放" → use bias=True
- "点击设置按钮" → use bias=False
```

This bias correction feature significantly improves the accuracy of interactions with media content, ensuring that clicks target the correct clickable areas rather than the text labels below them.