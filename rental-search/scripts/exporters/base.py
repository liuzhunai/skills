"""Base exporter interface."""

from abc import ABC, abstractmethod
from typing import List

from ..models.listing import Listing


class Exporter(ABC):
    """导出器抽象基类

    定义导出房源数据的标准接口。
    """

    @abstractmethod
    def export(self, listings: List[Listing], output_path: str, **kwargs) -> str:
        """导出房源数据

        Args:
            listings: 房源列表
            output_path: 输出路径
            **kwargs: 额外参数

        Returns:
            实际输出路径
        """
        pass

    @abstractmethod
    def get_format(self) -> str:
        """获取导出格式"""
        pass
