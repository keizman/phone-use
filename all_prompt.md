  当前的MCP tools太多了，可能导致外部LLM无法正常选用tool，请你：

  1. 智能分层简化策略
  - 保留Omniparser全部专业功能 - 这是核心竞争力，不能简化
  - 合并基础重复工具 - 只合并功能相似的基础ADB操作
  - 按使用频率分组 - 高频工具保持独立，低频工具可以合并
  - 保持专业工具独立性 - 视觉识别、prompt工程等专业功能保持独立

  2. 分层工具架构设计
  【核心专业层】- 保持独立，突出专业性
  - omniparser_analyze_screen (视觉分析主工具)
  - omniparser_tap_element_by_uuid (精确交互主工具)
  - omniparser_execute_action_by_uuid (高级交互工具)
  - get_task_guidance (AI任务指导)

  【常用功能层】- 适度合并，保持便利性
  - phone_basic_interaction (基础tap/swipe/input，非视觉)
  - phone_app_management (应用启动/停止/列表)
  - phone_system_control (系统按键/设置/导航)

  【辅助工具层】- 合并同类，减少选择
  - phone_file_operations (文件传输/APK安装/截图)
  - phone_info_and_debug (设备信息/连接检查/调试)

  3. 增强Prompt设计原则
  - 功能优先级明确: 用★★★标记主要工具，★★次要工具，★辅助工具
  - 使用场景描述: 每个工具明确说明"什么时候用这个工具"
  - 工具选择指引: 提供"如果你想要...，请使用..."的明确指导
  - 避免功能重叠: 明确说明工具间的边界和选择标准

  4. 具体实施要求
  - Omniparser工具: 增强prompt突出视觉识别优势，明确与普通点击的区别
  - 基础工具合并: 将android_tap_coordinates等基础坐标工具合并到phone_basic_interaction
  - prompt工程独立: get_task_guidance等AI辅助工具保持独立，突出AI协作价值
  - 错误处理统一: 所有工具提供一致的错误处理和fallback机制

  5. LLM选择指导增强
  - 每个工具的docstring开头用大写粗体说明核心用途
  - 提供决策树：屏幕交互→优先Omniparser，文件操作→file_operations
  - 明确工具能力边界，避免LLM误选工具
  - 提供使用优先级：专业工具>通用工具>调试工具

  期望效果:
  - 工具数量从30+减少到12-15个
  - 保留所有Omniparser核心功能的专业性
  - 提供清晰的工具选择指导
  - 维持高级功能的便利性


-----