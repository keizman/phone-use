import os
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# 导入被测试的模块
import phone_mcp
from phone_mcp.core import check_device_connection, run_command
from phone_mcp.tools.maps import get_poi_info_by_location, HAS_VALID_API_KEY


# Fixtures
@pytest.fixture
def adb_mock():
    """模拟ADB命令执行的fixture"""
    with patch("phone_mcp.core.run_command") as mock:
        yield mock


@pytest.fixture
def api_key_env():
    """设置API密钥环境变量的fixture"""
    old_key = os.environ.get("AMAP_MAPS_API_KEY")
    os.environ["AMAP_MAPS_API_KEY"] = "test_api_key"
    yield
    if old_key:
        os.environ["AMAP_MAPS_API_KEY"] = old_key
    else:
        os.environ.pop("AMAP_MAPS_API_KEY", None)


@pytest.fixture
def requests_mock():
    """模拟API请求的fixture"""
    with patch("phone_mcp.tools.maps.requests.get") as mock:
        yield mock


# 辅助函数
def async_return(result):
    """将同步结果包装为异步结果"""
    f = asyncio.Future()
    f.set_result(result)
    return f


# 测试设备连接功能
class TestDeviceConnection:
    def test_check_device_connection_connected(self, adb_mock):
        """测试设备已连接的情况"""
        # 模拟adb devices命令返回连接的设备
        adb_mock.return_value = async_return(
            (True, "List of devices attached\nXXXXXXXX\tdevice\n")
        )

        # 执行测试
        result = asyncio.run(check_device_connection())

        # 验证结果
        assert "connected and ready" in result
        adb_mock.assert_called_once_with("adb devices")

    def test_check_device_connection_not_connected(self, adb_mock):
        """测试设备未连接的情况"""
        # 模拟adb devices命令返回无设备
        adb_mock.return_value = async_return((True, "List of devices attached\n"))

        # 执行测试
        result = asyncio.run(check_device_connection())

        # 验证结果
        assert "No device found" in result
        assert "connected and ready" not in result

    def test_check_device_connection_failure(self, adb_mock):
        """测试命令执行失败的情况"""
        # 模拟adb命令执行失败
        adb_mock.return_value = async_return((False, "Command failed: adb not found"))

        # 执行测试
        result = asyncio.run(check_device_connection())

        # 验证结果
        assert "Failed to check device connection" in result
        assert "adb not found" in result


# 测试高德地图API功能
class TestMapAPI:
    @pytest.mark.usefixtures("api_key_env")
    def test_api_key_env_variable(self):
        """测试API密钥环境变量设置"""
        # 重新导入模块，使环境变量生效
        import importlib

        importlib.reload(phone_mcp.tools.maps)
        from phone_mcp.tools.maps import HAS_VALID_API_KEY

        # 验证HAS_VALID_API_KEY为True
        assert HAS_VALID_API_KEY is True

    @pytest.mark.usefixtures("api_key_env")
    def test_get_poi_info_by_location_success(self, requests_mock):
        """测试POI搜索成功的情况"""
        # 准备模拟响应数据
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "1",
            "pois": [
                {
                    "name": "测试餐厅",
                    "address": "测试地址",
                    "tel": "12345678901",
                    "location": "116.480053,39.987005",
                }
            ],
        }
        requests_mock.return_value = mock_response

        # 执行测试
        result = asyncio.run(
            get_poi_info_by_location("116.480053,39.987005", "餐厅", "1000")
        )
        result_data = json.loads(result)

        # 验证结果
        assert "测试餐厅" in result
        assert "pois" in result_data

        # 验证请求参数
        requests_mock.assert_called_once()
        args, kwargs = requests_mock.call_args
        assert kwargs["params"]["location"] == "116.480053,39.987005"
        assert kwargs["params"]["radius"] == "1000"
        assert "key" in kwargs["params"]

    @pytest.mark.usefixtures("api_key_env")
    def test_get_poi_info_by_location_api_error(self, requests_mock):
        """测试API返回错误的情况"""
        # 准备模拟响应数据
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "0", "info": "INVALID_KEY"}
        requests_mock.return_value = mock_response

        # 执行测试
        result = asyncio.run(get_poi_info_by_location("116.480053,39.987005", "餐厅"))
        result_data = json.loads(result)

        # 验证结果
        assert "error" in result_data
        assert "POI search failed" in result_data["error"]
        assert "INVALID_KEY" in result

    def test_get_poi_info_by_location_no_api_key(self):
        """测试未设置API密钥的情况"""
        # 确保环境变量未设置
        if "AMAP_MAPS_API_KEY" in os.environ:
            del os.environ["AMAP_MAPS_API_KEY"]

        # 重新导入模块
        import importlib

        importlib.reload(phone_mcp.tools.maps)
        from phone_mcp.tools.maps import get_poi_info_by_location as get_poi

        # 执行测试
        result = asyncio.run(get_poi("116.480053,39.987005"))
        result_data = json.loads(result)

        # 验证结果
        assert "error" in result_data
        assert "API key not configured" in result_data["error"]


# 测试CLI命令
class TestCLICommands:
    def test_cli_commands_availability(self):
        """测试CLI命令是否可用"""
        from phone_mcp.cli import main
        import inspect

        # 获取main函数源代码
        source = inspect.getsource(main)

        # 检查基本命令是否存在
        assert "check" in source
        assert "screenshot" in source
        assert "contacts" in source

        # 检查地图相关命令是否依赖于API密钥
        assert "if HAS_VALID_API_KEY:" in source
        assert "get-poi" in source
