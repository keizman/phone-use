# -*- coding: utf-8 -*-
"""
屏幕分析与交互接口 - 提供结构化的屏幕信息和统一的交互方法
整合多个工具，减少冗余功能，便于模型理解和使用
"""

import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

# 导入底层功能模块
from .ui import dump_ui, find_element_by_text, find_element_by_id
from .ui_enhanced import (
    find_element_by_content_desc, find_element_by_class, 
    find_clickable_elements, wait_for_element, scroll_to_element
)
from .interactions import tap_screen, swipe_screen, press_key, input_text, get_screen_size
from .media import take_screenshot

logger = logging.getLogger("phone_mcp")

class UIElement:
    """表示UI元素的类，包含其属性和交互方法
    
    属性:
        text (str): 元素文本内容
        resource_id (str): 元素资源ID
        class_name (str): 元素类名
        content_desc (str): 元素内容描述
        clickable (bool): 元素是否可点击
        bounds (str): 元素边界坐标字符串 "[x1,y1][x2,y2]"
        x1, y1, x2, y2 (int): 边界坐标值
        center_x, center_y (int): 元素中心点坐标
    
    方法:
        to_dict(): 将元素转换为字典格式
        tap(): 点击元素中心点
    """
    
    def __init__(self, element_data: Dict[str, Any]):
        """初始化UI元素
        
        Args:
            element_data: 包含元素属性的字典数据
        """
        self.data = element_data
        self.text = element_data.get("text", "")
        self.resource_id = element_data.get("resource_id", "")
        self.class_name = element_data.get("class_name", "")
        self.content_desc = element_data.get("content_desc", "")
        self.clickable = element_data.get("clickable", False)
        self.bounds = element_data.get("bounds", "")
        
        # 解析边界获取坐标
        if self.bounds and isinstance(self.bounds, str):
            try:
                coords = self.bounds.replace("[", "").replace("]", "").split(",")
                if len(coords) == 4:
                    self.x1 = int(coords[0])
                    self.y1 = int(coords[1])
                    self.x2 = int(coords[2])
                    self.y2 = int(coords[3])
                    self.center_x = (self.x1 + self.x2) // 2
                    self.center_y = (self.y1 + self.y2) // 2
            except Exception as e:
                logger.warning(f"解析元素边界失败: {self.bounds}, 错误: {str(e)}")
        elif self.bounds and isinstance(self.bounds, dict):
            # 如果bounds是字典格式，尝试从字典中提取坐标
            try:
                if all(k in self.bounds for k in ["left", "top", "right", "bottom"]):
                    self.x1 = int(self.bounds.get("left", 0))
                    self.y1 = int(self.bounds.get("top", 0))
                    self.x2 = int(self.bounds.get("right", 0))
                    self.y2 = int(self.bounds.get("bottom", 0))
                    self.center_x = (self.x1 + self.x2) // 2
                    self.center_y = (self.y1 + self.y2) // 2
            except Exception as e:
                logger.warning(f"从字典解析元素边界失败: {self.bounds}, 错误: {str(e)}")
            
    def to_dict(self) -> Dict[str, Any]:
        """将UI元素转换为字典格式，便于JSON序列化
        
        Returns:
            包含元素所有属性的字典
        """
        result = {
            "text": self.text,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "content_desc": self.content_desc,
            "clickable": self.clickable,
            "bounds": self.bounds,
        }
        
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            result["center_x"] = self.center_x
            result["center_y"] = self.center_y
            
        return result
        
    async def tap(self) -> str:
        """点击此元素的中心点
        
        Returns:
            str: 操作结果的JSON字符串，包含状态和消息
        """
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            return await tap_screen(self.center_x, self.center_y)
        return json.dumps({"status": "error", "message": "元素没有有效的坐标"})


async def get_screen_info() -> str:
    """获取当前屏幕的详细信息，包括所有可见元素、文本、坐标等
    
    此函数会获取完整的UI层次结构，解析所有元素的属性，并提取文本和可点击元素。
    
    Returns:
        str: JSON格式的屏幕信息，包含以下内容:
            - status: 操作状态 ("success" 或 "error")
            - screen_size: 屏幕尺寸 (width, height)
            - all_elements_count: 元素总数
            - clickable_elements_count: 可点击元素数量
            - text_elements_count: 文本元素数量
            - text_elements: 包含文本的元素列表
            - clickable_elements: 可点击的元素列表
            - timestamp: 获取时间戳
    
    示例:
        ```
        {
          "status": "success", 
          "screen_size": {"width": 1080, "height": 2340},
          "all_elements_count": 156,
          "text_elements": [
            {"text": "设置", "bounds": "[52,1688][228,1775]", "center_x": 140, "center_y": 1732}
          ]
        }
        ```
    """
    # 获取UI树
    ui_dump = await dump_ui()
    
    try:
        ui_data = json.loads(ui_dump)
        
        # 获取屏幕尺寸
        size_result = await get_screen_size()
        screen_size = json.loads(size_result)
        
        # 获取可点击元素
        clickable_result = await find_clickable_elements()
        clickable_elements = json.loads(clickable_result).get("elements", [])
        
        # 提取所有文本元素
        text_elements = []
        all_elements = []  # 确保变量在任何情况下都被初始化
        
        # 解析所有元素
        if "elements" in ui_data:
            for elem_data in ui_data["elements"]:
                element = UIElement(elem_data)
                all_elements.append(element.to_dict())
                
                # 如果有文本，添加到文本元素列表
                if element.text.strip():
                    text_element = {
                        "text": element.text,
                        "bounds": element.bounds
                    }
                    if hasattr(element, "center_x") and hasattr(element, "center_y"):
                        text_element["center_x"] = element.center_x
                        text_element["center_y"] = element.center_y
                    text_elements.append(text_element)
        
        result = {
            "status": "success",
            "screen_size": {
                "width": screen_size.get("width", 0),
                "height": screen_size.get("height", 0),
            },
            "all_elements_count": len(all_elements),
            "clickable_elements_count": len(clickable_elements),
            "text_elements_count": len(text_elements),
            "text_elements": text_elements,
            "clickable_elements": clickable_elements,
            "timestamp": time.time(),
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"解析UI信息时出错: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"无法获取屏幕信息: {str(e)}"
        }, ensure_ascii=False)


async def analyze_screen() -> str:
    """分析当前屏幕并提供结构化信息
    
    此函数会分析当前屏幕内容，提取有用信息并进行分类整理，包括:
    - 按区域(顶部/中部/底部)分类的文本元素
    - 检测UI模式(如列表视图、底部导航栏等)
    - 提供可能的交互建议
    
    适合用于理解屏幕内容并决定下一步操作。
    
    Returns:
        str: JSON格式的屏幕分析结果，包含以下内容:
            - status: 操作状态 ("success" 或 "error")
            - screen_size: 屏幕尺寸
            - screen_analysis: 包含文本元素、UI模式、可点击元素等分析结果
            - suggested_actions: 建议的交互操作
            - screenshot_path: 截图保存路径(如果有)
    
    示例:
        ```
        {
          "status": "success",
          "screen_analysis": {
            "text_elements": {
              "top": [{"text": "设置", "center_x": 540, "center_y": 89}],
              "middle": [{"text": "WLAN", "center_x": 270, "center_y": 614}],
              "bottom": [{"text": "确定", "center_x": 540, "center_y": 2200}]
            },
            "ui_patterns": ["list_view"],
            "notable_clickables": [...]
          },
          "suggested_actions": [
            {"action": "tap_element", "element_text": "确定"}
          ]
        }
        ```
    """
    screen_info_str = await get_screen_info()
    try:
        screen_info = json.loads(screen_info_str)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "无法解析屏幕信息JSON"})
    
    if screen_info.get("status") != "success":
        return screen_info_str
    
    # 截图用于调试/参考
    screenshot_result = await take_screenshot()
    screenshot_path = None
    if "success" in screenshot_result:
        screenshot_path = "./screen_snapshot.png"
    
    # 分析屏幕区域的文本
    texts_by_region = {
        "top": [],
        "middle": [],
        "bottom": []
    }
    
    screen_height = screen_info["screen_size"]["height"]
    top_threshold = screen_height * 0.25
    bottom_threshold = screen_height * 0.75
    
    for text_elem in screen_info.get("text_elements", []):
        y_pos = text_elem.get("center_y", 0)
        
        if y_pos < top_threshold:
            texts_by_region["top"].append(text_elem)
        elif y_pos > bottom_threshold:
            texts_by_region["bottom"].append(text_elem)
        else:
            texts_by_region["middle"].append(text_elem)
    
    # 识别UI模式
    ui_patterns = []
    
    # 检查是否为列表视图
    if len(texts_by_region["middle"]) > 3:
        middle_texts = texts_by_region["middle"]
        y_positions = [t.get("center_y") for t in middle_texts if "center_y" in t]
        
        if y_positions and len(y_positions) > 1:
            y_diffs = [abs(y_positions[i] - y_positions[i-1]) for i in range(1, len(y_positions))]
            if y_diffs and max(y_diffs) - min(y_diffs) < 20:
                ui_patterns.append("list_view")
    
    # 检查是否有底部导航栏
    bottom_clickables = []
    for e in screen_info.get("clickable_elements", []):
        try:
            bounds = e.get("bounds", "")
            if isinstance(bounds, str) and bounds:
                y_value = int(bounds.split(",")[1].replace("]", ""))
                if y_value > bottom_threshold:
                    bottom_clickables.append(e)
            elif isinstance(bounds, dict) and "top" in bounds:
                if int(bounds["top"]) > bottom_threshold:
                    bottom_clickables.append(e)
        except (IndexError, ValueError):
            continue
            
    if len(bottom_clickables) >= 3:
        ui_patterns.append("bottom_navigation")
    
    # 预测可能的操作
    suggested_actions = []
    
    # 建议点击明显的按钮
    for elem in screen_info.get("clickable_elements", []):
        if elem.get("text") and len(elem.get("text")) < 20:
            suggested_actions.append({
                "action": "tap_element", 
                "element_text": elem.get("text"),
                "description": f"点击按钮: {elem.get('text')}"
            })
    
    # 对于列表视图建议滚动
    if "list_view" in ui_patterns:
        suggested_actions.append({
            "action": "swipe", 
            "description": "向下滚动列表"
        })
    
    # 构建要返回的可点击元素列表，确保安全解析坐标
    notable_clickables = []
    for e in screen_info.get("clickable_elements", [])[:10]:
        try:
            clickable_item = {
                "text": e.get("text", ""), 
                "content_desc": e.get("content_desc", "")
            }
            
            # 如果元素已有计算好的中心点坐标，直接使用
            if "center_x" in e and "center_y" in e:
                clickable_item["center_x"] = e["center_x"]
                clickable_item["center_y"] = e["center_y"]
            # 否则尝试从bounds计算
            elif "bounds" in e:
                bounds = e["bounds"]
                if isinstance(bounds, str):
                    coords = bounds.replace("[", "").replace("]", "").split(",")
                    if len(coords) == 4:
                        x1 = int(coords[0])
                        y1 = int(coords[1])
                        x2 = int(coords[2])
                        y2 = int(coords[3])
                        clickable_item["center_x"] = (x1 + x2) // 2
                        clickable_item["center_y"] = (y1 + y2) // 2
                elif isinstance(bounds, dict) and all(k in bounds for k in ["left", "top", "right", "bottom"]):
                    x1 = int(bounds["left"])
                    y1 = int(bounds["top"])
                    x2 = int(bounds["right"])
                    y2 = int(bounds["bottom"])
                    clickable_item["center_x"] = (x1 + x2) // 2
                    clickable_item["center_y"] = (y1 + y2) // 2
            
            # 只添加有center_x和center_y的元素
            if "center_x" in clickable_item and "center_y" in clickable_item:
                notable_clickables.append(clickable_item)
        except Exception:
            continue
    
    # 构建AI友好的输出
    screen_analysis = {
        "status": "success",
        "screen_size": screen_info["screen_size"],
        "screen_analysis": {
            "text_elements": {
                "total": screen_info["text_elements_count"],
                "by_region": {
                    "top": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["top"] if "center_x" in t and "center_y" in t],
                    "middle": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["middle"] if "center_x" in t and "center_y" in t],
                    "bottom": [{"text": t.get("text"), "center_x": t.get("center_x"), "center_y": t.get("center_y")} 
                            for t in texts_by_region["bottom"] if "center_x" in t and "center_y" in t]
                }
            },
            "ui_patterns": ui_patterns,
            "clickable_count": screen_info["clickable_elements_count"],
            "notable_clickables": notable_clickables
        },
        "suggested_actions": suggested_actions,
        "screenshot_path": screenshot_path,
    }
    
    return json.dumps(screen_analysis, ensure_ascii=False, indent=2)


async def interact_with_screen(action: str, params: Dict[str, Any]) -> str:
    """执行屏幕交互动作
    
    统一的交互接口，支持多种交互方式，包括点击、滑动、按键、输入文本等。
    
    Args:
        action: 动作类型，可以是以下值之一:
            - "tap": 点击屏幕，需要坐标或元素文本
            - "swipe": 滑动屏幕，需要起点和终点坐标
            - "key": 按下按键，需要按键代码
            - "text": 输入文本，需要文本内容
            - "find": 查找元素，需要查找方法和值
            - "wait": 等待元素出现，需要查找方法、值和超时参数
            - "scroll": 滚动查找元素，需要查找方法、值和方向
        params: 动作参数字典，根据不同action需要不同的参数:
            - tap: element_text或x/y坐标
            - swipe: x1, y1, x2, y2, 可选duration
            - key: keycode
            - text: content
            - find: method, value
            - wait: method, value, timeout, interval
            - scroll: method, value, direction, max_swipes
    
    Returns:
        str: 操作结果的JSON字符串，包含状态和消息
    
    示例:
        ```python
        # 点击坐标
        result = await interact_with_screen("tap", {"x": 100, "y": 200})
        
        # 点击文本元素
        result = await interact_with_screen("tap", {"element_text": "登录"})
        
        # 滑动屏幕
        result = await interact_with_screen("swipe", 
                                           {"x1": 500, "y1": 1000, 
                                            "x2": 500, "y2": 200, 
                                            "duration": 300})
        
        # 等待元素出现
        result = await interact_with_screen("wait", 
                                           {"method": "text", 
                                            "value": "成功", 
                                            "timeout": 10})
        ```
    """
    try:
        if action == "tap":
            if "element_text" in params:
                element_result = await find_element_by_text(
                    params["element_text"], 
                    params.get("partial", True)
                )
                element_data = json.loads(element_result)
                
                if element_data.get("status") == "success" and element_data.get("elements"):
                    element = UIElement(element_data["elements"][0])
                    return await element.tap()
                else:
                    return json.dumps({
                        "status": "error", 
                        "message": f"找不到文本为 '{params['element_text']}' 的元素"
                    }, ensure_ascii=False)
            elif "x" in params and "y" in params:
                return await tap_screen(params["x"], params["y"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "缺少有效的点击参数"
                }, ensure_ascii=False)
                
        elif action == "swipe":
            if all(k in params for k in ["x1", "y1", "x2", "y2"]):
                duration = params.get("duration", 300)
                return await swipe_screen(
                    params["x1"], params["y1"], 
                    params["x2"], params["y2"], 
                    duration
                )
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "缺少滑动所需的坐标参数"
                }, ensure_ascii=False)
                
        elif action == "key":
            if "keycode" in params:
                return await press_key(params["keycode"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "缺少按键参数"
                }, ensure_ascii=False)
                
        elif action == "text":
            if "content" in params:
                return await input_text(params["content"])
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "缺少文本内容参数"
                }, ensure_ascii=False)
                
        elif action == "find":
            method = params.get("method", "text")
            value = params.get("value", "")
            
            if not value and method != "clickable":
                return json.dumps({
                    "status": "error", 
                    "message": "查找元素需要指定查找值"
                }, ensure_ascii=False)
                
            if method == "text":
                return await find_element_by_text(value, params.get("partial", True))
            elif method == "id":
                return await find_element_by_id(value)
            elif method == "content_desc":
                return await find_element_by_content_desc(value, params.get("partial", True))
            elif method == "class":
                return await find_element_by_class(value)
            elif method == "clickable":
                return await find_clickable_elements()
            else:
                return json.dumps({
                    "status": "error", 
                    "message": f"不支持的查找方法: {method}"
                }, ensure_ascii=False)
                
        elif action == "wait":
            method = params.get("method", "text")
            value = params.get("value", "")
            timeout = params.get("timeout", 30)
            interval = params.get("interval", 1.0)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "等待元素需要指定查找值"
                }, ensure_ascii=False)
                
            return await wait_for_element(method, value, timeout, interval)
            
        elif action == "scroll":
            method = params.get("method", "text")
            value = params.get("value", "")
            direction = params.get("direction", "down")
            max_swipes = params.get("max_swipes", 5)
            
            if not value:
                return json.dumps({
                    "status": "error", 
                    "message": "滚动查找需要指定查找值"
                }, ensure_ascii=False)
                
            return await scroll_to_element(method, value, direction, max_swipes)
            
        else:
            return json.dumps({
                "status": "error", 
                "message": f"不支持的交互动作: {action}"
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"执行交互动作 {action} 时出错: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"交互操作失败: {str(e)}"
        }, ensure_ascii=False) 