"""Configuration management using Singleton pattern."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class Config:
    """配置数据类"""

    # 默认城市
    default_city: str = "北京"
    default_city_code: str = "bj"

    # 默认搜索参数
    default_radius_km: float = 5.0
    default_days: int = 15
    max_districts: int = 3

    # 地铁站搜索范围
    subway_max_distance_km: float = 3.0

    # 平台配置
    enabled_platforms: list = field(default_factory=lambda: ["wuba"])

    # 输出配置
    output_directory: str = "."

    # 其他配置
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器 (单例模式)

    确保全局只有一个配置实例。
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = Config()
        return cls._instance

    @classmethod
    def get_config(cls) -> Config:
        """获取配置实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._config

    @classmethod
    def update_config(cls, **kwargs) -> Config:
        """更新配置

        Args:
            **kwargs: 配置项

        Returns:
            更新后的配置
        """
        config = cls.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.custom_settings[key] = value
        return config

    @classmethod
    def reset(cls):
        """重置配置为默认值"""
        cls._config = Config()

    @classmethod
    def set_city(cls, city: str, city_code: str = None):
        """设置默认城市

        Args:
            city: 城市名称
            city_code: 城市代码（可选，自动推断）
        """
        # 常见城市代码映射
        city_codes = {
            "北京": "bj",
            "上海": "sh",
            "广州": "gz",
            "深圳": "sz",
            "杭州": "hz",
            "成都": "cd",
            "武汉": "wh",
            "南京": "nj",
        }

        code = city_code or city_codes.get(city, city[:2].lower())
        cls.update_config(default_city=city, default_city_code=code)

    @classmethod
    def to_dict(cls) -> dict:
        """导出配置为字典"""
        config = cls.get_config()
        return {
            "default_city": config.default_city,
            "default_city_code": config.default_city_code,
            "default_radius_km": config.default_radius_km,
            "default_days": config.default_days,
            "max_districts": config.max_districts,
            "subway_max_distance_km": config.subway_max_distance_km,
            "enabled_platforms": config.enabled_platforms,
            "output_directory": config.output_directory,
            "custom_settings": config.custom_settings,
        }
