"""Platform factory using Factory pattern."""

from typing import Dict, Type, List, Optional

from .base import PlatformAdapter
from .wuba import WubaAdapter


class PlatformFactory:
    """平台工厂 (工厂模式)

    用于创建和管理不同房源平台的适配器。
    """

    # 注册的平台适配器
    _adapters: Dict[str, Type[PlatformAdapter]] = {
        "wuba": WubaAdapter,
        "58": WubaAdapter,
        "58同城": WubaAdapter,
    }

    # 默认平台
    DEFAULT_PLATFORM = "wuba"

    @classmethod
    def create(cls, platform_name: str = None) -> PlatformAdapter:
        """创建平台适配器

        Args:
            platform_name: 平台名称，不指定则使用默认平台

        Returns:
            平台适配器实例

        Raises:
            ValueError: 平台名称无效
        """
        name = platform_name or cls.DEFAULT_PLATFORM
        name = name.lower()

        if name not in cls._adapters:
            raise ValueError(
                f"Unknown platform: {platform_name}. "
                f"Available: {list(cls._adapters.keys())}"
            )

        return cls._adapters[name]()

    @classmethod
    def register(cls, name: str, adapter_class: Type[PlatformAdapter]):
        """注册新的平台适配器

        Args:
            name: 平台名称
            adapter_class: 适配器类
        """
        cls._adapters[name.lower()] = adapter_class

    @classmethod
    def list_platforms(cls) -> List[str]:
        """列出所有可用平台"""
        # 去重并返回主要名称
        seen = set()
        platforms = []
        for name in cls._adapters.keys():
            adapter = cls._adapters[name]
            if adapter.NAME not in seen:
                seen.add(adapter.NAME)
                platforms.append(adapter.DISPLAY_NAME)
        return platforms

    @classmethod
    def get_adapter_info(cls) -> Dict[str, Dict]:
        """获取所有适配器信息"""
        info = {}
        seen = set()

        for name, adapter_class in cls._adapters.items():
            if adapter_class.NAME not in seen:
                seen.add(adapter_class.NAME)
                adapter = adapter_class()
                info[adapter.NAME] = {
                    "name": adapter.NAME,
                    "display_name": adapter.DISPLAY_NAME,
                    "aliases": [
                        n for n, a in cls._adapters.items() if a == adapter_class
                    ],
                }

        return info

    @classmethod
    def create_multi(cls, platform_names: List[str] = None) -> List[PlatformAdapter]:
        """创建多个平台适配器

        Args:
            platform_names: 平台名称列表，不指定则使用默认平台

        Returns:
            平台适配器实例列表
        """
        if not platform_names:
            return [cls.create()]

        adapters = []
        seen = set()

        for name in platform_names:
            adapter = cls.create(name)
            if adapter.NAME not in seen:
                seen.add(adapter.NAME)
                adapters.append(adapter)

        return adapters
