"""工具管理 API 测试用例"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestToolsAPI:
    """工具 API 测试类"""

    def test_get_tools_empty_list(self, client):
        """测试获取空工具列表"""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_tools_with_data(self, client, sample_tool_data):
        """测试获取工具列表（有数据时）"""
        # 先创建一个工具
        response = client.post("/api/tools", json=sample_tool_data)
        assert response.status_code == 200

        # 获取列表
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        # 清理测试数据
        tools = [t for t in data["data"] if t["name"] == sample_tool_data["name"]]
        for tool in tools:
            client.delete(f"/api/tools?id={tool['id']}")

    def test_get_single_tool(self, client, sample_tool_data):
        """测试获取单个工具"""
        # 先创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        assert create_response.status_code == 200
        created_tool = create_response.json()["data"]
        tool_id = created_tool["id"]

        # 获取单个工具
        response = client.get(f"/api/tools?id={tool_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == tool_id
        assert data["data"]["name"] == sample_tool_data["name"]

        # 清理
        client.delete(f"/api/tools?id={tool_id}")

    def test_get_nonexistent_tool(self, client):
        """测试获取不存在的工具"""
        response = client.get("/api/tools?id=99999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_create_tool_success(self, client, sample_tool_data):
        """测试成功创建工具"""
        response = client.post("/api/tools", json=sample_tool_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_tool_data["name"]
        assert data["data"]["description"] == sample_tool_data["description"]
        assert data["data"]["is_active"] == sample_tool_data["is_active"]

        # 清理
        client.delete(f"/api/tools?id={data['data']['id']}")

    def test_create_tool_missing_name(self, client):
        """测试创建工具缺少名称"""
        response = client.post("/api/tools", json={"description": "描述"})
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_create_tool_duplicate_name(self, client, sample_tool_data):
        """测试创建重复名称的工具"""
        # 创建第一个工具
        response1 = client.post("/api/tools", json=sample_tool_data)
        assert response1.status_code == 200

        # 尝试创建同名工具
        response2 = client.post("/api/tools", json=sample_tool_data)
        assert response2.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "已存在" in data["error"] or "exist" in data["error"].lower()

        # 清理
        client.delete(f"/api/tools?id={response1.json()['data']['id']}")

    def test_update_tool_success(self, client, sample_tool_data):
        """测试成功更新工具"""
        # 创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        tool_id = create_response.json()["data"]["id"]

        # 更新工具
        update_data = {
            "name": "updated_tool",
            "description": "更新后的描述",
            "is_active": False
        }
        response = client.put(f"/api/tools?id={tool_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["description"] == update_data["description"]
        assert data["data"]["is_active"] is False

        # 清理
        client.delete(f"/api/tools?id={tool_id}")

    def test_update_nonexistent_tool(self, client):
        """测试更新不存在的工具"""
        response = client.put("/api/tools?id=99999", json={"name": "test"})
        assert response.status_code == 404

    def test_delete_tool_success(self, client, sample_tool_data):
        """测试成功删除工具"""
        # 创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        tool_id = create_response.json()["data"]["id"]

        # 删除工具
        response = client.delete(f"/api/tools?id={tool_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证已删除
        get_response = client.get(f"/api/tools?id={tool_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_tool(self, client):
        """测试删除不存在的工具"""
        response = client.delete("/api/tools?id=99999")
        assert response.status_code == 404

    def test_toggle_tool_active(self, client, sample_tool_data):
        """测试切换工具启用状态"""
        # 创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        tool_id = create_response.json()["data"]["id"]

        # 停用工具
        response = client.put(f"/api/tools/active?id={tool_id}", json={"is_active": False})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is False
        assert "停用" in data["message"]

        # 启用工具
        response = client.put(f"/api/tools/active?id={tool_id}", json={"is_active": True})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is True
        assert "启用" in data["message"]

        # 清理
        client.delete(f"/api/tools?id={tool_id}")

    def test_import_tools(self, client, sample_tool_list):
        """测试批量导入工具"""
        response = client.post("/api/tools/import", json={"tools": sample_tool_list})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

        # 清理
        for tool in data["data"]:
            client.delete(f"/api/tools?id={tool['id']}")

    def test_export_tools(self, client, sample_tool_data):
        """测试导出工具"""
        # 先创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        tool_id = create_response.json()["data"]["id"]

        # 导出
        response = client.get("/api/tools/export")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

        # 清理
        client.delete(f"/api/tools?id={tool_id}")

    def test_get_inheritable_tools(self, client, sample_tool_data):
        """测试获取可继承工具列表"""
        # 创建工具
        create_response = client.post("/api/tools", json=sample_tool_data)
        tool_id = create_response.json()["data"]["id"]

        # 获取可继承列表
        response = client.get("/api/tools/inheritable")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

        # 清理
        client.delete(f"/api/tools?id={tool_id}")


class TestToolModels:
    """工具模型测试类"""

    def test_tool_parameter_to_dict(self):
        """测试 ToolParameter 转换为字典"""
        from src.modules.tools.models import ToolParameter

        param = ToolParameter(
            name="test_param",
            description="测试参数",
            type="string",
            required=True,
            default="default_value",
            enum=["a", "b", "c"]
        )

        result = param.to_dict()
        assert result["name"] == "test_param"
        assert result["type"] == "string"
        assert result["required"] is True
        assert result["default"] == "default_value"
        assert result["enum"] == ["a", "b", "c"]

    def test_tool_parameter_from_dict(self):
        """测试从字典创建 ToolParameter"""
        from src.modules.tools.models import ToolParameter

        data = {
            "name": "test_param",
            "description": "测试参数",
            "type": "number",
            "required": False,
            "default": "123"
        }

        param = ToolParameter.from_dict(data)
        assert param.name == "test_param"
        assert param.type == "number"
        assert param.required is False

    def test_tool_to_dict(self):
        """测试 Tool 转换为字典"""
        from src.modules.tools.models import Tool

        tool = Tool(
            id=1,
            name="test_tool",
            description="测试工具",
            is_active=True,
            parameters_json='[{"name":"p1","description":"p1 desc","type":"string","required":true}]',
            code="print('hello')"
        )

        result = tool.to_dict()
        assert result["id"] == 1
        assert result["name"] == "test_tool"
        assert result["is_active"] is True
        assert len(result["parameters"]) == 1
        assert result["parameters"][0]["name"] == "p1"


class TestToolService:
    """工具服务测试类"""

    def test_service_create_tool_validation(self):
        """测试服务层工具创建验证"""
        from src.modules.tools.service import ToolService
        from src.modules.tools.dao import ToolDao
        from unittest.mock import MagicMock

        # 模拟 DAO
        mock_dao = MagicMock(spec=ToolDao)

        # 测试缺少名称
        mock_dao.get_by_name.return_value = None

        service = ToolService(mock_dao)

        # 缺少名称
        success, msg, data = service.create_tool({"description": "test"})
        assert success is False
        assert "名称" in msg

        # 缺少描述
        success, msg, data = service.create_tool({"name": "test"})
        assert success is False
        assert "描述" in msg

        # 重复名称
        mock_dao.get_by_name.return_value = {"id": 1, "name": "test"}
        success, msg, data = service.create_tool({"name": "test", "description": "desc"})
        assert success is False
        assert "已存在" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
