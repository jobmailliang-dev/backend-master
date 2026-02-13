"""Test API 端点 - 使用 @inject 注解"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.modules import TestService, Test, get_injector

router = APIRouter(prefix="/api/test", tags=["test"])

# 获取 Injector 实例
_injector = get_injector()


@router.get("/health")
async def test_health():
    """健康检查"""
    return {"status": "ok", "module": "test"}


@router.post("/", response_model=dict)
async def create_test(request: dict):
    """创建 Test 记录 - 通过 Injector 获取服务"""
    # 从 Injector 获取 TestService（单例）
    service: TestService = _injector.get(TestService)

    test = service.create(request.get("name"), request.get("value"))
    return test.to_dict()


@router.get("/", response_model=List[dict])
async def list_tests():
    """列出所有 Test 记录"""
    service: TestService = _injector.get(TestService)
    tests = service.list_all()
    return [test.to_dict() for test in tests]


@router.get("/{test_id}", response_model=dict)
async def get_test(test_id: int):
    """获取单个 Test 记录"""
    service: TestService = _injector.get(TestService)
    test = service.get_by_id(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return test.to_dict()


@router.put("/{test_id}", response_model=dict)
async def update_test(test_id: int, request: dict):
    """更新 Test 记录"""
    service: TestService = _injector.get(TestService)
    test = service.update(test_id, request.get("name"), request.get("value"))
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return test.to_dict()


@router.delete("/{test_id}")
async def delete_test(test_id: int):
    """删除 Test 记录"""
    service: TestService = _injector.get(TestService)
    success = service.delete(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"message": "Test deleted successfully"}
