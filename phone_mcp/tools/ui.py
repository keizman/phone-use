"""UI inspection functions for Phone MCP.
This module provides functions to inspect and interact with UI elements on the device.
"""

import asyncio
import json
import re
import os
import tempfile
import xml.etree.ElementTree as ET
import logging
from ..core import run_command, check_device_connection

logger = logging.getLogger("phone_mcp")


async def dump_ui():
    """Dump the current UI hierarchy from the device.

    Returns:
        str: JSON string with UI elements or error message
    """
    # Check for connected device
    connection_status = await check_device_connection()
    if "ready" not in connection_status:
        logger.error("设备未连接或未就绪")
        return connection_status

    # 创建临时文件路径
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, "ui_dump.xml")
    logger.debug(f"临时文件路径: {temp_file}")

    # 在设备上执行UI dump
    logger.debug("开始在设备上dump UI")
    cmd = "adb shell uiautomator dump"
    success, output = await run_command(cmd)
    logger.debug(f"UI dump命令执行结果: {success}, 输出: {output}")

    # 检查dump是否成功
    if not success:
        logger.error(f"UI dump失败: {output}")
        return json.dumps({
            "status": "error",
            "message": "Failed to dump UI hierarchy",
            "output": output
        }, indent=2)

    # 获取dump文件的路径
    device_file_path = ""
    match = re.search(r"UI hierchary dumped to: (.*\.xml)", output)
    if match:
        device_file_path = match.group(1)
        logger.debug(f"设备上dump文件路径: {device_file_path}")
    else:
        logger.error("无法找到dump文件路径")
        return json.dumps({
            "status": "error",
            "message": "Could not find dump file path",
            "output": output
        }, indent=2)

    # 从设备pull文件到本地
    logger.debug(f"开始pull文件: {device_file_path} -> {temp_file}")
    pull_cmd = f"adb pull {device_file_path} {temp_file}"
    pull_success, pull_output = await run_command(pull_cmd)
    logger.debug(f"Pull结果: {pull_success}, 输出: {pull_output}")

    if not pull_success:
        logger.error(f"Pull文件失败: {pull_output}")
        # 尝试直接从设备读取内容
        logger.debug("尝试直接从设备读取文件内容")
        cat_cmd = f"adb shell cat {device_file_path}"
        cat_success, xml_content = await run_command(cat_cmd)
        
        if not cat_success or not xml_content or "<hierarchy" not in xml_content:
            logger.error("无法读取UI信息")
            return json.dumps({
                "status": "error",
                "message": "Could not read UI dump file",
                "output": pull_output
            }, indent=2)
    else:
        # 从本地文件读取内容
        try:
            logger.debug(f"开始读取本地文件: {temp_file}")
            with open(temp_file, "r", encoding="utf-8") as f:
                xml_content = f.read()
            logger.debug(f"文件读取成功，内容长度: {len(xml_content)}")
        except Exception as e:
            logger.exception(f"读取本地文件失败: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to read local XML file: {str(e)}",
            }, indent=2)

    # 检查XML内容是否有效
    if not xml_content or "<hierarchy" not in xml_content:
        logger.error("XML内容无效")
        return json.dumps({
            "status": "error",
            "message": "Invalid XML content",
            "xml_preview": xml_content[:100] if xml_content else "Empty content"
        }, indent=2)

    # 处理XML并转换为JSON
    try:
        logger.debug("开始处理XML")
        json_result = process_ui_xml(xml_content)
        logger.debug("XML处理成功")
        
        # 清理临时文件
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"已删除临时文件: {temp_file}")
        except Exception as cleanup_error:
            logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
            
        return json_result
    except Exception as e:
        logger.exception(f"处理XML失败: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to process UI XML: {str(e)}",
            "raw_xml_sample": xml_content[:500] if xml_content else "No XML content"
        }, indent=2)


def process_ui_xml(xml_content):
    """Process UI XML content and convert to simplified JSON.

    Args:
        xml_content (str): XML string from UI Automator

    Returns:
        str: JSON string with simplified UI elements
    """
    # Parse the XML
    root = ET.fromstring(xml_content)

    # Extract elements into a simplified structure
    elements = []

    for node in root.findall(".//node"):
        element = {}

        # Extract key attributes
        for attr in [
            "resource-id",
            "class",
            "package",
            "text",
            "content-desc",
            "clickable",
            "checkable",
            "checked",
            "enabled",
            "password",
            "selected",
        ]:
            if attr in node.attrib:
                # Convert boolean attributes
                if attr in [
                    "clickable",
                    "checkable",
                    "checked",
                    "enabled",
                    "password",
                    "selected",
                ]:
                    element[attr.replace("-", "_")] = node.attrib[attr] == "true"
                else:
                    element[attr.replace("-", "_")] = node.attrib[attr]

        # Extract bounds as string for compatibility with existing code
        if "bounds" in node.attrib:
            element["bounds"] = node.attrib["bounds"]
            
            # Also extract parsed bounds
            bounds_str = node.attrib["bounds"]
            bounds_match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
            if bounds_match:
                x1, y1, x2, y2 = map(int, bounds_match.groups())
                element["bounds_parsed"] = {
                    "left": x1,
                    "top": y1,
                    "right": x2,
                    "bottom": y2
                }
                element["center_x"] = (x1 + x2) // 2
                element["center_y"] = (y1 + y2) // 2

        # Add element if it has useful info
        if element:
            elements.append(element)

    if not elements:
        logger.warning("未找到任何UI元素")
        
    return json.dumps(
        {"status": "success", "count": len(elements), "elements": elements}, indent=2
    )


async def find_element_by_text(text, partial_match=False):
    """Find UI element by text content.

    Args:
        text (str): Text to search for
        partial_match (bool): If True, find elements containing the text. If False,
                             only exact matches are returned.

    Returns:
        str: JSON string with matching elements or error message
    """
    # Get the full UI dump first
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response  # Return error from dump_ui

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_text = element.get("text", "")

            if (partial_match and text in element_text) or element_text == text:
                matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": text,
                "partial_match": partial_match,
                "count": len(matches),
                "elements": matches,
            },
            indent=2,
        )
    except json.JSONDecodeError:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to process UI data",
                "raw_response": dump_response[
                    :500
                ],  # Include part of the raw response for debugging
            },
            indent=2,
        )


async def find_element_by_id(resource_id, package_name=None):
    """Find UI element by resource ID.

    Args:
        resource_id (str): Resource ID to search for
        package_name (str, optional): Package name to limit search to

    Returns:
        str: JSON string with matching elements or error message
    """
    # Get the full UI dump first
    dump_response = await dump_ui()

    try:
        dump_data = json.loads(dump_response)

        if dump_data.get("status") != "success":
            return dump_response  # Return error from dump_ui

        # Find matching elements
        matches = []
        for element in dump_data.get("elements", []):
            element_id = element.get("resource_id", "")
            element_package = element.get("package", "")

            # Check if ID matches and (no package filter or package matches)
            if resource_id in element_id and (
                package_name is None or package_name in element_package
            ):
                matches.append(element)

        return json.dumps(
            {
                "status": "success",
                "query": resource_id,
                "package_filter": package_name,
                "count": len(matches),
                "elements": matches,
            },
            indent=2,
        )
    except json.JSONDecodeError:
        return json.dumps(
            {
                "status": "error",
                "message": "Failed to process UI data",
                "raw_response": dump_response[
                    :500
                ],  # Include part of the raw response for debugging
            },
            indent=2,
        )


async def tap_element(element_json):
    """Tap on a UI element by using its center coordinates.

    Args:
        element_json (str): JSON representation of the element with bounds

    Returns:
        str: Success or error message
    """
    try:
        element = json.loads(element_json)
        
        # Try to get center coordinates directly
        center_x = element.get("center_x")
        center_y = element.get("center_y")
        
        if not center_x or not center_y:
            # Check for parsed bounds
            bounds_parsed = element.get("bounds_parsed")
            if bounds_parsed:
                center_x = (bounds_parsed.get("left", 0) + bounds_parsed.get("right", 0)) // 2
                center_y = (bounds_parsed.get("top", 0) + bounds_parsed.get("bottom", 0)) // 2
            else:
                # Try to parse from bounds string
                bounds = element.get("bounds", "")
                if bounds and isinstance(bounds, str):
                    bounds_match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
                    if bounds_match:
                        x1, y1, x2, y2 = map(int, bounds_match.groups())
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2

        if not center_x or not center_y:
            return json.dumps({
                "status": "error",
                "message": "Could not determine element coordinates"
            })

        # Now use our existing tap function
        from .interactions import tap_screen
        return await tap_screen(center_x, center_y)

    except json.JSONDecodeError:
        return json.dumps({
            "status": "error",
            "message": "Invalid element JSON format"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error tapping element: {str(e)}"
        })
