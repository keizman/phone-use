import os
import json
import pytest
from unittest.mock import patch, MagicMock

# 导入被测试的模块
# 修正导入路径
from phone_mcp.tools.maps import get_poi_info_by_location, HAS_VALID_API_KEY
import phone_mcp


@pytest.fixture
def amap_key():
    """提供高德地图API密钥的固定装置"""
    original_key = os.environ.get("AMAP_MAPS_API_KEY")
    os.environ["AMAP_MAPS_API_KEY"] = "test_api_key"
    yield "test_api_key"
    if original_key:
        os.environ["AMAP_MAPS_API_KEY"] = original_key
    else:
        del os.environ["AMAP_MAPS_API_KEY"]


@pytest.fixture
def requests_mock():
    """模拟高德API响应的固定装置"""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        yield mock_get


@pytest.mark.amap
class TestPOISearch:
    """测试POI信息搜索功能"""

    @pytest.mark.usefixtures("amap_key")
    def test_api_key_env_variable(self):
        """测试API密钥环境变量设置"""
        # 重新导入模块，使环境变量生效
        import importlib

        importlib.reload(phone_mcp.tools.maps)
        from phone_mcp.tools.maps import HAS_VALID_API_KEY

        # 验证HAS_VALID_API_KEY为True
        assert HAS_VALID_API_KEY is True

    def test_get_poi_info_by_location_success(self, amap_key, requests_mock):
        """测试POI搜索成功的情况"""
        # 准备模拟响应数据
        mock_data = {
            "status": "1",
            "pois": [
                {
                    "id": "B000A816R6",
                    "name": "测试餐厅",
                    "type": "餐饮服务;中餐厅;中餐厅",
                    "address": "北京市海淀区中关村南大街5号",
                    "location": "116.310905,39.992806",
                    "tel": "010-12345678",
                    "distance": "500",
                }
            ],
            "count": "1",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        requests_mock.return_value = mock_response

        # 执行被测试的函数
        location = "116.310905,39.992806"
        keywords = "餐厅"
        radius = "1000"
        result = get_poi_info_by_location(location, keywords, radius)

        # 验证结果
        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert "测试餐厅" in result
        assert "pois" in result_dict
        assert len(result_dict["pois"]) > 0
        assert "tel" in result_dict["pois"][0]

        # 验证请求参数
        requests_mock.assert_called_once()
        args, kwargs = requests_mock.call_args
        assert kwargs["params"]["location"] == location
        assert kwargs["params"]["radius"] == radius
        assert kwargs["params"]["keywords"] == keywords
        assert "key" in kwargs["params"]

    def test_get_poi_info_by_location_api_error(self, amap_key, requests_mock):
        """测试API返回错误的情况"""
        # 准备模拟响应数据
        mock_data = {"status": "0", "info": "INVALID_KEY"}
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        requests_mock.return_value = mock_response

        # 执行被测试的函数
        result = get_poi_info_by_location("116.310905,39.992806", "餐厅")

        # 验证结果
        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert "error" in result_dict
        assert "POI search failed" in result_dict["error"]
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
        result = get_poi("116.310905,39.992806")

        # 验证结果
        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert "error" in result_dict
        assert "API key not configured" in result_dict["error"]

    def test_get_poi_info_by_location_request_exception(self, amap_key):
        """测试请求异常的情况"""
        # 确保环境变量设置为有效值
        assert os.environ.get("AMAP_MAPS_API_KEY") is not None

        # 重新导入模块，使环境变量生效
        import importlib

        importlib.reload(phone_mcp.tools.maps)
        from phone_mcp.tools.maps import get_poi_info_by_location as get_poi

        # 使用特定的patch范围模拟异常
        with patch("phone_mcp.tools.maps.requests.get") as mock_get:
            # 模拟请求抛出异常
            mock_get.side_effect = Exception("Connection error")

            # 执行被测试的函数
            result = get_poi("116.310905,39.992806")

            # 验证结果
            assert isinstance(result, str)
            result_dict = json.loads(result)
            assert "error" in result_dict
            assert "Request failed" in result_dict["error"]
            assert "Connection error" in result_dict["error"]
