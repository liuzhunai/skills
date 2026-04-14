"""Base platform adapter using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

from ..models.params import SearchParams
from ..models.listing import Listing


@dataclass
class SearchURL:
    """搜索URL信息"""

    url: str
    district: str
    distance: float
    platform: str


class PlatformAdapter(ABC):
    """平台适配器抽象基类 (策略模式)

    定义房源平台适配器的标准接口，不同平台实现各自的策略。
    """

    # 平台名称
    NAME: str = ""

    # 平台显示名称
    DISPLAY_NAME: str = ""

    @abstractmethod
    def build_search_urls(
        self, params: SearchParams, districts: List[Dict]
    ) -> List[SearchURL]:
        """构建搜索URL列表

        Args:
            params: 搜索参数
            districts: 目标区域列表

        Returns:
            SearchURL 列表
        """
        pass

    @abstractmethod
    def parse_list_page(self, html: str) -> List[Dict]:
        """解析列表页

        Args:
            html: 页面HTML内容

        Returns:
            房源数据字典列表
        """
        pass

    @abstractmethod
    def parse_detail_page(self, html: str, url: str) -> Dict:
        """解析详情页

        Args:
            html: 页面HTML内容
            url: 页面URL

        Returns:
            房源详细数据
        """
        pass

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.NAME

    def get_display_name(self) -> str:
        """获取平台显示名称"""
        return self.DISPLAY_NAME

    @abstractmethod
    def supports_rental_type(self, rental_type: Optional[str]) -> bool:
        """检查是否支持指定的租赁类型

        Args:
            rental_type: 租赁类型

        Returns:
            是否支持
        """
        pass
