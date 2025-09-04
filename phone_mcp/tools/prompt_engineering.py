"""
Prompt Engineering System for Phone MCP
Provides structured prompts and task guidance for accurate task execution
"""

import json
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger("phone_mcp")


class TaskType(Enum):
    """Types of tasks that can be performed"""
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    INFORMATION_RETRIEVAL = "information_retrieval"
    APP_MANAGEMENT = "app_management"
    SYSTEM_CONTROL = "system_control"


class TaskComplexity(Enum):
    """Complexity levels for tasks"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class TaskPrompts:
    """System prompts for different task types"""
    
    SYSTEM_PROMPT = """
You are an expert Android device automation assistant using Omniparser for precise UI element recognition.

KEY PRINCIPLES:
1. PRECISION: Always use UUID-based element interaction for accuracy
2. CONTEXT AWARENESS: Understand current screen state before actions
3. VERIFICATION: Check results after each action
4. SAFETY: Avoid destructive actions without explicit confirmation
5. EFFICIENCY: Use the most direct path to achieve goals

WORKFLOW:
1. Analyze current screen state with omniparser_get_screen_state
2. Identify target elements using omniparser_find_elements_by_content or omniparser_find_interactive_elements
3. Execute actions using omniparser_tap_element_by_uuid or omniparser_execute_action_by_uuid
4. Verify results and adjust if needed

POSITIONING STRATEGY:
- For "where am i": Use omniparser_get_current_focus_pkg_name to identify current app/location
- For navigation: Analyze screen structure and identify path elements
- For interaction: Use precise UUID targeting instead of coordinate guessing

RESET STRATEGY:
- Resettable apps: Use omniparser_clear_cache_and_restart to start fresh
- Non-resettable: Get current position and navigate from there

Remember: Every UI element has a UUID. Use it for precise targeting.
"""

    NAVIGATION_PROMPT = """
NAVIGATION TASK GUIDANCE:

For navigation tasks, follow this sequence:
1. Get current focus package to understand where you are
2. Analyze screen to identify navigation elements
3. Use interactive elements to navigate step by step
4. Verify each navigation step succeeded

Common navigation patterns:
- Back button: Look for system back button or app-specific back arrow
- Home navigation: Use omniparser_get_current_focus_pkg_name then go to home
- Menu navigation: Look for hamburger menu (≡) or menu buttons
- Tab navigation: Identify tab bars at bottom or top of screen

REMEMBER: Always verify you're in the expected location after navigation.
"""

    INTERACTION_PROMPT = """
INTERACTION TASK GUIDANCE:

For interaction tasks, follow this sequence:
1. Identify interactive elements using omniparser_find_interactive_elements
2. Find specific elements by content using omniparser_find_elements_by_content
3. Use UUID-based tapping for precise interaction
4. Apply bias correction if needed for program/video content
5. Verify the interaction succeeded

Common interaction patterns:
- Buttons: Usually have clear text labels and are marked as interactive
- Input fields: May require tapping first, then text input
- Lists: Items are typically interactive, look for consistent patterns
- Toggles/switches: Usually have on/off states
- Program/Video content: Use bias=True when element names appear below clickable area

BIAS CORRECTION GUIDANCE:
- Use bias=True when tapping on program/video content (节目, 视频, 四宫格视频, etc.)
- This adjusts the click position upward to account for titles appearing below content
- Common keywords that require bias: program, video, show, episode, 节目, 视频, 电视剧, 电影

TV/VIDEO APP SPECIFIC GUIDANCE:
- For com.unitvnet.tvod app: Always check for modal dialogs/overlays first
- 四宫格跳转频道: Look for grid layout with channel options, use bias=True
- Modal dialog handling: Look for "close", "关闭", "返回", "确定" buttons
- If element not found: Try dismissing modals with back button or close buttons first
- Channel navigation: Grid patterns usually require bias correction for proper targeting

MODAL DIALOG HANDLING:
- Always check for overlay dialogs before main interaction
- Common close patterns: "×", "close", "关闭", "返回", "cancel", "取消"
- If target element not found, dismiss dialogs first then retry
- Use back button (phone_system_control with action='back') as fallback

REMEMBER: Check element interactivity before attempting to tap, and use bias for media content.
"""

    INFORMATION_RETRIEVAL_PROMPT = """
INFORMATION RETRIEVAL TASK GUIDANCE:

For information retrieval tasks:
1. Analyze current screen for relevant text elements
2. Use omniparser_analyze_screen with use_paddleocr=True for comprehensive text recognition
3. Look for specific patterns in text content
4. Navigate to information sources if needed

Common information patterns:
- Status information: Usually in top bars or dedicated status areas
- Content text: Main body areas, article text, descriptions
- Metadata: Timestamps, authors, tags, categories
- Navigation breadcrumbs: Shows current location in app hierarchy

REMEMBER: Use PaddleOCR mode for complete text recognition.
"""

    APP_MANAGEMENT_PROMPT = """
APP MANAGEMENT TASK GUIDANCE:

For app management tasks:
1. Use omniparser_get_current_focus_pkg_name to identify current app
2. For clearing cache: Use omniparser_clear_cache_and_restart
3. For app switching: Navigate to home or recent apps
4. For app installation: Use system settings or app stores

Common app management patterns:
- App settings: Usually accessible through hamburger menu or settings icon
- App switching: Use recent apps button or home screen
- App information: Long press on app icons or through settings
- App permissions: Through system settings → Apps → specific app

REMEMBER: Some actions require system permissions.
"""

    SYSTEM_CONTROL_PROMPT = """
SYSTEM CONTROL TASK GUIDANCE:

For system control tasks:
1. Navigate to system settings when needed
2. Use precise element targeting for system controls
3. Be careful with system-level changes
4. Verify changes took effect

Common system control patterns:
- Settings access: Swipe down for quick settings or use settings app
- System toggles: WiFi, Bluetooth, airplane mode usually in quick settings
- Volume controls: Physical buttons or on-screen controls
- Power management: Battery settings, power saving modes

REMEMBER: System changes may require confirmation dialogs.
"""


class TaskExecutionGuide:
    """Provides structured guidance for task execution"""
    
    def __init__(self):
        self.prompts = TaskPrompts()
    
    def get_task_guidance(self, task_type: TaskType, task_description: str) -> Dict[str, Any]:
        """Get structured guidance for a specific task"""
        
        guidance = {
            "system_prompt": self.prompts.SYSTEM_PROMPT,
            "task_type": task_type.value,
            "task_description": task_description,
            "recommended_workflow": self._get_workflow_for_task(task_type),
            "key_tools": self._get_key_tools_for_task(task_type),
            "common_pitfalls": self._get_pitfalls_for_task(task_type),
            "verification_steps": self._get_verification_steps_for_task(task_type)
        }
        
        # Add specific prompt for task type
        if task_type == TaskType.NAVIGATION:
            guidance["specific_prompt"] = self.prompts.NAVIGATION_PROMPT
        elif task_type == TaskType.INTERACTION:
            guidance["specific_prompt"] = self.prompts.INTERACTION_PROMPT
        elif task_type == TaskType.INFORMATION_RETRIEVAL:
            guidance["specific_prompt"] = self.prompts.INFORMATION_RETRIEVAL_PROMPT
        elif task_type == TaskType.APP_MANAGEMENT:
            guidance["specific_prompt"] = self.prompts.APP_MANAGEMENT_PROMPT
        elif task_type == TaskType.SYSTEM_CONTROL:
            guidance["specific_prompt"] = self.prompts.SYSTEM_CONTROL_PROMPT
        
        return guidance
    
    def _get_workflow_for_task(self, task_type: TaskType) -> List[str]:
        """Get recommended workflow steps for task type"""
        
        base_workflow = [
            "1. Get current screen state with omniparser_get_screen_state",
            "2. Analyze current context and position",
            "3. Plan the sequence of actions needed"
        ]
        
        if task_type == TaskType.NAVIGATION:
            return base_workflow + [
                "4. Identify navigation elements",
                "5. Execute navigation steps one by one",
                "6. Verify each navigation step",
                "7. Confirm final destination reached"
            ]
        elif task_type == TaskType.INTERACTION:
            return base_workflow + [
                "4. Find target interactive elements",
                "5. Execute interaction using UUID",
                "6. Verify interaction succeeded",
                "7. Handle any resulting UI changes"
            ]
        elif task_type == TaskType.INFORMATION_RETRIEVAL:
            return base_workflow + [
                "4. Analyze text elements on screen",
                "5. Navigate to information sources if needed",
                "6. Extract relevant information",
                "7. Verify information completeness"
            ]
        elif task_type == TaskType.APP_MANAGEMENT:
            return base_workflow + [
                "4. Identify current app package",
                "5. Navigate to app management options",
                "6. Execute app management action",
                "7. Verify action completed"
            ]
        elif task_type == TaskType.SYSTEM_CONTROL:
            return base_workflow + [
                "4. Navigate to system settings if needed",
                "5. Find system control elements",
                "6. Execute system control action",
                "7. Verify system state changed"
            ]
        
        return base_workflow
    
    def _get_key_tools_for_task(self, task_type: TaskType) -> List[str]:
        """Get key tools for task type"""
        
        base_tools = [
            "omniparser_get_screen_state",
            "omniparser_analyze_screen",
            "omniparser_find_interactive_elements"
        ]
        
        if task_type == TaskType.NAVIGATION:
            return base_tools + [
                "omniparser_find_elements_by_content",
                "omniparser_tap_element_by_uuid",
                "omniparser_get_current_focus_pkg_name"
            ]
        elif task_type == TaskType.INTERACTION:
            return base_tools + [
                "omniparser_tap_element_by_uuid",
                "omniparser_execute_action_by_uuid",
                "omniparser_get_element_info"
            ]
        elif task_type == TaskType.INFORMATION_RETRIEVAL:
            return base_tools + [
                "omniparser_analyze_screen (with use_paddleocr=True)",
                "omniparser_find_elements_by_content"
            ]
        elif task_type == TaskType.APP_MANAGEMENT:
            return base_tools + [
                "omniparser_get_current_focus_pkg_name",
                "omniparser_clear_cache_and_restart"
            ]
        elif task_type == TaskType.SYSTEM_CONTROL:
            return base_tools + [
                "omniparser_tap_element_by_uuid",
                "omniparser_find_elements_by_content"
            ]
        
        return base_tools
    
    def _get_pitfalls_for_task(self, task_type: TaskType) -> List[str]:
        """Get common pitfalls for task type"""
        
        base_pitfalls = [
            "Not checking current screen state before actions",
            "Using coordinate-based actions instead of UUID-based",
            "Not verifying action results"
        ]
        
        if task_type == TaskType.NAVIGATION:
            return base_pitfalls + [
                "Assuming navigation elements are always in the same place",
                "Not handling navigation failures gracefully",
                "Skipping intermediate navigation steps"
            ]
        elif task_type == TaskType.INTERACTION:
            return base_pitfalls + [
                "Tapping non-interactive elements",
                "Not handling loading states between interactions",
                "Ignoring confirmation dialogs"
            ]
        elif task_type == TaskType.INFORMATION_RETRIEVAL:
            return base_pitfalls + [
                "Missing text elements due to insufficient OCR",
                "Not scrolling to find additional information",
                "Extracting partial or incomplete information"
            ]
        elif task_type == TaskType.APP_MANAGEMENT:
            return base_pitfalls + [
                "Not identifying correct app package name",
                "Performing destructive actions without confirmation",
                "Not handling app restart properly"
            ]
        elif task_type == TaskType.SYSTEM_CONTROL:
            return base_pitfalls + [
                "Not handling system permission requests",
                "Making system changes without verification",
                "Not handling system confirmation dialogs"
            ]
        
        return base_pitfalls
    
    def _get_verification_steps_for_task(self, task_type: TaskType) -> List[str]:
        """Get verification steps for task type"""
        
        base_verification = [
            "Check current screen state after action",
            "Verify expected elements are present",
            "Confirm no error dialogs appeared"
        ]
        
        if task_type == TaskType.NAVIGATION:
            return base_verification + [
                "Verify current focus package changed if expected",
                "Check for expected navigation destination elements",
                "Confirm navigation path is correct"
            ]
        elif task_type == TaskType.INTERACTION:
            return base_verification + [
                "Check for expected UI changes after interaction",
                "Verify interaction feedback (button press, etc.)",
                "Confirm no error messages appeared"
            ]
        elif task_type == TaskType.INFORMATION_RETRIEVAL:
            return base_verification + [
                "Verify all relevant information was extracted",
                "Check information accuracy and completeness",
                "Confirm no information was missed"
            ]
        elif task_type == TaskType.APP_MANAGEMENT:
            return base_verification + [
                "Verify app state changed as expected",
                "Check app restart succeeded if applicable",
                "Confirm app management action completed"
            ]
        elif task_type == TaskType.SYSTEM_CONTROL:
            return base_verification + [
                "Check system state changed as expected",
                "Verify system settings were applied",
                "Confirm no system errors occurred"
            ]
        
        return base_verification


async def get_task_guidance(task_description: str, task_type: Optional[str] = None) -> str:
    """
    ★★★ AI TASK ORCHESTRATION - Get intelligent guidance for complex automation workflows
    
    **WHEN TO USE**: Before starting complex automation tasks to get intelligent workflow guidance.
    This tool provides structured strategies and step-by-step recommendations.
    
    **ADVANTAGES**:
    - Intelligent task decomposition into actionable steps
    - Context-aware strategy recommendations
    - Automation workflow optimization
    - Error prevention through strategic planning
    
    **TASK TYPES**:
    - "navigation": Moving between screens/apps
    - "interaction": UI element interactions
    - "app_management": App lifecycle operations
    - "system_control": System-level operations
    - "information_retrieval": Data extraction and analysis
    
    Args:
        task_description: Description of the task to be performed
        task_type: Optional task type (navigation, interaction, information_retrieval, app_management, system_control)
        
    Returns:
        JSON string with structured task guidance
    """
    try:
        guide = TaskExecutionGuide()
        
        # Auto-detect task type if not provided
        if task_type is None:
            task_type = _detect_task_type(task_description)
        
        # Convert string to TaskType enum
        try:
            task_type_enum = TaskType(task_type.lower())
        except ValueError:
            task_type_enum = TaskType.INTERACTION  # Default fallback
        
        guidance = guide.get_task_guidance(task_type_enum, task_description)
        
        return json.dumps(guidance, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get task guidance: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get task guidance: {str(e)}"
        })


async def get_tv_app_guidance(
    app_package: str = "com.unitvnet.tvod",
    target_action: str = "四宫格跳转频道"
) -> str:
    """
    ★★★ TV APP AUTOMATION GUIDANCE - Specialized guidance for TV/video app interactions
    
    Provides specific guidance for TV app automation including modal dialog handling.
    
    Args:
        app_package: Package name of the TV app (default: com.unitvnet.tvod)
        target_action: Target action to perform (default: 四宫格跳转频道)
        
    Returns:
        JSON with TV app specific guidance and workflow
    """
    try:
        tv_guidance = {
            "status": "success",
            "app_package": app_package,
            "target_action": target_action,
            "recommended_workflow": [
                "1. First launch app with: phone_app_control(action='launch', app_name='tvod')",
                "2. Wait for app to load, then analyze screen: omniparser_analyze_screen()",
                "3. Check for modal dialogs/overlays and dismiss if present",
                "4. Look for target element with: omniparser_find_elements_by_content()",
                "5. If element not found, try dismissing modals with back button",
                "6. Use bias=True when tapping on grid/channel content",
                "7. Verify action succeeded with screen analysis"
            ],
            "modal_dialog_handling": {
                "detection_keywords": ["close", "关闭", "返回", "确定", "取消", "×"],
                "dismissal_strategy": [
                    "Look for close buttons with omniparser_find_elements_by_content()",
                    "Try tapping close buttons with omniparser_tap_element_by_uuid()",
                    "Use back button as fallback: phone_system_control(action='back')",
                    "Retry main action after dialog dismissal"
                ]
            },
            "grid_interaction_tips": {
                "bias_correction": "Always use bias=True for 四宫格跳转频道 elements",
                "grid_detection": "Look for grid layout with multiple channel options",
                "targeting_strategy": "Use content-based finding rather than coordinate guessing"
            },
            "troubleshooting": {
                "element_not_found": [
                    "Check for overlay dialogs blocking the element",
                    "Dismiss any modal dialogs first",
                    "Try scrolling to reveal more content",
                    "Use omniparser_find_interactive_elements() to see all clickable items"
                ],
                "app_not_responding": [
                    "Use phone_system_control(action='back') to navigate back",
                    "Restart app if needed: phone_app_control(action='terminate') then launch again",
                    "Check device connection: phone_device_info(action='check_connection')"
                ]
            }
        }
        
        return json.dumps(tv_guidance, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"TV app guidance error: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


def _detect_task_type(task_description: str) -> str:
    """Auto-detect task type from description"""
    
    task_lower = task_description.lower()
    
    # Navigation keywords
    navigation_keywords = ["navigate", "go to", "open", "back", "home", "menu", "tab", "page", "screen"]
    if any(keyword in task_lower for keyword in navigation_keywords):
        return "navigation"
    
    # Interaction keywords
    interaction_keywords = ["tap", "click", "press", "select", "choose", "toggle", "switch", "button"]
    if any(keyword in task_lower for keyword in interaction_keywords):
        return "interaction"
    
    # Information retrieval keywords
    info_keywords = ["find", "search", "get", "read", "check", "show", "display", "tell me", "what is"]
    if any(keyword in task_lower for keyword in info_keywords):
        return "information_retrieval"
    
    # App management keywords
    app_keywords = ["install", "uninstall", "clear cache", "restart", "close", "force stop", "app"]
    if any(keyword in task_lower for keyword in app_keywords):
        return "app_management"
    
    # System control keywords
    system_keywords = ["settings", "wifi", "bluetooth", "volume", "brightness", "system", "permission"]
    if any(keyword in task_lower for keyword in system_keywords):
        return "system_control"
    
    return "interaction"  # Default fallback


def detect_bias_requirement(content: str) -> bool:
    """
    Detect if bias correction should be applied based on content.
    
    Args:
        content: Element content or task description
        
    Returns:
        True if bias correction should be applied, False otherwise
    """
    content_lower = content.lower()
    
    # Chinese keywords for program/video content
    chinese_keywords = ["节目", "视频", "四宫格视频", "电视剧", "电影", "综艺", "直播", "播放"]
    
    # English keywords for program/video content
    english_keywords = ["program", "video", "show", "episode", "movie", "tv", "play", "stream", "channel"]
    
    # Check for keywords that suggest media content
    if any(keyword in content_lower for keyword in chinese_keywords + english_keywords):
        return True
    
    # Check for patterns that suggest media content
    media_patterns = [
        "四宫格",  # Grid layout common in video apps
        "播放",    # Play
        "观看",    # Watch
        "收看",    # View
        "点播",    # On-demand
        "直播",    # Live broadcast
    ]
    
    if any(pattern in content_lower for pattern in media_patterns):
        return True
    
    return False


async def get_bias_recommendation(content: str, element_type: str = None) -> str:
    """
    Get recommendation for bias usage based on content and element type.
    
    Args:
        content: Element content text
        element_type: Type of element (optional)
        
    Returns:
        JSON string with bias recommendation
    """
    try:
        requires_bias = detect_bias_requirement(content)
        
        recommendation = {
            "requires_bias": requires_bias,
            "content_analyzed": content,
            "element_type": element_type,
            "recommendation": "Use bias=True when tapping this element" if requires_bias else "No bias correction needed",
            "reasoning": "Content indicates program/video element where title appears below clickable area" if requires_bias else "Content does not indicate media content requiring bias correction"
        }
        
        return json.dumps(recommendation, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get bias recommendation: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get bias recommendation: {str(e)}"
        })


async def get_positioning_guidance() -> str:
    """
    Get guidance for positioning and state management.
    
    Returns:
        JSON string with positioning guidance
    """
    try:
        guidance = {
            "positioning_strategy": {
                "current_location": {
                    "method": "Use omniparser_get_current_focus_pkg_name",
                    "description": "Identify current app package and context",
                    "verification": "Check returned package name matches expected location"
                },
                "screen_analysis": {
                    "method": "Use omniparser_get_screen_state",
                    "description": "Get comprehensive screen state including all elements",
                    "verification": "Verify element count and types match expectations"
                },
                "relative_positioning": {
                    "method": "Use element relationships and screen regions",
                    "description": "Understand element positions relative to screen regions",
                    "verification": "Check element bbox coordinates for positioning"
                }
            },
            "reset_strategies": {
                "resettable_apps": {
                    "method": "Use omniparser_clear_cache_and_restart",
                    "description": "Clear app cache and restart for fresh state",
                    "when_to_use": "When app state is corrupted or needs fresh start"
                },
                "non_resettable_apps": {
                    "method": "Navigate from current position",
                    "description": "Analyze current state and navigate to desired position",
                    "when_to_use": "When app state must be preserved"
                }
            },
            "best_practices": [
                "Always check current position before starting task",
                "Use screen analysis to understand context",
                "Verify positioning changes after navigation",
                "Handle unexpected states gracefully",
                "Use relative positioning when possible"
            ]
        }
        
        return json.dumps(guidance, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get positioning guidance: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to get positioning guidance: {str(e)}"
        })