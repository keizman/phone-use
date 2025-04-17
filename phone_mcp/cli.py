#!/usr/bin/env python3
"""
Command-line interface for Phone MCP.
This script provides a direct command line interface to phone control functions.
"""

import argparse
import asyncio
import sys
import json
import logging
import time
from typing import Dict, Any, Optional
from .core import check_device_connection
from .tools.call import call_number, end_call, receive_incoming_call
from .tools.messaging import send_text_message, receive_text_messages, get_raw_messages
from .tools.media import take_screenshot, start_screen_recording, play_media
from .tools.apps import open_app, set_alarm, list_installed_apps, terminate_app
from .tools.contacts import get_contacts
from .tools.system import get_current_window, get_app_shortcuts, launch_activity
from .tools.interactions import (
    tap_screen,
    swipe_screen,
    press_key,
    input_text,
    open_url,
    get_screen_size,
)
from .tools.ui import dump_ui, find_element_by_text, find_element_by_id, tap_element
from .tools.ui_enhanced import (
    find_element_by_content_desc,
    find_element_by_class,
    find_clickable_elements,
    wait_for_element,
    scroll_to_element,
)
from .tools.ui_monitor import monitor_ui_changes, mcp_monitor_ui_changes
from .tools.screen_interface import analyze_screen, interact_with_screen

# Import map-related functionality, including environment variable check
try:
    from .tools.maps import get_phone_numbers_from_poi, HAS_VALID_API_KEY
except ImportError:
    HAS_VALID_API_KEY = False


# Set up CLI logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("phone_cli")


# Helper function to format JSON output
def format_json_output(json_str: str, pretty: bool = True) -> str:
    """Format JSON output to make it more readable"""
    try:
        data = json.loads(json_str)
        if pretty:
            # Check if it's simple data
            if isinstance(data, dict) and "status" in data:
                if data["status"] == "success" or data["status"] == "1":
                    return f"✅ {data.get('message', 'Operation successful')}"
                else:
                    return f"❌ {data.get('message', 'Operation failed')}"
            # Return prettified JSON
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json_str
    except:
        # If not JSON, return original string
        return json_str


async def call(args):
    """Make a phone call."""
    result = await call_number(args.number)
    print(format_json_output(result))


async def hangup(args):
    """End the current call."""
    result = await end_call()
    print(format_json_output(result))


async def check_device(args):
    """Check device connection."""
    result = await check_device_connection()
    print(format_json_output(result))


async def verify_sms_sent(number: str, text: str) -> bool:
    """Verify if an SMS was actually sent by checking the sent messages using ADB.
    
    Args:
        number: The phone number the SMS was sent to
        text: The content of the SMS
        
    Returns:
        bool: True if the SMS was found in sent messages, False otherwise
    """
    from .core import run_command
    
    try:
        # Clean number (remove spaces, dashes, etc.)
        clean_number = "".join(c for c in number if c.isdigit())
        
        # Use a filtered query to check specifically for our message
        # This is much faster than querying all SMS and filtering in Python
        
        # First try to find by address (phone number)
        adb_command = f'adb shell content query --uri content://sms/sent --where "address LIKE \'%{clean_number}%\'" --limit 5'
        success, output = await run_command(adb_command)
        
        if not success:
            logger.error(f"Failed to query SMS database: {output}")
            return False
            
        # If we found recent messages to this number, check if our text is in there
        # Simplify text for comparison (remove extra spaces, line breaks, etc.)
        simplified_text = " ".join(text.split())
        
        # Check if any of these messages contain our text
        for line in output.split("\n"):
            if "body=" in line:
                # Extract the body value
                body_start = line.find("body=")
                if body_start >= 0:
                    # Extract everything after body= until the next parameter or end of line
                    body_part = line[body_start:]
                    body_end = body_part.find(", ", 5)  # Skip past "body="
                    if body_end > 0:
                        body = body_part[5:body_end]
                    else:
                        body = body_part[5:]
                    
                    # Remove quotes if present
                    if body.startswith('"') and body.endswith('"'):
                        body = body[1:-1]
                    # Simplify body
                    body = " ".join(body.split())
                    
                    # If the message body contains our text, consider it a match
                    if simplified_text in body:
                        return True
        
        # If we don't find it by number + content, try a more general search with date filtering
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        one_minute_ago = current_time - (60 * 1000)  # 1 minute ago
        
        # Query for all messages sent in the last minute
        time_query = f'adb shell content query --uri content://sms/sent --where "date > {one_minute_ago}" --limit 10'
        success, recent_output = await run_command(time_query)
        
        if success:
            # Check these recent messages
            for line in recent_output.split("\n"):
                if "body=" in line:
                    body_start = line.find("body=")
                    if body_start >= 0:
                        body_part = line[body_start:]
                        body_end = body_part.find(", ", 5)
                        if body_end > 0:
                            body = body_part[5:body_end]
                        else:
                            body = body_part[5:]
                        
                        # Remove quotes if present
                        if body.startswith('"') and body.endswith('"'):
                            body = body[1:-1]
                        body = " ".join(body.split())
                        
                        # Look for content match in recent messages
                        if simplified_text in body:
                            return True
        
        # If we get here, no matching SMS was found
        return False
        
    except Exception as e:
        logger.error(f"Error verifying SMS: {str(e)}")
        return False


async def send_sms(args):
    """Send a text message using both messaging API and screen interaction.
    
    This enhanced version:
    1. Uses the messaging API to input the number and text
    2. Verifies if SMS was actually sent using ADB
    3. If not sent, tries screen interaction method
    4. Verifies again after enhanced interaction
    """
    from .core import run_command
    
    # Set a timeout for the entire operation
    enhanced_timeout = 20.0  # 20 seconds timeout
    start_time = time.time()
    
    # First attempt to use the traditional messaging API
    result = await send_text_message(args.number, args.text)
    
    if args.debug:
        debug_json_response(result, "SMS API result:")
    
    # Safely parse the result - handle case where it's not valid JSON
    result_data = {}
    try:
        if result and isinstance(result, str):
            result_data = json.loads(result)
    except json.JSONDecodeError:
        # If parsing fails, treat as if operation needs enhanced mode
        logger.debug(f"Failed to parse result as JSON: {result}")
        result_data = {"status": "error", "message": "Invalid response from send_text_message"}
    
    # If API reports success, verify with ADB if the message was actually sent
    api_success = result_data.get("status") == "success"
    
    # Immediately verify if the SMS was sent
    if api_success or args.auto_enhance:
        logger.info("Verifying SMS delivery with ADB...")
        
        # Verify if SMS was actually sent
        sms_sent = await verify_sms_sent(args.number, args.text)
        
        if sms_sent:
            logger.info("SMS verified as sent")
            print(f"✅ Message sent to {args.number} (verified)")
            return
        elif api_success:
            logger.warning("API reported success but SMS not found in sent messages")
            
            # Give it a moment in case the SMS is still being processed
            logger.info("Waiting briefly for message to be processed...")
            await asyncio.sleep(1.0)
            
            # Check again
            sms_sent = await verify_sms_sent(args.number, args.text)
            if sms_sent:
                logger.info("SMS verified as sent after waiting")
                print(f"✅ Message sent to {args.number} (verified)")
                return
            
            print("⚠️ API reported success but message not found in sent messages")
            
            # Only proceed to enhanced mode if requested
            if not args.enhanced and not args.auto_enhance:
                print("Use --enhanced or --auto-enhance to retry with UI interaction")
                return
    elif not args.enhanced and not args.auto_enhance:
        # If API failed and enhanced mode not requested
        print(format_json_output(result))
        print("Use --enhanced or --auto-enhance to retry with UI interaction")
        return
    
    # At this point, we're in enhanced mode
    try:
        # Use screen analysis to find interactive elements
        logger.info("Using enhanced mode with screen interaction to send SMS")
        print("Using enhanced mode with screen interaction...")
        
        # Set a flag to track if we successfully tapped a send button
        send_button_tapped = False
        
        # Wait briefly for the messaging app to load
        await asyncio.sleep(1.0)
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > enhanced_timeout:
            logger.warning("Enhanced mode timeout while waiting for message app to load")
            print("⚠️ Enhanced operation timed out - basic SMS function may have worked")
            return
        
        # Analyze the screen to find buttons
        analysis_result = await analyze_screen()
        
        if args.debug:
            debug_json_response(analysis_result, "Screen analysis:")
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > enhanced_timeout:
            logger.warning("Enhanced mode timeout after screen analysis")
            print("⚠️ Enhanced operation timed out - basic SMS function may have worked")
            return
        
        analysis_data = {}
        try:
            if analysis_result and isinstance(analysis_result, str):
                analysis_data = json.loads(analysis_result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse screen analysis result: {analysis_result}")
            print("❌ Failed to analyze screen for buttons")
            return
        
        # Look for the send button (typically appears in the bottom section with text like "Send", "发送", etc.)
        send_button = None
        send_keywords = ["send", "发送", "发信息", "确定", "ok"]
        
        if analysis_data.get("status") == "success":
            # First check notable clickables
            if args.debug:
                logger.debug(f"Searching for send button in notable clickables...")
                
            notable_clickables = analysis_data.get("screen_analysis", {}).get("notable_clickables", [])
            if args.debug:
                logger.debug(f"Found {len(notable_clickables)} notable clickable elements")
                
            for clickable in notable_clickables:
                if clickable.get("text") and any(keyword in clickable.get("text", "").lower() for keyword in send_keywords):
                    send_button = clickable
                    if args.debug:
                        logger.debug(f"Found send button in notable clickables: {clickable.get('text')}")
                    break
                    
            # If not found in notable clickables, check by region
            if not send_button:
                if args.debug:
                    logger.debug("Send button not found in notable clickables, checking bottom region...")
                    
                # Send button is typically at the bottom
                bottom_elements = analysis_data.get("screen_analysis", {}).get("text_elements", {}).get("by_region", {}).get("bottom", [])
                if args.debug:
                    logger.debug(f"Found {len(bottom_elements)} elements in bottom region")
                    
                for elem in bottom_elements:
                    if any(keyword in elem.get("text", "").lower() for keyword in send_keywords):
                        send_button = elem
                        if args.debug:
                            logger.debug(f"Found send button in bottom region: {elem.get('text')}")
                        break
                        
            # Check if we've exceeded the timeout
            if time.time() - start_time > enhanced_timeout:
                logger.warning("Enhanced mode timeout while searching for send button")
                print("⚠️ Enhanced operation timed out - basic SMS function may have worked")
                return
        
        # If we found a send button, tap it
        if send_button and "center_x" in send_button and "center_y" in send_button:
            logger.info(f"Found send button: {send_button.get('text')} at coordinates ({send_button['center_x']}, {send_button['center_y']})")
            
            # Tap the send button
            try:
                # Use a timeout for the tap operation
                tap_future = tap_screen(send_button["center_x"], send_button["center_y"])
                tap_result = await asyncio.wait_for(tap_future, timeout=3.0)
                send_button_tapped = True
            except asyncio.TimeoutError:
                logger.error("Tap operation timed out")
                print("⚠️ Message input complete, but send button tap timed out")
                return
            
            if args.debug:
                logger.debug(f"Tap result: {tap_result}")
                
            # Handle both JSON and string responses
            tap_success = False
            try:
                if isinstance(tap_result, str) and tap_result.startswith("{"):
                    tap_data = json.loads(tap_result)
                    tap_success = tap_data.get("status") == "success"
                else:
                    # If not JSON, check for success message in the string
                    tap_success = "success" in tap_result.lower() or "tapped" in tap_result.lower()
            except:
                # If parsing fails, check for success keywords in the string
                tap_success = isinstance(tap_result, str) and ("success" in tap_result.lower() or "tapped" in tap_result.lower())
            
            if tap_success:
                print(f"✅ Send button tapped, verifying message delivery...")
            else:
                print(f"⚠️ Message input complete, but couldn't tap send button: {tap_result}")
                return
        else:
            if args.debug:
                logger.debug("No send button found, trying fallback to bottom-right corner")
                
            # If no send button found, try to tap near the bottom right (common location for send)
            screen_size = analysis_data.get("screen_size", {})
            if screen_size.get("width") and screen_size.get("height"):
                # Calculate position (typically bottom right corner)
                x = int(screen_size["width"] * 0.85)  # 85% to the right
                y = int(screen_size["height"] * 0.9)  # 90% down from top
                
                logger.info(f"No send button found, trying to tap at position ({x}, {y})")
                
                try:
                    # Use a timeout for the tap operation
                    tap_future = tap_screen(x, y)
                    tap_result = await asyncio.wait_for(tap_future, timeout=3.0)
                    send_button_tapped = True
                except asyncio.TimeoutError:
                    logger.error("Fallback tap operation timed out")
                    print("⚠️ Message input complete, but fallback tap timed out")
                    return
                
                if args.debug:
                    logger.debug(f"Fallback tap result: {tap_result}")
                    
                # Handle both JSON and string responses
                tap_success = False
                try:
                    if isinstance(tap_result, str) and tap_result.startswith("{"):
                        tap_data = json.loads(tap_result)
                        tap_success = tap_data.get("status") == "success"
                    else:
                        # If not JSON, check for success message in the string
                        tap_success = "success" in tap_result.lower() or "tapped" in tap_result.lower()
                except:
                    # If parsing fails, check for success keywords in the string
                    tap_success = isinstance(tap_result, str) and ("success" in tap_result.lower() or "tapped" in tap_result.lower())
                
                if tap_success:
                    print(f"✅ Send button location tapped, verifying message delivery...")
                else:
                    print(f"⚠️ Message input complete, but couldn't tap estimated send button: {tap_result}")
                    return
            else:
                print(f"⚠️ Message input complete, but couldn't find send button")
                return
        
        # Check if a send button was successfully tapped
        if not send_button_tapped:
            logger.warning("No send button was tapped")
            print("⚠️ SMS sending process incomplete - no send button was tapped")
            return
            
        # --------- FINAL VERIFICATION AFTER ENHANCED MODE ----------
        # Wait for the SMS to be registered in the system
        logger.info("Waiting for message to be registered...")
        
        # Verify immediately after tapping
        sms_sent = await verify_sms_sent(args.number, args.text)
        if sms_sent:
            logger.info("SMS successfully sent and verified with ADB")
            print(f"✅ Message successfully sent to {args.number} (verified)")
            return
            
        # Wait a bit longer for SMS to be processed - check every 0.5 seconds for up to 3 seconds
        max_wait_time = 3.0  # Maximum wait time in seconds
        interval = 0.5  # Check interval in seconds
        waited_time = 0.0
        
        while waited_time < max_wait_time:
            # Check if we've exceeded the timeout
            if time.time() - start_time > enhanced_timeout:
                logger.warning("Enhanced mode timeout during final verification")
                print("⚠️ Send button tapped, but verification timed out")
                return
                
            # Wait a bit
            await asyncio.sleep(interval)
            waited_time += interval
            
            # Verify if SMS was sent using ADB
            sms_sent = await verify_sms_sent(args.number, args.text)
            
            if sms_sent:
                logger.info(f"SMS successfully sent and verified with ADB after waiting {waited_time:.1f}s")
                print(f"✅ Message successfully sent to {args.number} (verified)")
                return
                
        # If we get here, SMS wasn't found in sent messages
        logger.warning("SMS not found in sent messages after enhanced mode")
        print(f"⚠️ Send button tapped, but message not found in sent messages. It may still be processing.")
        
    except Exception as e:
        logger.error(f"Error in enhanced SMS sending: {str(e)}")
        print(f"⚠️ Error during SMS operation: {str(e)}")
    finally:
        # Always log when the enhanced operation completes
        logger.info(f"SMS operation completed in {time.time() - start_time:.2f} seconds")

    # Explicitly return to ensure function exits
    return


async def check_messages(args):
    """Check recent text messages."""
    result = await get_raw_messages(limit=args.limit)
    print(format_json_output(result))


async def screenshot(args):
    """Take a screenshot."""
    result = await take_screenshot()
    print(format_json_output(result))


async def record(args):
    """Record screen."""
    result = await start_screen_recording(args.duration)
    print(format_json_output(result))


async def media_control(args):
    """Control media playback."""
    result = await play_media()
    print(format_json_output(result))


async def launch_app(args):
    """Launch an app."""
    result = await open_app(args.name)
    print(format_json_output(result))


async def close_app(args):
    """Force stop an app."""
    result = await terminate_app(args.package)
    print(format_json_output(result))


async def alarm(args):
    """Set an alarm."""
    result = await set_alarm(args.hour, args.minute, args.label)
    print(format_json_output(result))


async def receive_call(args):
    """Check for incoming calls."""
    result = await receive_incoming_call()
    print(format_json_output(result))


async def check_contacts(args):
    """Retrieve contacts from the phone."""
    result = await get_contacts(limit=args.limit)
    
    try:
        # 尝试解析为JSON
        try:
            contacts = json.loads(result)
            # 如果返回的是错误消息字符串，JSON解析会失败，会进入except部分
            if not isinstance(contacts, list):
                # 如果返回的不是列表，当作错误处理
                print(format_json_output(result))
                return
        except json.JSONDecodeError:
            # 如果不是JSON，认为是原始ADB输出格式或错误信息，直接处理
            if "Row:" in result:
                rows = result.strip().split("Row:")
                contacts = []
                for row in rows:
                    if not row.strip():
                        continue
                    
                    # 将每一行转换为字典
                    contact = {}
                    parts = row.split(", ")
                    for part in parts:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            # 只添加非NULL值
                            if value and value != "NULL" and value != "null":
                                contact[key.strip()] = value.strip()
                    
                    if contact:
                        contacts.append(contact)
            else:
                # 如果不是Row格式，可能是错误消息
                print(result)
                return
        
        # 处理联系人数据
        valid_contacts = []
        for contact in contacts:
            # 提取名称
            name = contact.get("name", contact.get("display_name", "Unknown"))
            
            # 收集所有可能是电话号码的字段
            phone_values = []
            for key, value in contact.items():
                # 跳过明显不是电话号码的字段
                if key in ["name", "display_name", "id", "_id", "rowid", "starred", "times_contacted", "send_to_voicemail"]:
                    continue
                
                # 如果字段名称暗示这是电话号码，或者值包含数字
                if "number" in key.lower() or "phone" in key.lower() or (isinstance(value, str) and any(c.isdigit() for c in value)):
                    # 确保值是字符串
                    if isinstance(value, str):
                        # 标准化电话号码格式
                        normalized = ''.join(c for c in value if c.isdigit() or c == '+')
                        # 验证电话号码格式
                        if normalized and _is_valid_phone_number(normalized) and normalized not in phone_values:
                            phone_values.append(normalized)
                    elif isinstance(value, list):
                        # 如果值是列表，只添加其中的字符串项
                        for item in value:
                            if isinstance(item, str):
                                normalized = ''.join(c for c in item if c.isdigit() or c == '+')
                                if normalized and _is_valid_phone_number(normalized) and normalized not in phone_values:
                                    phone_values.append(normalized)
                    else:
                        # 其他类型转为字符串
                        try:
                            normalized = ''.join(c for c in str(value) if c.isdigit() or c == '+')
                            if normalized and _is_valid_phone_number(normalized) and normalized not in phone_values:
                                phone_values.append(normalized)
                        except:
                            pass
            
            # 如果有电话号码，添加到有效联系人列表
            if phone_values:
                valid_contacts.append({
                    "name": name,
                    "phone_values": phone_values,
                    "original": contact  # 保存原始过滤后的数据，以防需要更多字段
                })
        
        total_count = len(valid_contacts)
        
        # 检查是否有联系人
        if total_count == 0:
            print("未找到联系人数据")
            return
        
        # 打印联系人信息
        print(f"找到 {total_count} 个联系人:")
        
        # 检查是否请求JSON输出
        if hasattr(args, 'json') and args.json:
            # 显示JSON格式
            print(json.dumps(valid_contacts, indent=2, ensure_ascii=False))
        else:
            # 每行输出一个联系人
            for contact in valid_contacts[:args.limit]:
                name = contact["name"]
                
                # 确保所有电话号码都是字符串类型
                phone_values = []
                for value in contact["phone_values"]:
                    if isinstance(value, str):
                        phone_values.append(value)
                    else:
                        try:
                            phone_values.append(str(value))
                        except:
                            continue
                
                if phone_values:
                    phone_display = ", ".join(phone_values)
                    # 每个联系人输出一行
                    print(f"{name}: {phone_display}")
                else:
                    # 如果没有有效的电话号码，尝试使用原始数据中的任何可能是电话号码的字段
                    original = contact.get("original", {})
                    for key, value in original.items():
                        if "number" in key.lower() or "phone" in key.lower():
                            if isinstance(value, str):
                                print(f"{name}: {value}")
                                break
    except Exception as e:
        # 解析失败时，回退到原始输出
        logger.error(f"解析联系人时出错: {str(e)}")
        print(format_json_output(result))


async def check_window(args):
    """Get current window information."""
    result = await get_current_window()
    print(format_json_output(result))


async def check_shortcuts(args):
    """Get app shortcuts."""
    result = await get_app_shortcuts(package_name=args.package)
    print(format_json_output(result))


async def launch(args):
    """Launch a specific activity with custom action and component."""
    result = await launch_activity(package_component=args.component, action=args.action, extra_args=args.extras)
    print(format_json_output(result))


async def receive_sms(args):
    """Check recent text messages (alias for 'messages')."""
    limit = args.limit if hasattr(args, 'limit') else 5
    result = await get_raw_messages(limit=limit)
    print(format_json_output(result))


async def get_phone_by_poi(args):
    """Search for phone numbers from POIs (Points of Interest) around a specified location."""
    try:
        # Check if API key is configured properly
        if not HAS_VALID_API_KEY:
            print("❌ API key for map services is not properly configured")
            print("Please configure a valid API key in your environment variables")
            print("See the documentation for more details on setting up map services")
            print("Windows: set AMAP_MAPS_API_KEY=your_api_key")
            print("Linux/Mac: export AMAP_MAPS_API_KEY=your_api_key")
            return
            
        logger.info(f"Searching for phone numbers near {args.location} with keywords: {args.keywords} (radius: {args.radius}m)")
        
        # Validate location format (should be longitude,latitude)
        location = args.location
        try:
            if "," in location:
                longitude, latitude = location.split(",")
                float(longitude.strip())
                float(latitude.strip())
            else:
                print("❌ Invalid location format. Please use 'longitude,latitude' format")
                print("Example: 116.480053,39.987005")
                return
        except ValueError:
            print("❌ Invalid coordinates. Please provide valid numeric longitude and latitude")
            print("Example: 116.480053,39.987005")
            return
            
        # Call the POI search function
        result = await get_phone_numbers_from_poi(args.location, args.keywords, args.radius)
        
        # Debug output if requested
        if args.debug:
            debug_json_response(result, "POI search result:")
            
        # Parse the result
        try:
            data = json.loads(result)
            
            # Check if the request was successful
            if data.get("status") == "1" and "pois" in data:
                pois_list = data["pois"]
                
                if len(pois_list) == 0:
                    print(f"No POIs found matching '{args.keywords}' within {args.radius}m of {args.location}")
                else:
                    # Display the POIs in a more readable format
                    print(f"Found {len(pois_list)} POIs near {args.location}:")
                    
                    # Display in compact format
                    for i, poi in enumerate(pois_list, 1):
                        name = poi.get("name", "Unknown")
                        address = poi.get("address", "No address")
                        phone = poi.get("tel", "No phone")
                        distance = poi.get("distance", "Unknown")
                        
                        print(f"{i}. {name}")
                        print(f"   Address: {address}")
                        print(f"   Phone: {phone}")
                        print(f"   Distance: {distance}m")
                        print()
            else:
                # For non-standard responses, use default formatting
                print(format_json_output(result))
                # Print more detailed error information
                if "error" in data:
                    error_info = data.get("error", {})
                    if isinstance(error_info, dict):
                        error_code = error_info.get("code", "unknown")
                        error_message = error_info.get("message", "Unknown error")
                        print(f"Error code: {error_code}")
                        print(f"Error message: {error_message}")
                    else:
                        print(f"Error details: {error_info}")
                
        except json.JSONDecodeError:
            # If parsing fails, output the raw result
            print(f"Failed to parse result as JSON: {result}")
            
    except Exception as e:
        logger.error(f"Error getting POI information: {str(e)}")
        print(f"❌ Failed to get POI information: {str(e)}")
        # If it's an API key issue, provide a hint
        if "api key" in str(e).lower() or "apikey" in str(e).lower():
            print("This appears to be an API key issue. Please check your map services configuration.")
        # If it's a connection issue, provide another hint
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            print("This appears to be a network connection issue. Please check your internet connection.")


async def list_apps(args):
    """List installed applications."""
    if args.system:
        only_system = True
        only_third_party = False
    elif args.third_party:
        only_system = False
        only_third_party = True
    else:
        only_system = False
        only_third_party = False
        
    try:
        # Log parameters for debugging
        if args.verbose:
            logger.debug(f"Listing apps with filter: {args.filter}, system: {only_system}, third_party: {only_third_party}")
        
        print("Fetching application list...")
            
        result = await list_installed_apps(
            filter_keyword=args.filter, 
            only_system=only_system,
            only_third_party=only_third_party,
            limit=args.limit
        )
        
        # First check if result is valid
        if not result:
            print("❌ No response from device when listing applications")
            return
            
        if args.verbose:
            logger.debug(f"Raw result length: {len(result) if result else 0}")
            logger.debug(f"Raw result type: {type(result)}")
            logger.debug(f"Raw result preview: {result[:100] if isinstance(result, str) and len(result) > 100 else result}")
            
        # Check if the result is already a string
        if isinstance(result, str):
            # Try to parse the result
            try:
                data = json.loads(result)
                
                # Always display the apps list, not just a success message
                if isinstance(data, dict) and data.get("status") == "success" and "apps" in data:
                    apps_list = data["apps"]
                    
                    if len(apps_list) == 0:
                        print("No applications found matching the criteria. Try without filters or check device connection.")
                        return
                        
                    # Display the apps in a more readable format
                    print(f"Found {len(apps_list)} applications:")
                    
                    # Default is now compact one-line format, 
                    # JSON format only if --json flag is used
                    if hasattr(args, 'json') and args.json:
                        # Display full JSON with proper formatting
                        print(json.dumps(apps_list, indent=2, ensure_ascii=False))
                    else:
                        # Display apps in one line per app format (default)
                        for i, app in enumerate(apps_list, 1):
                            if not isinstance(app, dict):
                                # Skip non-dictionary entries
                                continue
                                
                            app_name = app.get("app_name", "Unknown")
                            package_name = app.get("package_name", "")
                            app_type = "System" if app.get("is_system", False) else "User"
                            
                            # Add version info if available
                            version_info = f" v{app.get('version_name', '')}" if app.get('version_name') else ""
                            
                            print(f"{i}. {app_name}{version_info} ({package_name}) - {app_type}")
                            # Flush after each print to ensure output is visible immediately
                            sys.stdout.flush()
                                
                elif isinstance(data, list):
                    # Handle case where result is directly a list of apps
                    apps_list = data
                    
                    if len(apps_list) == 0:
                        print("No applications found matching the criteria. Try without filters or check device connection.")
                        return
                        
                    # Display the apps in a more readable format
                    print(f"Found {len(apps_list)} applications:")
                    
                    # Default is now compact one-line format, 
                    # JSON format only if --json flag is used
                    if hasattr(args, 'json') and args.json:
                        # Display full JSON with proper formatting
                        print(json.dumps(apps_list, indent=2, ensure_ascii=False))
                    else:
                        # Display apps in one line per app format (default)
                        for i, app in enumerate(apps_list, 1):
                            if not isinstance(app, dict):
                                # Skip non-dictionary entries
                                continue
                                
                            app_name = app.get("app_name", "Unknown")
                            package_name = app.get("package_name", "")
                            app_type = "System" if app.get("is_system", False) else "User"
                            
                            # Add version info if available
                            version_info = f" v{app.get('version_name', '')}" if app.get('version_name') else ""
                            
                            print(f"{i}. {app_name}{version_info} ({package_name}) - {app_type}")
                            # Flush after each print to ensure output is visible immediately
                            sys.stdout.flush()
                else:
                    # For non-standard responses, use default formatting
                    print(format_json_output(result))
                    if args.verbose:
                        logger.debug(f"Non-standard response structure. Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
                
            except json.JSONDecodeError as e:
                # If parsing fails, output the raw result
                print(f"Failed to parse apps list: {result}")
                if args.verbose:
                    logger.debug(f"JSON parse error: {str(e)}")
        elif isinstance(result, list):
            # Handle case where result is directly a list of apps
            apps_list = result
            
            if len(apps_list) == 0:
                print("No applications found matching the criteria. Try without filters or check device connection.")
                return
                
            # Display the apps in a more readable format
            print(f"Found {len(apps_list)} applications:")
            
            # Default is now compact one-line format, 
            # JSON format only if --json flag is used
            if hasattr(args, 'json') and args.json:
                # Display full JSON with proper formatting
                print(json.dumps(apps_list, indent=2, ensure_ascii=False))
            else:
                # Display apps in one line per app format (default)
                for i, app in enumerate(apps_list, 1):
                    if not isinstance(app, dict):
                        # Skip non-dictionary entries
                        continue
                        
                    app_name = app.get("app_name", "Unknown")
                    package_name = app.get("package_name", "")
                    app_type = "System" if app.get("is_system", False) else "User"
                    
                    # Add version info if available
                    version_info = f" v{app.get('version_name', '')}" if app.get('version_name') else ""
                    
                    print(f"{i}. {app_name}{version_info} ({package_name}) - {app_type}")
                    # Flush after each print to ensure output is visible immediately
                    sys.stdout.flush()
        else:
            # Unexpected result type
            print(f"❌ Unexpected result type: {type(result)}")
            if args.debug:
                print(f"Result: {result}")
            
    except Exception as e:
        logger.error(f"Error listing applications: {str(e)}")
        print(f"❌ Failed to list applications: {str(e)}")
        if args.debug or args.verbose:
            import traceback
            traceback.print_exc()


# Updated command functions with more descriptive names
async def screen_analysis(args):
    """Analyze current screen and return structured information
    
    This command gets the current screen content and analyzes it, providing:
    - Text elements classified by region (top/middle/bottom)
    - UI pattern detection (such as list view, bottom navigation bar, etc.)
    - Clickable element information
    - Suggested actions
    
    Suitable for understanding screen content and deciding next steps for interaction.
    """
    result = await analyze_screen()
    print(format_json_output(result, args.raw))


async def screen_interact(args):
    """Execute screen interaction actions
    
    Unified interaction command supporting multiple interaction methods:
    - tap: Tap screen (coordinates or element)
    - swipe: Swipe screen
    - key: Key operation
    - text: Input text
    - find: Find element
    - wait: Wait for element to appear
    - scroll: Scroll to find element
    
    Each interaction method requires different parameters in key=value format.
    """
    params = {}
    
    # Parse command line arguments
    for param in args.params:
        if "=" in param:
            key, value = param.split("=", 1)
            # Try to convert numeric values
            try:
                if "." in value:
                    params[key] = float(value)
                else:
                    params[key] = int(value)
            except ValueError:
                # Handle boolean values
                if value.lower() in ("true", "yes", "y"):
                    params[key] = True
                elif value.lower() in ("false", "no", "n"):
                    params[key] = False
                else:
                    params[key] = value
    
    # Log what we're about to do
    if args.verbose:
        logger.info(f"Executing screen interaction: {args.action} with parameters: {params}")
    
    # Execute the interaction
    result = await interact_with_screen(args.action, params)
    
    # Debug output if requested
    if args.debug:
        debug_json_response(result, f"{args.action} result:")
    
    # Parse and provide more detailed output
    try:
        result_data = json.loads(result)
        
        # Format output based on action type
        if args.action == "find" and result_data.get("status") == "success":
            element_count = result_data.get("count", 0)
            if element_count > 0:
                elements = result_data.get("elements", [])
                print(f"✅ Found {element_count} element(s) matching {params.get('value', '')}")
                
                # Show detailed info for found elements (limited to prevent excessive output)
                for i, element in enumerate(elements[:3]):
                    print(f"  Element {i+1}:")
                    if "text" in element and element["text"]:
                        print(f"    Text: {element['text']}")
                    if "resource_id" in element and element["resource_id"]:
                        print(f"    ID: {element['resource_id']}")
                    if "bounds" in element:
                        print(f"    Bounds: {element['bounds']}")
                    if "clickable" in element:
                        print(f"    Clickable: {element['clickable']}")
                
                # If there are more elements, indicate how many more
                if element_count > 3:
                    print(f"  ... and {element_count - 3} more element(s)")
            else:
                print(f"❌ No elements found matching {params.get('value', '')}")
        
        elif args.action == "tap" and result_data.get("status") == "success":
            if "element_text" in params:
                print(f"✅ Tapped element with text '{params['element_text']}'")
            else:
                print(f"✅ Tapped screen at coordinates ({params.get('x', 0)}, {params.get('y', 0)})")
        
        elif args.action == "swipe" and result_data.get("status") == "success":
            print(f"✅ Swiped from ({params.get('x1', 0)}, {params.get('y1', 0)}) to ({params.get('x2', 0)}, {params.get('y2', 0)})")
        
        elif args.action == "scroll" and result_data.get("status") == "success":
            print(f"✅ Found element '{params.get('value', '')}' after scrolling {result_data.get('swipes_performed', 0)} times")
            if result_data.get("element"):
                elem = result_data.get("element", {})
                if "text" in elem:
                    print(f"  Text: {elem['text']}")
                if "bounds" in elem:
                    print(f"  Bounds: {elem['bounds']}")
        
        else:
            # For other cases, use the default formatter
            print(format_json_output(result))
    
    except json.JSONDecodeError:
        # If not valid JSON, print the raw result
        print(result)


# Helper functions for debugging
def debug_json_response(response: str, context: str = "") -> None:
    """Print detailed debug information about a JSON response.
    
    Args:
        response: The JSON response string
        context: Optional context information to include in output
    """
    if not response:
        logger.debug(f"{context} Response is empty")
        return
        
    try:
        if not isinstance(response, str):
            logger.debug(f"{context} Response is not a string: {type(response)}")
            return
            
        # Try to parse as JSON
        data = json.loads(response)
        
        # Log the structure
        logger.debug(f"{context} Response type: JSON")
        logger.debug(f"{context} Status: {data.get('status', 'unknown')}")
        logger.debug(f"{context} Keys: {list(data.keys())}")
        
        # Log more detailed info based on common structures
        if "elements" in data:
            element_count = len(data.get("elements", []))
            logger.debug(f"{context} Elements count: {element_count}")
            
            # Sample first element
            if element_count > 0:
                sample = data["elements"][0]
                logger.debug(f"{context} Sample element keys: {list(sample.keys())}")
        
    except json.JSONDecodeError:
        # Not JSON, log the beginning of the string
        logger.debug(f"{context} Response is not valid JSON")
        if len(response) > 100:
            logger.debug(f"{context} Response (truncated): {response[:100]}...")
        else:
            logger.debug(f"{context} Response: {response}")
    except Exception as e:
        logger.debug(f"{context} Error processing response: {str(e)}")


def _is_valid_phone_number(number: str) -> bool:
    """验证电话号码格式是否有效
    
    Args:
        number: 标准化后的电话号码（只包含数字和加号）
        
    Returns:
        bool: 如果电话号码格式有效返回True，否则返回False
    """
    # 移除所有非数字字符（保留加号）
    clean_number = ''.join(c for c in number if c.isdigit() or c == '+')
    
    # 检查长度
    if len(clean_number) < 7 or len(clean_number) > 15:
        return False
        
    # 检查是否以加号开头（国际号码）
    if clean_number.startswith('+'):
        # 国际号码应该以国家代码开头
        if not clean_number[1:].isdigit():
            return False
        # 国际号码长度应该在8-15位之间
        if len(clean_number) < 8 or len(clean_number) > 15:
            return False
    else:
        # 本地号码应该全是数字
        if not clean_number.isdigit():
            return False
        # 本地号码长度应该在7-11位之间
        if len(clean_number) < 7 or len(clean_number) > 11:
            return False
            
    # 检查数字是否合理（避免全是相同数字或明显错误的号码）
    if len(set(clean_number.lstrip('+'))) < 3:
        return False
        
    return True


async def open_web(args):
    """Open a URL in the device's default browser."""
    result = await open_url(args.url)
    print(format_json_output(result))


async def monitor_ui(args):
    """Monitor UI for changes."""
    from .tools.ui_monitor import mcp_monitor_ui_changes
    
    # 将命令行参数映射到函数参数
    result = await mcp_monitor_ui_changes(
        interval_seconds=args.interval,
        max_duration_seconds=args.duration,
        watch_for=args.watch_for,
        target_text=args.text if hasattr(args, 'text') else "",
        target_id=args.id if hasattr(args, 'id') else "",
        target_class=args.class_name if hasattr(args, 'class_name') else "",
        target_content_desc=args.content_desc if hasattr(args, 'content_desc') else ""
    )
    
    print(format_json_output(result, args.raw if hasattr(args, 'raw') else False))


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Phone MCP CLI - Control your Android phone from the command line")
    
    # Add general parameters
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable detailed debug output (implies verbose)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Call command
    call_parser = subparsers.add_parser("call", help="Make a phone call")
    call_parser.add_argument("number", help="Phone number to call")
    
    # End call command
    subparsers.add_parser("hangup", help="End the current call")
    
    # Check device command
    subparsers.add_parser("check", help="Check device connection")
    
    # Send SMS command
    send_sms_parser = subparsers.add_parser("send-sms", help="Send a text message")
    send_sms_parser.add_argument("number", help="Phone number to send message to")
    send_sms_parser.add_argument("text", help="Message content")
    send_sms_parser.add_argument("--enhanced", "-e", action="store_true", help="Force use of enhanced mode with screen interaction")
    send_sms_parser.add_argument("--auto-enhance", "-a", action="store_true", help="Automatically use enhanced mode if basic method fails or can't be verified")
    
    # Check messages command
    check_messages_parser = subparsers.add_parser("messages", help="Check recent text messages")
    check_messages_parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")
    
    # Contacts command
    contacts_parser = subparsers.add_parser("contacts", help="Retrieve contacts from the phone")
    contacts_parser.add_argument("--limit", type=int, default=20, help="Number of contacts to retrieve")
    contacts_parser.add_argument("--json", "-j", action="store_true", help="Show contacts in JSON format instead of default compact format")
    contacts_parser.add_argument("--compact", "-c", action="store_true", help="Show contacts in compact one-line format (default behavior)")
    contacts_parser.add_argument("--oneline", "-o", action="store_true", help="Alias for --compact (default behavior)")
    
    # Window information command
    subparsers.add_parser("window", help="Get current window information")
    
    # App shortcuts command
    shortcuts_parser = subparsers.add_parser("shortcuts", help="Get app shortcuts")
    shortcuts_parser.add_argument("--package", help="Specific package to get shortcuts for")
    
    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch a specific activity")
    launch_parser.add_argument("component", help="App component in format 'package/activity'")
    launch_parser.add_argument("--action", help="Intent action to use")
    launch_parser.add_argument("--extras", help="Additional intent arguments")
    
    # Screenshot command
    subparsers.add_parser("screenshot", help="Take a screenshot of the current screen")
    
    # Screen recording command
    record_parser = subparsers.add_parser("record", help="Record the screen for a specified duration")
    record_parser.add_argument("--duration", type=int, default=30, help="Recording duration in seconds (max 180)")
    
    # Media control command
    subparsers.add_parser("media", help="Play or pause media")
    
    # App launch command
    app_parser = subparsers.add_parser("app", help="Open an app")
    app_parser.add_argument("name", help="App name or package name")
    
    # App termination command
    app_close_parser = subparsers.add_parser("close-app", help="Force stop an app")
    app_close_parser.add_argument("package", help="Package name of the app to terminate")
    
    # List installed apps command
    apps_list_parser = subparsers.add_parser("list-apps", help="List installed applications")
    apps_list_parser.add_argument("--filter", help="Filter apps by name")
    apps_list_parser.add_argument("--system", action="store_true", help="Show only system apps")
    apps_list_parser.add_argument("--third-party", action="store_true", help="Show only third-party apps")
    apps_list_parser.add_argument("--limit", type=int, default=50, help="Maximum number of apps to list")
    apps_list_parser.add_argument("--json", "-j", action="store_true", help="Show apps in JSON format instead of default compact format")
    # Keep backward compatibility but with updated help text
    apps_list_parser.add_argument("--compact", "-c", action="store_true", help="Show apps in compact one-line format (default behavior)")
    apps_list_parser.add_argument("--oneline", "-o", action="store_true", help="Alias for --compact (default behavior)")
    
    # Alarm command
    alarm_parser = subparsers.add_parser("alarm", help="Set an alarm")
    alarm_parser.add_argument("hour", type=int, help="Hour (0-23)")
    alarm_parser.add_argument("minute", type=int, help="Minute (0-59)")
    alarm_parser.add_argument("--label", default="Alarm", help="Alarm label")
    
    # Incoming call command
    subparsers.add_parser("incoming", help="Check for incoming calls")
    
    # POI command for getting location information
    poi_parser = subparsers.add_parser("get-poi", help="Get phone numbers from nearby businesses and POIs by location")
    poi_parser.add_argument("location", help="Central coordinate point (longitude,latitude)")
    poi_parser.add_argument("--keywords", help="Search keywords (e.g., 'restaurant', 'hotel')")
    poi_parser.add_argument("--radius", default="1000", help="Search radius in meters (default: 1000)")
    poi_parser.add_argument("--debug", action="store_true", help="Show detailed API response for debugging")
    
    # Updated command names, more descriptive
    screen_analysis_parser = subparsers.add_parser("analyze-screen", help="Analyze current screen and return structured information")
    screen_analysis_parser.add_argument("--raw", action="store_true", help="Return raw JSON data instead of prettified output")
    
    # Updated command name, removing "ai" prefix
    screen_interact_parser = subparsers.add_parser("screen-interact", help="Execute screen interaction")
    screen_interact_parser.add_argument("action", choices=["tap", "swipe", "key", "text", "find", "wait", "scroll"], 
                                   help="Interaction action type")
    screen_interact_parser.add_argument("params", nargs="+", help="Interaction parameters in key=value format")
    
    # Open URL command
    open_url_parser = subparsers.add_parser("open-url", help="Open a URL in the device's default browser")
    open_url_parser.add_argument("url", help="URL to open (http:// or https:// will be added if missing)")
    
    # Add UI monitoring command
    monitor_parser = subparsers.add_parser("monitor-ui", help="Monitor UI for changes")
    monitor_parser.add_argument("--interval", type=float, default=1.0, help="Time between checks in seconds")
    monitor_parser.add_argument("--duration", type=float, default=60.0, help="Maximum monitoring time in seconds")
    monitor_parser.add_argument("--watch-for", type=str, default="any_change", 
                              help="What to watch for: any_change, text_appears, id_appears, etc.")
    monitor_parser.add_argument("--text", type=str, help="Text to watch for")
    monitor_parser.add_argument("--id", type=str, help="Element ID to watch for")
    monitor_parser.add_argument("--class-name", type=str, help="Element class to watch for")
    monitor_parser.add_argument("--content-desc", type=str, help="Content description to watch for")
    monitor_parser.add_argument("--raw", action="store_true", help="Output raw JSON")
    monitor_parser.set_defaults(func=monitor_ui)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger("phone_mcp").setLevel(logging.DEBUG)
        # Override verbose to be true if debug is enabled
        args.verbose = True
    elif args.verbose:
        logging.getLogger("phone_mcp").setLevel(logging.INFO)
    
    # Command mapping, keeping basic functionality, adding new unified commands
    commands = {
        # Basic communication functions
        "call": call,
        "hangup": hangup,
        "check": check_device,
        "send-sms": send_sms,
        "messages": check_messages,
        
        # Contact/app management functions
        "contacts": check_contacts,
        "window": check_window,
        "shortcuts": check_shortcuts,
        "launch": launch,
        "app": launch_app,
        "close-app": close_app,
        "list-apps": list_apps,
        "alarm": alarm,
        "incoming": receive_call,
        
        # Media functions
        "screenshot": screenshot,
        "record": record,
        "media": media_control,
        
        # Browser functions
        "open-url": open_web,
        
        # Map functions
        "get-poi": get_phone_by_poi,
        
        # Updated command names
        "analyze-screen": screen_analysis,
        "screen-interact": screen_interact,
        
        # UI monitoring command
        "monitor-ui": monitor_ui,
    }
    
    # Check if command exists
    if not args.command:
        parser.print_help()
        return
    elif args.command not in commands:
        print(f"Error: Unknown command '{args.command}'")
        parser.print_help()
        return
    
    # Execute command
    try:
        asyncio.run(commands[args.command](args))
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
