# Omniparser Integration Usage Examples

This document provides comprehensive examples of how to use the new Omniparser integration for precise visual UI element recognition and interaction.

## Overview

The Omniparser integration provides a revolutionary approach to Android UI automation by using computer vision to identify UI elements with high precision. Each element receives a unique UUID for reliable targeting.

## Basic Usage Examples

### 1. Screen Analysis

```python
# Basic screen analysis with text recognition
await omniparser_analyze_screen(use_paddleocr=True)

# Analysis with icon recognition only
await omniparser_analyze_screen(use_paddleocr=False)

# Get comprehensive screen state
await omniparser_get_screen_state()
```

### 2. Element Finding

```python
# Find elements by content text
await omniparser_find_elements_by_content("Login", partial_match=True)

# Find all interactive elements
await omniparser_find_interactive_elements()

# Get element details by UUID
await omniparser_get_element_info("abc123-def456")
```

### 3. Element Interaction

```python
# Tap element by UUID
await omniparser_tap_element_by_uuid("abc123-def456")

# Execute different actions on elements
await omniparser_execute_action_by_uuid("abc123-def456", "tap")
await omniparser_execute_action_by_uuid("abc123-def456", "long_press")
```

## Advanced Usage Scenarios

### Scenario 1: Login Flow Automation

```python
# Step 1: Analyze login screen
screen_state = await omniparser_get_screen_state()

# Step 2: Find username field
username_elements = await omniparser_find_elements_by_content("Username", partial_match=True)

# Step 3: Tap username field and input text
if username_elements:
    username_uuid = username_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(username_uuid)
    await android_input_text("user@example.com")

# Step 4: Find and tap password field
password_elements = await omniparser_find_elements_by_content("Password", partial_match=True)
if password_elements:
    password_uuid = password_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(password_uuid)
    await android_input_text("password123")

# Step 5: Find and tap login button
login_elements = await omniparser_find_elements_by_content("Login", partial_match=False)
if login_elements:
    login_uuid = login_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(login_uuid)
```

### Scenario 2: App Navigation

```python
# Step 1: Get current app focus
focus_result = await omniparser_get_current_focus_pkg_name()

# Step 2: Find navigation menu
menu_elements = await omniparser_find_elements_by_content("Menu", partial_match=True)

# Step 3: Tap menu if found
if menu_elements:
    menu_uuid = menu_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(menu_uuid)

# Step 4: Find settings option
settings_elements = await omniparser_find_elements_by_content("Settings", partial_match=True)

# Step 5: Navigate to settings
if settings_elements:
    settings_uuid = settings_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(settings_uuid)
```

### Scenario 3: Form Filling

```python
# Analyze form screen
screen_analysis = await omniparser_analyze_screen(use_paddleocr=True)

# Find all interactive elements
interactive_elements = await omniparser_find_interactive_elements()

# Define form data
form_data = {
    "Name": "John Doe",
    "Email": "john@example.com",
    "Phone": "+1234567890"
}

# Fill form fields
for field_label, field_value in form_data.items():
    # Find field by label
    field_elements = await omniparser_find_elements_by_content(field_label, partial_match=True)
    
    if field_elements:
        field_uuid = field_elements[0]["uuid"]
        await omniparser_tap_element_by_uuid(field_uuid)
        await android_input_text(field_value)

# Submit form
submit_elements = await omniparser_find_elements_by_content("Submit", partial_match=False)
if submit_elements:
    submit_uuid = submit_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(submit_uuid)
```

## Task Guidance Integration

### Using Task Guidance for Navigation

```python
# Get guidance for navigation task
guidance = await get_task_guidance("Navigate to app settings", "navigation")

# Use guidance to plan navigation steps
print("Navigation guidance:", guidance)

# Execute navigation with guidance
# 1. Get current position
current_state = await omniparser_get_screen_state()

# 2. Find navigation elements
nav_elements = await omniparser_find_interactive_elements()

# 3. Look for settings-related elements
settings_elements = await omniparser_find_elements_by_content("Settings", partial_match=True)

# 4. Execute navigation
if settings_elements:
    settings_uuid = settings_elements[0]["uuid"]
    await omniparser_tap_element_by_uuid(settings_uuid)
```

### Using Task Guidance for Interaction

```python
# Get guidance for interaction task
guidance = await get_task_guidance("Tap login button and handle errors", "interaction")

# Execute interaction with error handling
try:
    # Find login button
    login_elements = await omniparser_find_elements_by_content("Login", partial_match=False)
    
    if login_elements:
        login_uuid = login_elements[0]["uuid"]
        
        # Get element info before tapping
        element_info = await omniparser_get_element_info(login_uuid)
        
        # Tap the element
        result = await omniparser_tap_element_by_uuid(login_uuid)
        
        # Verify tap succeeded
        if "success" in result:
            print("Login button tapped successfully")
        else:
            print("Login button tap failed:", result)
    else:
        print("Login button not found")

except Exception as e:
    print("Error during interaction:", str(e))
```

## Error Handling and Best Practices

### Robust Element Finding

```python
async def find_element_robust(content, max_retries=3):
    """Robust element finding with retries"""
    for attempt in range(max_retries):
        try:
            elements = await omniparser_find_elements_by_content(content, partial_match=True)
            if elements:
                return elements[0]
            
            # If not found, refresh screen analysis
            await omniparser_analyze_screen(use_paddleocr=True, use_cache=False)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
        
        # Wait before retry
        await asyncio.sleep(1)
    
    return None
```

### Safe Element Interaction

```python
async def safe_element_tap(uuid):
    """Safe element tapping with verification"""
    try:
        # Verify element exists
        element_info = await omniparser_get_element_info(uuid)
        if "error" in element_info:
            print(f"Element {uuid} not found")
            return False
        
        # Check if element is interactive
        element_data = json.loads(element_info)
        if not element_data.get("element", {}).get("interactivity", False):
            print(f"Warning: Element {uuid} is not marked as interactive")
        
        # Perform tap
        result = await omniparser_tap_element_by_uuid(uuid)
        result_data = json.loads(result)
        
        if result_data.get("status") == "success":
            print(f"Successfully tapped element {uuid}")
            return True
        else:
            print(f"Failed to tap element {uuid}: {result_data.get('message')}")
            return False
            
    except Exception as e:
        print(f"Error tapping element {uuid}: {e}")
        return False
```

## Integration with Android Computer Tools

### Combining Omniparser with Android Computer Actions

```python
# Use Omniparser to find elements, Android Computer for actions
async def hybrid_interaction_example():
    # Find button using Omniparser
    button_elements = await omniparser_find_elements_by_content("Download", partial_match=True)
    
    if button_elements:
        button_element = button_elements[0]
        
        # Get screen size
        screen_info = await android_get_screen_info()
        screen_data = json.loads(screen_info)
        
        # Calculate actual coordinates
        screen_width = screen_data["screen_size"]["width"]
        screen_height = screen_data["screen_size"]["height"]
        
        center_x = int(button_element["center_x"] * screen_width)
        center_y = int(button_element["center_y"] * screen_height)
        
        # Use Android Computer tools for interaction
        await android_tap_coordinates(center_x, center_y)
        
        # Or use long press
        await android_long_press_coordinates(center_x, center_y, 1000)
```

## Complete Example: App Reset and Navigation

```python
async def complete_app_example():
    """Complete example showing app reset and navigation"""
    
    # Step 1: Get current app focus
    focus_result = await omniparser_get_current_focus_pkg_name()
    focus_data = json.loads(focus_result)
    
    if focus_data.get("status") == "success":
        package_name = focus_data.get("package_name")
        print(f"Current app: {package_name}")
        
        # Step 2: Clear cache and restart if needed
        # (Only do this if explicitly required)
        # await omniparser_clear_cache_and_restart(package_name)
        
        # Step 3: Analyze screen state
        screen_state = await omniparser_get_screen_state()
        screen_data = json.loads(screen_state)
        
        print(f"Screen elements: {screen_data.get('summary', {}).get('total_elements', 0)}")
        
        # Step 4: Find and interact with specific elements
        # Example: Find search functionality
        search_elements = await omniparser_find_elements_by_content("Search", partial_match=True)
        
        if search_elements:
            search_uuid = search_elements[0]["uuid"]
            await omniparser_tap_element_by_uuid(search_uuid)
            
            # Input search query
            await android_input_text("example query")
            
            # Press enter
            await android_press_key("enter")
        
        # Step 5: Monitor results
        # Wait for results to appear
        await asyncio.sleep(2)
        
        # Analyze results
        results_screen = await omniparser_analyze_screen(use_paddleocr=True)
        results_data = json.loads(results_screen)
        
        print(f"Results found: {results_data.get('element_count', 0)} elements")

# Run the example
# asyncio.run(complete_app_example())
```

## Configuration and Server Setup

### Server Configuration

```python
# Configure custom Omniparser server
custom_server = "http://your-server:9333"

# Use custom server for analysis
await omniparser_analyze_screen(server_url=custom_server)

# Use custom server for element finding
await omniparser_find_elements_by_content("Login", server_url=custom_server)
```

### Error Handling for Server Issues

```python
async def check_server_health():
    """Check if Omniparser server is available"""
    try:
        # Try to analyze screen - this will check server health
        result = await omniparser_analyze_screen(use_paddleocr=False)
        result_data = json.loads(result)
        
        if result_data.get("status") == "success":
            print("Omniparser server is healthy")
            return True
        else:
            print("Omniparser server returned error:", result_data.get("message"))
            return False
            
    except Exception as e:
        print(f"Omniparser server is not available: {e}")
        return False

# Use server health check
if await check_server_health():
    # Proceed with Omniparser operations
    pass
else:
    # Fall back to traditional UI automation
    pass
```

## Performance Tips

1. **Use Caching**: Set `use_cache=True` for repeated screen analysis
2. **Optimize OCR Usage**: Use `use_paddleocr=False` for icon-only recognition when text is not needed
3. **Batch Operations**: Group multiple element operations together
4. **Server Proximity**: Use a nearby Omniparser server for better performance
5. **Element Verification**: Always verify element existence before interaction

## Troubleshooting Common Issues

### Element Not Found
```python
# If element is not found, try refreshing screen analysis
await omniparser_analyze_screen(use_cache=False)
```

### Server Connection Issues
```python
# Check server availability
server_available = await check_server_health()
if not server_available:
    # Fall back to traditional methods
    pass
```

### Coordinate Precision Issues
```python
# Use Android Computer tools for coordinate-based actions
screen_info = await android_get_screen_info()
# Calculate precise coordinates
```

This comprehensive guide should help you effectively use the Omniparser integration for precise Android UI automation.