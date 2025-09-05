"""
Enhanced UI Extractor for Phone MCP
增强版UI提取器，结合XML解析和Omniparser视觉识别

核心功能:
1. 正常模式: 使用 XML 方式定位元素并点击，执行用户任务
2. 播放状态: 使用 Omniparser 解析现有模式进行视觉识别  
3. 统一接口: 智能调度器自动选择最佳工具，对外输出一致
4. 手动选择: 支持外部指定使用的具体组件
"""

import asyncio
import json
import xml.etree.ElementTree as ET
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
from dataclasses import dataclass

from ..core import run_command, check_device_connection
from .omniparser_interface import (
    get_omniparser_client,
    get_screen_analyzer,
    get_interaction_manager,
    OmniparserClient,
    OmniparserScreenAnalyzer,
    OmniparserInteractionManager,
    OmniElement
)
from .ui_enhanced import (
    find_element_by_content_desc,
    find_element_by_class,
    find_clickable_elements,
    wait_for_element
)

logger = logging.getLogger("phone_mcp")


class ExtractionMode(Enum):
    """提取模式枚举"""
    AUTO = "auto"           # 自动选择模式
    XML_ONLY = "xml_only"   # 仅使用XML模式
    VISUAL_ONLY = "visual_only"  # 仅使用视觉模式
    HYBRID = "hybrid"       # 混合模式


class PlaybackState(Enum):
    """播放状态枚举"""
    UNKNOWN = "unknown"
    PLAYING = "playing"
    STOPPED = "stopped"


@dataclass
class UnifiedElement:
    """统一元素结构 - 兼容XML和视觉识别"""
    uuid: str
    element_type: str  # "xml" or "visual"
    name: str
    text: str
    package: str
    resource_id: str
    class_name: str
    clickable: bool
    bounds: List[float]  # 归一化坐标 [x1, y1, x2, y2]
    center_x: float      # 归一化中心X
    center_y: float      # 归一化中心Y
    confidence: float    # 识别置信度 (0.0-1.0)
    source: str         # 数据源标识
    metadata: Dict[str, Any] = None  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uuid": self.uuid,
            "element_type": self.element_type,
            "name": self.name,
            "text": self.text,
            "package": self.package,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "clickable": self.clickable,
            "bounds": self.bounds,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata or {}
        }

    def get_screen_coordinates(self, screen_width: int, screen_height: int, bias: bool = False) -> Tuple[int, int]:
        """获取实际屏幕坐标，支持偏差校正"""
        x = int(self.center_x * screen_width)
        y = int(self.center_y * screen_height)
        
        # 媒体内容偏差校正
        if bias:
            bias_pixels = int(screen_height * 0.02)  # 2% 上移
            y = max(0, y - bias_pixels)
        
        return x, y


class PlaybackDetector:
    """增强的播放状态检测器 - 多重检测机制"""
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 2.0  # 2秒缓存
    
    async def detect_playback_state(self) -> PlaybackState:
        """检测当前播放状态 - 增强版多重检测"""
        try:
            # 检查缓存
            current_time = time.time()
            if 'playback_state' in self._cache:
                cached_state, timestamp = self._cache['playback_state']
                if current_time - timestamp < self._cache_timeout:
                    return cached_state
            
            # 方法1: 检查音频flinger状态 (优化版)
            audio_active = await self._check_audio_flinger_enhanced()
            
            # 方法2: 检查Wake Locks (优化版)
            wake_lock_active = await self._check_wake_locks_enhanced()
            
            # 方法3: 检查媒体会话状态 (新增)
            media_session_active = await self._check_media_sessions()
            
            # 方法4: 检查音频焦点状态 (新增)
            audio_focus_active = await self._check_audio_focus()
            
            # 综合判断 - 增强的逻辑
            playback_indicators = [
                audio_active,
                wake_lock_active, 
                media_session_active,
                audio_focus_active
            ]
            active_count = sum(playback_indicators)
            
            if active_count >= 2:  # 至少2个指标表明播放状态
                state = PlaybackState.PLAYING
                logger.info(f"检测到播放状态 (活跃指标: {active_count}/4)")
            elif active_count == 1:
                # 单个指标可能是误判，进行二次确认
                await asyncio.sleep(0.5)
                confirm_audio = await self._check_audio_flinger_enhanced()
                state = PlaybackState.PLAYING if confirm_audio else PlaybackState.STOPPED
                logger.info(f"单指标检测，二次确认结果: {state.value}")
            else:
                state = PlaybackState.STOPPED
                logger.info("未检测到播放状态")
            
            # 缓存结果
            self._cache['playback_state'] = (state, current_time)
            return state
                
        except Exception as e:
            logger.error(f"播放状态检测失败: {e}")
            return PlaybackState.UNKNOWN
    
    async def _check_audio_flinger_enhanced(self) -> bool:
        """精确的音频flinger状态检查 - 基于用户验证的方法"""
        try:
            # 方法基于用户验证:
            # Not Playing: 1 "Standby: no" (AudioIn only)  
            # Playing: 2+ "Standby: no" (AudioIn + AudioOut)
            cmd = 'adb shell dumpsys media.audio_flinger | grep "Standby: no"'
            success, output = await run_command(cmd)
            
            if success and output.strip():
                standby_count = len([line for line in output.split('\n') 
                                   if 'Standby: no' in line.strip()])
                
                # 精确判断: 2或更多表示真正播放 (AudioIn + AudioOut)
                # 1个通常只是AudioIn (麦克风/系统音频)
                logger.debug(f"音频Flinger检测: {standby_count} 个 'Standby: no' 条目")
                return standby_count >= 2
                
        except Exception as e:
            logger.warning(f"音频flinger检测失败: {e}")
        
        return False
    
    async def _check_wake_locks_enhanced(self) -> bool:
        """精确的Wake Lock状态检查 - 基于用户验证的方法"""
        try:
            # 方法基于用户验证:
            # Not Playing: 只有 AudioIn AudioIn_A61005
            # Playing: AudioIn + AudioMix AudioOut_xxxx (新增输出锁)
            cmd = 'adb shell dumpsys power | grep -i wake | grep Audio'
            success, output = await run_command(cmd)
            
            if success and output.strip():
                lines = output.split('\n')
                audio_locks = [line.strip() for line in lines if line.strip()]
                
                # 检查是否有AudioOut或AudioMix输出锁 (表明正在播放)
                has_output_lock = any('AudioOut' in lock or 'AudioMix' in lock 
                                    for lock in audio_locks)
                
                logger.debug(f"音频Wake Lock检测: {len(audio_locks)} 个锁, 输出锁: {has_output_lock}")
                return has_output_lock
                
        except Exception as e:
            logger.warning(f"Wake Lock检测失败: {e}")
        
        return False
    
    async def _check_media_sessions(self) -> bool:
        """检查媒体会话状态 - 新增功能"""
        try:
            cmd = 'adb shell "dumpsys media_session | grep -E \\"state=|PLAYING\\""'
            success, output = await run_command(cmd)
            
            if success:
                return 'PLAYING' in output or 'state=3' in output  # 3 = PlaybackState.STATE_PLAYING
                
        except Exception as e:
            logger.warning(f"媒体会话检测失败: {e}")
        
        return False
    
    async def _check_audio_focus(self) -> bool:
        """检查音频焦点状态 - 新增功能"""
        try:
            cmd = 'adb shell "dumpsys audio | grep -E \\"Audio Focus|AUDIOFOCUS_GAIN\\""'
            success, output = await run_command(cmd)
            
            if success:
                return 'AUDIOFOCUS_GAIN' in output
                
        except Exception as e:
            logger.warning(f"音频焦点检测失败: {e}")
        
        return False

    async def verify_current_playing_state(self) -> Dict[str, Any]:
        """检查当前播放状态 - 供编程使用"""
        try:
            # 音频Flinger检测
            cmd1 = 'adb shell dumpsys media.audio_flinger | grep "Standby: no"'
            success1, output1 = await run_command(cmd1)
            audio_playing = False
            if success1:
                standby_count = len([line for line in output1.split('\n') 
                                   if 'Standby: no' in line.strip()])
                audio_playing = standby_count >= 2
            
            # Wake Lock检测
            cmd2 = 'adb shell dumpsys power | grep -i wake | grep Audio'
            success2, output2 = await run_command(cmd2)
            wake_playing = False
            if success2:
                audio_locks = [line.strip() for line in output2.split('\n') if line.strip()]
                wake_playing = any('AudioOut' in lock or 'AudioMix' in lock 
                                 for lock in audio_locks)
            
            # 简化返回结果
            is_playing = audio_playing or wake_playing
            return {
                "is_playing": is_playing,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"播放状态检测失败: {e}")
            return {"is_playing": False, "error": str(e)}


class XMLExtractor:
    """增强的XML元素提取器 - 集成ui_enhanced模块功能"""
    
    def __init__(self):
        self.xml_content = None
        self.screen_size = (1080, 1920)
        self._cache = {}
        self._cache_timeout = 5.0
        self._ui_enhanced_cache = {}  # 缓存ui_enhanced模块的结果
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        try:
            success, output = await run_command("adb shell wm size")
            if success:
                import re
                match = re.search(r'(\d+)x(\d+)', output)
                if match:
                    self.screen_size = (int(match.group(1)), int(match.group(2)))
            
            return self.screen_size
            
        except Exception as e:
            logger.error(f"获取屏幕尺寸失败: {e}")
            return self.screen_size
    
    async def get_xml_from_device(self) -> bool:
        """从设备获取UI XML"""
        try:
            logger.info("正在获取设备UI层次结构XML...")
            success, output = await run_command("adb shell uiautomator dump")
            
            if not success:
                logger.error(f"UI dump失败: {output}")
                return False
            
            # 获取dump文件路径
            import re
            match = re.search(r"UI hierchary dumped to: (.*\.xml)", output)
            if not match:
                logger.error("无法找到dump文件路径")
                return False
            
            device_file_path = match.group(1)
            
            # 创建临时文件
            import tempfile
            import os
            temp_file = os.path.join(tempfile.gettempdir(), "ui_dump.xml")
            
            # 拉取文件
            success, output = await run_command(f"adb pull {device_file_path} {temp_file}")
            if not success:
                logger.error(f"拉取dump文件失败: {output}")
                return False
            
            # 读取XML内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                self.xml_content = f.read()
            
            # 清理临时文件
            try:
                os.remove(temp_file)
            except:
                pass
            
            logger.info(f"获取XML成功，长度: {len(self.xml_content)} 字符")
            return True
            
        except Exception as e:
            logger.error(f"获取XML失败: {e}")
            return False
    
    def parse_bounds(self, bounds_str: str) -> Tuple[int, int, int, int]:
        """解析bounds字符串 '[54,34][592,75]' -> (54, 34, 592, 75)"""
        try:
            bounds_str = bounds_str.replace('[', '').replace(']', ',')
            coords = [int(x) for x in bounds_str.split(',') if x]
            if len(coords) >= 4:
                return coords[0], coords[1], coords[2], coords[3]
        except (ValueError, IndexError):
            pass
        return 0, 0, 0, 0
    
    async def extract_elements(self, use_cache: bool = True) -> List[UnifiedElement]:
        """提取XML元素"""
        # 检查缓存
        cache_key = "xml_elements"
        current_time = time.time()
        
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                logger.info("使用缓存的XML元素")
                return cached_data
        
        # 获取XML数据
        if not self.xml_content:
            if not await self.get_xml_from_device():
                return []
        
        # 获取屏幕尺寸
        screen_width, screen_height = await self.get_screen_size()
        
        try:
            logger.info("正在解析XML...")
            root = ET.fromstring(self.xml_content)
            
            elements = []
            self._extract_xml_node_recursive(root, elements, [], screen_width, screen_height)
            
            # 缓存结果
            if use_cache:
                self._cache[cache_key] = (elements, current_time)
            
            # 使用ui_enhanced模块增强元素信息
            enhanced_elements = await self._enhance_elements_with_ui_enhanced(elements)
            
            # 缓存结果
            if use_cache:
                self._cache[cache_key] = (enhanced_elements, current_time)
            
            logger.info(f"成功提取 {len(enhanced_elements)} 个增强XML元素")
            return enhanced_elements
            
        except Exception as e:
            logger.error(f"解析XML失败: {e}")
            return []
    
    def _extract_xml_node_recursive(self, node_elem, elements: List[UnifiedElement], 
                                  path: List[int], screen_width: int, screen_height: int):
        """递归提取XML节点"""
        # 跳过hierarchy根节点
        if node_elem.tag == 'hierarchy':
            for i, child in enumerate(node_elem):
                self._extract_xml_node_recursive(child, elements, [i], screen_width, screen_height)
            return
        
        # 提取当前节点属性
        attrib = node_elem.attrib
        bounds_str = attrib.get('bounds', '[0,0][0,0]')
        x1, y1, x2, y2 = self.parse_bounds(bounds_str)
        
        # 计算归一化坐标
        if screen_width > 0 and screen_height > 0:
            norm_bounds = [
                x1 / screen_width,
                y1 / screen_height,
                x2 / screen_width,
                y2 / screen_height
            ]
            center_x = (norm_bounds[0] + norm_bounds[2]) / 2
            center_y = (norm_bounds[1] + norm_bounds[3]) / 2
        else:
            norm_bounds = [0, 0, 0, 0]
            center_x, center_y = 0, 0
        
        # 创建统一元素
        text = attrib.get('text', '').strip()
        class_name = attrib.get('class', '')
        resource_id = attrib.get('resource-id', '')
        package = attrib.get('package', '')
        
        element = UnifiedElement(
            uuid=f"xml_{len(elements)}",
            element_type="xml",
            name=resource_id if resource_id else (text if text else class_name),
            text=text,
            package=package,
            resource_id=resource_id,
            class_name=class_name,
            clickable=attrib.get('clickable', 'false').lower() == 'true',
            bounds=norm_bounds,
            center_x=center_x,
            center_y=center_y,
            confidence=1.0,  # XML数据置信度为1.0
            source="xml_extractor",
            metadata={
                "path": '/'.join(map(str, path)) if path else 'root',
                "raw_bounds": bounds_str,
                "enabled": attrib.get('enabled', 'false').lower() == 'true',
                "focusable": attrib.get('focusable', 'false').lower() == 'true',
                "scrollable": attrib.get('scrollable', 'false').lower() == 'true',
                "children_count": len(list(node_elem)),
                "content_desc": attrib.get('content-desc', ''),
                "checkable": attrib.get('checkable', 'false').lower() == 'true',
                "checked": attrib.get('checked', 'false').lower() == 'true',
                "selected": attrib.get('selected', 'false').lower() == 'true',
                "screen_size": {"width": screen_width, "height": screen_height}
            }
        )
        
        elements.append(element)
        
        # 递归处理子节点
        for i, child in enumerate(node_elem):
            self._extract_xml_node_recursive(child, elements, path + [i], screen_width, screen_height)
    
    async def _enhance_elements_with_ui_enhanced(self, elements: List[UnifiedElement]) -> List[UnifiedElement]:
        """使用ui_enhanced模块功能增强元素信息"""
        try:
            enhanced_elements = []
            
            for element in elements:
                # 复制原始元素
                enhanced_element = element
                
                # 增强文本识别 - 添加content-desc信息
                if not element.text and element.metadata.get('content_desc'):
                    enhanced_element.text = element.metadata.get('content_desc', '')
                
                # 增强可点击性判断 - 基于类名推断
                if not element.clickable:
                    clickable_classes = [
                        'Button', 'ImageButton', 'CheckBox', 'RadioButton',
                        'Switch', 'ToggleButton', 'MenuItem', 'Tab', 'Chip'
                    ]
                    if any(cls in element.class_name for cls in clickable_classes):
                        enhanced_element.clickable = True
                        enhanced_element.metadata['inferred_clickable'] = True
                
                # 增强元素命名 - 智能推断名称
                if not element.name or element.name == element.class_name:
                    if element.resource_id and '/' in element.resource_id:
                        # 从resource_id中提取有意义的名称
                        id_part = element.resource_id.split('/')[-1]
                        enhanced_element.name = id_part.replace('_', ' ').title()
                    elif element.text and len(element.text.strip()) > 0:
                        enhanced_element.name = element.text.strip()[:30]  # 取前30个字符
                    elif element.metadata.get('content_desc'):
                        enhanced_element.name = element.metadata.get('content_desc', '')[:30]
                
                # 添加增强的元数据
                enhanced_element.metadata.update({
                    'enhanced_by_ui_enhanced': True,
                    'content_desc': element.metadata.get('content_desc', ''),
                    'checkable': element.metadata.get('checkable', False),
                    'checked': element.metadata.get('checked', False),
                    'selected': element.metadata.get('selected', False)
                })
                
                enhanced_elements.append(enhanced_element)
            
            logger.info(f"ui_enhanced模块增强了 {len(enhanced_elements)} 个元素")
            return enhanced_elements
            
        except Exception as e:
            logger.warning(f"ui_enhanced增强失败: {e}")
            return elements
    
    async def find_elements_by_content_desc_enhanced(self, content_desc: str, partial_match: bool = True) -> List[UnifiedElement]:
        """增强版内容描述查找 - 集成ui_enhanced模块"""
        try:
            # 使用ui_enhanced模块进行查找
            result_json = await find_element_by_content_desc(content_desc, partial_match)
            result = json.loads(result_json)
            
            if result.get("status") == "success":
                elements = []
                for elem_data in result.get("elements", []):
                    # 转换为统一元素格式
                    element = self._convert_ui_dump_to_unified_element(elem_data)
                    elements.append(element)
                
                logger.info(f"通过content_desc找到 {len(elements)} 个元素")
                return elements
            else:
                logger.warning(f"content_desc查找失败: {result.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"增强版content_desc查找失败: {e}")
            return []
    
    async def find_elements_by_class_enhanced(self, class_name: str, package_name: str = None) -> List[UnifiedElement]:
        """增强版类名查找 - 集成ui_enhanced模块"""
        try:
            # 使用ui_enhanced模块进行查找
            result_json = await find_element_by_class(class_name, package_name)
            result = json.loads(result_json)
            
            if result.get("status") == "success":
                elements = []
                for elem_data in result.get("elements", []):
                    # 转换为统一元素格式
                    element = self._convert_ui_dump_to_unified_element(elem_data)
                    elements.append(element)
                
                logger.info(f"通过class找到 {len(elements)} 个元素")
                return elements
            else:
                logger.warning(f"class查找失败: {result.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"增强版class查找失败: {e}")
            return []
    
    def _convert_ui_dump_to_unified_element(self, elem_data: Dict) -> UnifiedElement:
        """将UI dump数据转换为统一元素格式"""
        # 解析bounds信息
        bounds_str = elem_data.get('bounds', '[0,0][0,0]')
        x1, y1, x2, y2 = self.parse_bounds(bounds_str)
        
        # 计算归一化坐标
        if self.screen_size[0] > 0 and self.screen_size[1] > 0:
            norm_bounds = [
                x1 / self.screen_size[0],
                y1 / self.screen_size[1],
                x2 / self.screen_size[0],
                y2 / self.screen_size[1]
            ]
            center_x = (norm_bounds[0] + norm_bounds[2]) / 2
            center_y = (norm_bounds[1] + norm_bounds[3]) / 2
        else:
            norm_bounds = [0, 0, 0, 0]
            center_x, center_y = 0, 0
        
        return UnifiedElement(
            uuid=f"ui_enhanced_{elem_data.get('index', 0)}",
            element_type="xml",
            name=elem_data.get('resource-id', elem_data.get('text', elem_data.get('class', ''))),
            text=elem_data.get('text', ''),
            package=elem_data.get('package', ''),
            resource_id=elem_data.get('resource-id', ''),
            class_name=elem_data.get('class', ''),
            clickable=elem_data.get('clickable', False),
            bounds=norm_bounds,
            center_x=center_x,
            center_y=center_y,
            confidence=1.0,
            source="ui_enhanced_integrated",
            metadata={
                "content_desc": elem_data.get('content-desc', ''),
                "enabled": elem_data.get('enabled', False),
                "focusable": elem_data.get('focusable', False),
                "checkable": elem_data.get('checkable', False),
                "checked": elem_data.get('checked', False),
                "selected": elem_data.get('selected', False),
                "raw_bounds": bounds_str
            }
        )


class VisualExtractor:
    """视觉元素提取器 - 基于Omniparser"""
    
    def __init__(self, server_url: str = "http://100.122.57.128:9333"):
        self.server_url = server_url
        self.screen_analyzer = get_screen_analyzer(server_url)
        self._cache = {}
        self._cache_timeout = 5.0
    
    async def extract_elements(self, use_cache: bool = True) -> List[UnifiedElement]:
        """提取视觉元素"""
        # 检查缓存
        cache_key = "visual_elements"
        current_time = time.time()
        
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                logger.info("使用缓存的视觉元素")
                return cached_data
        
        try:
            # 检查Omniparser服务器健康状态
            if not await self.screen_analyzer.client.health_check():
                logger.warning("Omniparser服务器不可用")
                return []
            
            # 使用Omniparser进行屏幕分析
            analysis_result = await self.screen_analyzer.capture_and_analyze_screen(
                use_paddleocr=True, use_cache=use_cache
            )
            
            if analysis_result.get("status") != "success":
                logger.error(f"Omniparser分析失败: {analysis_result.get('message')}")
                return []
            
            # 转换为统一元素格式
            elements = []
            screen_size = analysis_result.get("screen_size", {"width": 1080, "height": 1920})
            
            for i, elem_data in enumerate(analysis_result.get("elements", [])):
                # 创建统一元素
                element = UnifiedElement(
                    uuid=elem_data.get("uuid", f"visual_{i}"),
                    element_type="visual",
                    name=elem_data.get("content", ""),
                    text=elem_data.get("content", ""),
                    package="",  # 视觉识别无包名信息
                    resource_id="",
                    class_name=elem_data.get("type", "visual_element"),
                    clickable=elem_data.get("interactivity", True),
                    bounds=elem_data.get("bbox", []),
                    center_x=elem_data.get("center_x", 0),
                    center_y=elem_data.get("center_y", 0),
                    confidence=1.0,  # Omniparser默认高置信度
                    source="omniparser",
                    metadata={
                        "omniparser_type": elem_data.get("type", ""),
                        "omniparser_source": elem_data.get("source", ""),
                        "screen_size": screen_size
                    }
                )
                elements.append(element)
            
            # 缓存结果
            if use_cache:
                self._cache[cache_key] = (elements, current_time)
            
            logger.info(f"提取到 {len(elements)} 个视觉元素")
            return elements
            
        except Exception as e:
            logger.error(f"视觉元素提取失败: {e}")
            return []


class EnhancedUIExtractor:
    """增强版UI提取器 - 统一XML和视觉识别"""
    
    def __init__(self, omniparser_url: str = "http://100.122.57.128:9333"):
        self.xml_extractor = XMLExtractor()
        self.visual_extractor = VisualExtractor(omniparser_url)
        self.playback_detector = PlaybackDetector()
        
        # 缓存管理
        self._last_extraction_mode = None
        self._unified_cache = {}
        self._cache_timeout = 3.0
    
    async def detect_optimal_mode(self) -> ExtractionMode:
        """检测最佳提取模式"""
        try:
            # 检查设备连接状态
            connection_status = await check_device_connection()
            if "ready" not in connection_status:
                logger.error("设备未连接")
                return ExtractionMode.XML_ONLY
            
            # 检查Omniparser服务器状态
            omniparser_available = await self.visual_extractor.screen_analyzer.client.health_check()
            
            # 检查播放状态
            playback_state = await self.playback_detector.detect_playback_state()
            
            if playback_state == PlaybackState.PLAYING:
                if omniparser_available:
                    logger.info("检测到播放状态，选择视觉模式")
                    return ExtractionMode.VISUAL_ONLY
                else:
                    logger.warning("播放状态但Omniparser不可用，回退到XML模式")
                    return ExtractionMode.XML_ONLY
            else:
                logger.info("非播放状态，选择XML模式")
                return ExtractionMode.XML_ONLY
                
        except Exception as e:
            logger.error(f"模式检测失败: {e}")
            return ExtractionMode.XML_ONLY
    
    async def extract_elements_unified(self, 
                                     mode: ExtractionMode = ExtractionMode.AUTO,
                                     use_cache: bool = True) -> Tuple[List[UnifiedElement], ExtractionMode]:
        """统一元素提取接口
        
        Returns:
            (elements, actual_mode): 元素列表和实际使用的模式
        """
        # 自动模式检测
        if mode == ExtractionMode.AUTO:
            mode = await self.detect_optimal_mode()
        
        # 检查统一缓存
        cache_key = f"unified_{mode.value}"
        current_time = time.time()
        
        if use_cache and cache_key in self._unified_cache:
            cached_data, timestamp = self._unified_cache[cache_key]
            if current_time - timestamp < self._cache_timeout:
                logger.info(f"使用缓存的{mode.value}元素")
                return cached_data, mode
        
        elements = []
        
        try:
            if mode == ExtractionMode.XML_ONLY:
                elements = await self.xml_extractor.extract_elements(use_cache)
                
            elif mode == ExtractionMode.VISUAL_ONLY:
                elements = await self.visual_extractor.extract_elements(use_cache)
                
            elif mode == ExtractionMode.HYBRID:
                # 混合模式：同时使用两种方法
                xml_elements = await self.xml_extractor.extract_elements(use_cache)
                visual_elements = await self.visual_extractor.extract_elements(use_cache)
                
                # 合并元素，视觉识别结果在前
                elements = visual_elements + xml_elements
            
            # 缓存结果
            if use_cache:
                self._unified_cache[cache_key] = (elements, current_time)
            
            self._last_extraction_mode = mode
            logger.info(f"使用 {mode.value} 模式提取到 {len(elements)} 个元素")
            
        except Exception as e:
            logger.error(f"元素提取失败: {e}")
            # 降级处理
            if mode != ExtractionMode.XML_ONLY:
                logger.info("降级到XML模式")
                elements = await self.xml_extractor.extract_elements(use_cache)
                mode = ExtractionMode.XML_ONLY
        
        return elements, mode
    
    async def find_elements_by_text(self, 
                                  text: str, 
                                  partial_match: bool = True,
                                  mode: ExtractionMode = ExtractionMode.AUTO) -> List[UnifiedElement]:
        """根据文本查找元素"""
        elements, actual_mode = await self.extract_elements_unified(mode)
        
        matches = []
        for element in elements:
            element_text = element.text.lower()
            search_text = text.lower()
            
            if partial_match:
                if search_text in element_text or search_text in element.name.lower():
                    matches.append(element)
            else:
                if element_text == search_text or element.name.lower() == search_text:
                    matches.append(element)
        
        logger.info(f"找到 {len(matches)} 个匹配 '{text}' 的元素")
        return matches
    
    async def find_elements_by_resource_id(self, 
                                         resource_id: str,
                                         mode: ExtractionMode = ExtractionMode.AUTO) -> List[UnifiedElement]:
        """根据resource_id查找元素"""
        elements, actual_mode = await self.extract_elements_unified(mode)
        
        matches = []
        for element in elements:
            if resource_id in element.resource_id:
                matches.append(element)
        
        logger.info(f"找到 {len(matches)} 个匹配resource_id '{resource_id}' 的元素")
        return matches
    
    async def find_clickable_elements(self, 
                                    mode: ExtractionMode = ExtractionMode.AUTO) -> List[UnifiedElement]:
        """查找所有可点击元素"""
        elements, actual_mode = await self.extract_elements_unified(mode)
        
        clickable_elements = [e for e in elements if e.clickable]
        logger.info(f"找到 {len(clickable_elements)} 个可点击元素")
        return clickable_elements
    
    async def find_elements_by_content_desc(self, 
                                          content_desc: str, 
                                          partial_match: bool = True,
                                          mode: ExtractionMode = ExtractionMode.AUTO) -> List[UnifiedElement]:
        """根据content description查找元素 - 集成ui_enhanced模块"""
        try:
            if mode == ExtractionMode.XML_ONLY or mode == ExtractionMode.AUTO:
                # 使用XML提取器的增强功能
                xml_results = await self.xml_extractor.find_elements_by_content_desc_enhanced(content_desc, partial_match)
                if xml_results:
                    logger.info(f"通过XML找到 {len(xml_results)} 个content_desc匹配元素")
                    return xml_results
            
            # 回退到标准方法
            elements, actual_mode = await self.extract_elements_unified(mode)
            matches = []
            for element in elements:
                content_desc_text = element.metadata.get('content_desc', '').lower()
                search_text = content_desc.lower()
                
                if partial_match:
                    if search_text in content_desc_text:
                        matches.append(element)
                else:
                    if content_desc_text == search_text:
                        matches.append(element)
            
            logger.info(f"找到 {len(matches)} 个匹配content_desc '{content_desc}' 的元素")
            return matches
            
        except Exception as e:
            logger.error(f"content_desc查找失败: {e}")
            return []
    
    async def find_elements_by_class_name(self, 
                                        class_name: str, 
                                        package_name: str = None,
                                        mode: ExtractionMode = ExtractionMode.AUTO) -> List[UnifiedElement]:
        """根据class name查找元素 - 集成ui_enhanced模块"""
        try:
            if mode == ExtractionMode.XML_ONLY or mode == ExtractionMode.AUTO:
                # 使用XML提取器的增强功能
                xml_results = await self.xml_extractor.find_elements_by_class_enhanced(class_name, package_name)
                if xml_results:
                    logger.info(f"通过XML找到 {len(xml_results)} 个class匹配元素")
                    return xml_results
            
            # 回退到标准方法
            elements, actual_mode = await self.extract_elements_unified(mode)
            matches = []
            for element in elements:
                element_class = element.class_name
                element_package = element.package
                
                if class_name in element_class and (
                    package_name is None or package_name in element_package
                ):
                    matches.append(element)
            
            logger.info(f"找到 {len(matches)} 个匹配class '{class_name}' 的元素")
            return matches
            
        except Exception as e:
            logger.error(f"class查找失败: {e}")
            return []
    
    async def tap_element(self, element: UnifiedElement, bias: bool = False) -> Dict[str, Any]:
        """点击元素"""
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = await self.xml_extractor.get_screen_size()
            
            # 获取实际屏幕坐标
            x, y = element.get_screen_coordinates(screen_width, screen_height, bias)
            
            # 执行点击
            success, output = await run_command(f"adb shell input tap {x} {y}")
            
            if success:
                logger.info(f"成功点击元素 {element.uuid} 在坐标 ({x}, {y})")
                return {
                    "status": "success",
                    "message": f"点击元素 {element.uuid} 成功",
                    "element": element.to_dict(),
                    "coordinates": {"x": x, "y": y},
                    "bias_applied": bias
                }
            else:
                logger.error(f"点击元素失败: {output}")
                return {
                    "status": "error",
                    "message": f"点击失败: {output}",
                    "element": element.to_dict()
                }
                
        except Exception as e:
            logger.error(f"点击元素异常: {e}")
            return {
                "status": "error",
                "message": f"点击异常: {str(e)}",
                "element": element.to_dict()
            }
    
    async def get_elements_json(self, 
                              mode: ExtractionMode = ExtractionMode.AUTO,
                              filter_package: str = None) -> Dict[str, Any]:
        """获取元素的JSON格式数据"""
        elements, actual_mode = await self.extract_elements_unified(mode)
        
        # 包过滤
        if filter_package:
            elements = [e for e in elements if filter_package in e.package]
        
        # 播放状态检测
        playback_state = await self.playback_detector.detect_playback_state()
        
        return {
            "total_count": len(elements),
            "extraction_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "extraction_mode": actual_mode.value,
            "playback_state": playback_state.value,
            "elements": [element.to_dict() for element in elements],
            "statistics": {
                "xml_elements": len([e for e in elements if e.element_type == "xml"]),
                "visual_elements": len([e for e in elements if e.element_type == "visual"]),
                "clickable_elements": len([e for e in elements if e.clickable]),
                "text_elements": len([e for e in elements if e.text.strip()])
            }
        }


# 智能调度器 - 统一对外接口
class UIAutomationScheduler:
    """UI自动化智能调度器
    
    对外提供统一接口，内部智能选择XML或视觉识别方法
    外部LLM感知不到具体使用哪种技术，保证输出一致性
    """
    
    def __init__(self, omniparser_url: str = "http://100.122.57.128:9333"):
        self.extractor = EnhancedUIExtractor(omniparser_url)
        self.default_mode = ExtractionMode.AUTO
    
    # ==================== 统一对外接口 - 对LLM透明 ====================
    
    async def get_screen_elements(self, filter_package: str = None) -> str:
        """获取屏幕元素 - 统一接口
        
        Returns:
            JSON string: 标准化的元素数据
        """
        try:
            data = await self.extractor.get_elements_json(self.default_mode, filter_package)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"获取屏幕元素失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"获取屏幕元素失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def find_elements_by_text(self, text: str, partial_match: bool = True) -> str:
        """根据文本查找元素 - 统一接口"""
        try:
            elements = await self.extractor.find_elements_by_text(text, partial_match, self.default_mode)
            
            return json.dumps({
                "status": "success",
                "query": text,
                "partial_match": partial_match,
                "count": len(elements),
                "elements": [element.to_dict() for element in elements]
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"文本查找失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"文本查找失败: {str(e)}",
                "query": text
            })
    
    async def find_clickable_elements(self) -> str:
        """查找可点击元素 - 统一接口"""
        try:
            elements = await self.extractor.find_clickable_elements(self.default_mode)
            
            return json.dumps({
                "status": "success",
                "count": len(elements),
                "elements": [element.to_dict() for element in elements]
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"查找可点击元素失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"查找可点击元素失败: {str(e)}"
            })
    
    async def find_elements_by_content_desc(self, content_desc: str, partial_match: bool = True) -> str:
        """根据内容描述查找元素 - 统一接口，集成ui_enhanced模块"""
        try:
            elements = await self.extractor.find_elements_by_content_desc(content_desc, partial_match, self.default_mode)
            
            return json.dumps({
                "status": "success",
                "query": content_desc,
                "partial_match": partial_match,
                "count": len(elements),
                "elements": [element.to_dict() for element in elements],
                "enhanced_by": "ui_enhanced_integration"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"内容描述查找失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"内容描述查找失败: {str(e)}",
                "query": content_desc
            })
    
    async def find_elements_by_class_name(self, class_name: str, package_name: str = None) -> str:
        """根据类名查找元素 - 统一接口，集成ui_enhanced模块"""
        try:
            elements = await self.extractor.find_elements_by_class_name(class_name, package_name, self.default_mode)
            
            return json.dumps({
                "status": "success",
                "query": class_name,
                "package_filter": package_name,
                "count": len(elements),
                "elements": [element.to_dict() for element in elements],
                "enhanced_by": "ui_enhanced_integration"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"类名查找失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"类名查找失败: {str(e)}",
                "query": class_name
            })
    
    async def tap_element_by_text(self, text: str, bias: bool = False) -> str:
        """根据文本点击元素 - 统一接口"""
        try:
            # 查找元素
            elements = await self.extractor.find_elements_by_text(text, True, self.default_mode)
            
            if not elements:
                return json.dumps({
                    "status": "error",
                    "message": f"未找到文本为 '{text}' 的元素",
                    "query": text
                })
            
            # 选择第一个可点击的元素
            target_element = None
            for element in elements:
                if element.clickable:
                    target_element = element
                    break
            
            if not target_element:
                # 如果没有可点击的，使用第一个
                target_element = elements[0]
                logger.warning("没有可点击元素，使用第一个元素")
            
            # 执行点击
            result = await self.extractor.tap_element(target_element, bias)
            result["query"] = text
            result["timestamp"] = datetime.now().isoformat()
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"文本点击失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"文本点击失败: {str(e)}",
                "query": text
            })
    
    async def tap_element_by_uuid(self, uuid: str, bias: bool = False) -> str:
        """根据UUID点击元素 - 统一接口"""
        try:
            # 获取所有元素
            elements, _ = await self.extractor.extract_elements_unified(self.default_mode)
            
            # 查找目标元素
            target_element = None
            for element in elements:
                if element.uuid == uuid:
                    target_element = element
                    break
            
            if not target_element:
                return json.dumps({
                    "status": "error",
                    "message": f"未找到UUID为 '{uuid}' 的元素",
                    "uuid": uuid
                })
            
            # 执行点击
            result = await self.extractor.tap_element(target_element, bias)
            result["uuid"] = uuid
            result["timestamp"] = datetime.now().isoformat()
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"UUID点击失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"UUID点击失败: {str(e)}",
                "uuid": uuid
            })
    
    # ==================== 手动模式选择接口 - 允许外部指定组件 ====================
    
    async def force_xml_mode(self) -> str:
        """强制使用XML模式"""
        self.default_mode = ExtractionMode.XML_ONLY
        logger.info("已切换到强制XML模式")
        return json.dumps({
            "status": "success",
            "message": "已切换到强制XML模式",
            "mode": "xml_only"
        })
    
    async def force_visual_mode(self) -> str:
        """强制使用视觉模式"""
        self.default_mode = ExtractionMode.VISUAL_ONLY
        logger.info("已切换到强制视觉模式")
        return json.dumps({
            "status": "success",
            "message": "已切换到强制视觉模式",
            "mode": "visual_only"
        })
    
    async def force_hybrid_mode(self) -> str:
        """强制使用混合模式"""
        self.default_mode = ExtractionMode.HYBRID
        logger.info("已切换到强制混合模式")
        return json.dumps({
            "status": "success",
            "message": "已切换到强制混合模式",
            "mode": "hybrid"
        })
    
    async def auto_mode(self) -> str:
        """恢复自动模式"""
        self.default_mode = ExtractionMode.AUTO
        logger.info("已恢复自动模式")
        return json.dumps({
            "status": "success",
            "message": "已恢复自动模式",
            "mode": "auto"
        })
    
    async def get_current_mode_info(self) -> str:
        """获取当前模式信息"""
        try:
            playback_state = await self.extractor.playback_detector.detect_playback_state()
            omniparser_available = await self.extractor.visual_extractor.screen_analyzer.client.health_check()
            
            # 获取屏幕尺寸
            screen_width, screen_height = await self.extractor.xml_extractor.get_screen_size()
            
            return json.dumps({
                "status": "success",
                "current_mode": self.default_mode.value,
                "playback_state": playback_state.value,
                "omniparser_available": omniparser_available,
                "screen_size": {"width": screen_width, "height": screen_height},
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"获取模式信息失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"获取模式信息失败: {str(e)}"
            })


# 全局调度器实例
_global_scheduler = None


def get_ui_scheduler(omniparser_url: str = "http://100.122.57.128:9333") -> UIAutomationScheduler:
    """获取全局UI调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = UIAutomationScheduler(omniparser_url)
    return _global_scheduler


# ==================== 使用示例 ====================

async def demo_enhanced_capabilities():
    """演示增强功能的使用示例"""
    print("Enhanced UI Extractor Demo - 增强功能演示")
    print("=" * 60)
    
    # 创建调度器
    scheduler = UIAutomationScheduler()
    
    try:
        # 1. 获取模式信息
        print("1. 获取当前模式信息...")
        mode_info = await scheduler.get_current_mode_info()
        print(f"模式信息: {mode_info}")
        
        # 2. 获取屏幕元素 (自动选择最佳模式)
        print("\n2. 获取屏幕元素 (智能模式选择)...")
        elements = await scheduler.get_screen_elements()
        elements_data = json.loads(elements)
        print(f"提取模式: {elements_data.get('extraction_mode')}")
        print(f"元素总数: {elements_data.get('total_count')}")
        print(f"播放状态: {elements_data.get('playback_state')}")
        
        # 3. 演示增强的查找功能
        print("\n3. 演示增强查找功能...")
        
        # 通过content description查找
        content_desc_result = await scheduler.find_elements_by_content_desc("播放")
        print(f"Content Desc查找结果: {len(json.loads(content_desc_result).get('elements', []))} 个元素")
        
        # 通过class name查找
        class_result = await scheduler.find_elements_by_class_name("Button")
        print(f"Class Name查找结果: {len(json.loads(class_result).get('elements', []))} 个元素")
        
        # 查找可点击元素
        clickable_result = await scheduler.find_clickable_elements()
        print(f"可点击元素: {len(json.loads(clickable_result).get('elements', []))} 个元素")
        
        # 4. 演示模式切换
        print("\n4. 演示模式切换...")
        
        # 强制切换到XML模式
        await scheduler.force_xml_mode()
        print("已切换到XML模式")
        
        # 强制切换到视觉模式
        await scheduler.force_visual_mode()
        print("已切换到视觉模式")
        
        # 恢复自动模式
        await scheduler.auto_mode()
        print("已恢复自动模式")
        
        print("\n✅ 演示完成！增强功能正常工作")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    """主函数 - 运行演示"""
    asyncio.run(demo_enhanced_capabilities())