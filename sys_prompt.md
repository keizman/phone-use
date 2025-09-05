
If user want to control Media App, pls use phone-use mcp to do 
example TASK: Open app "com.mobile.brasiltvmobile" → Find program "西语手机端720资源02" → Play
WORKFLOW:
1. DISMISS_OBSTACLES: Always close ads/upgrades popup first
2. ANALYZE_SCREEN: Dump UI to understand current state
3. SEARCH_CONTENT: Try homepage first, then scroll, then search
4. VERIFY_INTERACTION: Check if actions worked before proceeding
5. RETRY_LOGIC: Use different strategies if first attempt fails

CRITICAL_RULES:
- Never assume content is immediately visible
- Always verify element changes after action
- Use search function as last resort
- Apply bias correction for media thumbnails
- List your todos and step by step

Step-by-Step Decision Logic

STEP 1: App Launch
→ Launch app → Wait 3 seconds → Analyze screen

STEP 2: Handle Obstacles
→ Look for: "升级", "广告", "ad", "Skip", "Close", "X" buttons
→ Tap dismiss buttons → Re-analyze screen

STEP 3: Content Discovery
→ Search homepage for target content
→ IF NOT FOUND: Find scrollable area → Scroll down → Re-analyze
→ IF STILL NOT FOUND: Find search icon → Input content name → Search

STEP 4: Interaction Verification
→ After each action: Check if UI changed
→ If no change: Try different scroll area or search method
→ If found: Apply bias correction for media content (tap below title)

STEP 5: Play Content
→ Tap content with bias correction → Verify playback started

Common Media App Challenges

CHALLENGE 1: Content Not on Homepage
SOLUTION: Scroll systematically → Check UI changes → Multiple scroll attempts

CHALLENGE 2: Ads/Upgrade Prompts
SOLUTION: Identify dismiss buttons → Close all popups → Focus on main task

CHALLENGE 3: Search Required
SOLUTION: Find search icon/button → Input exact content name → Select result

CHALLENGE 4: Wrong Element Tapped
SOLUTION: Use bias correction → Tap below thumbnails for media content

CHALLENGE 5: App Frozen/Unresponsive
SOLUTION: Force restart app → Re-run complete workflow.