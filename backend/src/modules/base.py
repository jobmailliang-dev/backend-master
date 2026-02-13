"""Service 层基础接口模块"""

from typing import TypeVar, Generic, List, Optional, Union


class ValidException(Exception):
    """校验异常基类"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ApiException(Exception):
    """API 业务异常

    抛出此异常时，RequestLoggingMiddleware 会返回 400 状态码给前端。
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


T = TypeVar("T")


class IService(Generic[T]):
    """Service 层泛型接口基类

    定义了 CRUD 操作的标准接口，所有业务 Service 应实现此接口。
    """

    def get_list(self) -> List[T]:
        """获取所有实体列表

        Returns:
            List[T]: DTO 列表
        """
        raise NotImplementedError

    def get_one(self, id: int) -> Optional[T]:
        """根据 ID 获取单个 DTO

        Args:
            id: 实体 ID

        Returns:
            Optional[T]: 找到返回 DTO，否则返回 None
        """
        raise NotImplementedError

    def create_one(self, data: dict) -> T:
        """创建新实体

        Args:
            data: 创建数据字典

        Returns:
            T: 创建的 DTO
        """
        raise NotImplementedError

    def update(self, id: int, data: dict) -> Optional[T]:
        """更新实体

        Args:
            id: 实体 ID
            data: 更新数据字典

        Returns:
            Optional[T]: 更新后的 DTO，未找到返回 None
        """
        raise NotImplementedError

    def delete_by_id(self, id: int) -> bool:
        """删除实体

        Args:
            id: 实体 ID

        Returns:
            bool: 删除成功返回 True
        """
        raise NotImplementedError

    def convert_dto(self, entity: Union[dict, object]) -> T:
        """将实体转换为 DTO

        Args:
            entity: 实体对象或字典

        Returns:
            T: DTO 对象
        """
        raise NotImplementedError


__all__ = ["ValidException", "ApiException", "IService"]
