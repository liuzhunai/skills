"""Location service for coordinate lookup."""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from .distance import DistanceCalculator


@dataclass
class LocationInfo:
    """地点信息"""

    name: str
    lat: float
    lng: float
    district: Optional[str] = None


class LocationService:
    """地点坐标服务

    提供地点名称到坐标的转换，支持预设地点和行政区划。
    """

    # 预设地点坐标
    PRESET_LOCATIONS: Dict[str, Dict] = {
        "百度科技园": {"lat": 40.0569, "lng": 116.3015, "district": "海淀"},
        "百度大厦": {"lat": 40.0569, "lng": 116.3015, "district": "海淀"},
        "中关村": {"lat": 39.9841, "lng": 116.3075, "district": "海淀"},
        "国贸": {"lat": 39.9087, "lng": 116.4594, "district": "朝阳"},
        "望京": {"lat": 40.0032, "lng": 116.4773, "district": "朝阳"},
        "西二旗": {"lat": 40.0569, "lng": 116.3015, "district": "海淀"},
        "上地": {"lat": 40.0310, "lng": 116.2870, "district": "海淀"},
        "五道口": {"lat": 39.9929, "lng": 116.3370, "district": "海淀"},
        "三里屯": {"lat": 39.9324, "lng": 116.4536, "district": "朝阳"},
        "王府井": {"lat": 39.9139, "lng": 116.4103, "district": "东城"},
        "西单": {"lat": 39.9134, "lng": 116.3728, "district": "西城"},
        "北京南站": {"lat": 39.8654, "lng": 116.3786, "district": "丰台"},
        "北京西站": {"lat": 39.8946, "lng": 116.3220, "district": "丰台"},
    }

    # 北京行政区划
    BEIJING_DISTRICTS: Dict[str, Dict] = {
        "朝阳": {"url": "chaoyang", "lat": 39.9219, "lng": 116.4431},
        "海淀": {"url": "haidian", "lat": 39.9563, "lng": 116.3103},
        "昌平": {"url": "changping", "lat": 40.2206, "lng": 116.2311},
        "丰台": {"url": "fengtai", "lat": 39.8584, "lng": 116.2863},
        "大兴": {"url": "daxing", "lat": 39.7268, "lng": 116.3412},
        "通州": {"url": "tongzhouqu", "lat": 39.9066, "lng": 116.6627},
        "房山": {"url": "fangshan", "lat": 39.7488, "lng": 115.9938},
        "顺义": {"url": "shunyi", "lat": 40.1301, "lng": 116.6545},
        "西城": {"url": "xicheng", "lat": 39.9128, "lng": 116.3662},
        "东城": {"url": "dongcheng", "lat": 39.9289, "lng": 116.4162},
        "石景山": {"url": "shijingshan", "lat": 39.9063, "lng": 116.1954},
    }

    # 区域内详细地点坐标（用于距离估算）
    DISTRICT_LOCATIONS: Dict[str, Tuple[float, float]] = {
        # 海淀区
        "公主坟": (39.9006, 116.3211),
        "马连洼": (40.0289, 116.2822),
        "小西天": (39.9489, 116.3644),
        "花园桥": (39.9378, 116.3433),
        "海淀周边": (40.0300, 116.2500),
        "苏家坨": (40.0889, 116.1511),
        "田村": (39.9389, 116.2211),
        "上庄": (40.1111, 116.1300),
        "永定路": (39.9078, 116.2433),
        "皂君庙": (39.9533, 116.3356),
        "西二旗": (40.0569, 116.3015),
        "北洼路": (39.9311, 116.3033),
        "军博": (39.9089, 116.3256),
        "四季青": (39.9589, 116.2433),
        "清河": (40.0333, 116.3489),
        "西北旺": (40.0444, 116.2733),
        "西三旗": (40.0667, 116.3333),
        "五道口": (39.9929, 116.3370),
        "中关村": (39.9841, 116.3075),
        "上地": (40.0310, 116.2870),
        "安宁庄": (40.0550, 116.3189),
        "回龙观": (40.0711, 116.3150),
        "龙泽": (40.0633, 116.3089),
    }

    @classmethod
    def get_location(cls, name: str) -> Optional[LocationInfo]:
        """获取地点信息

        Args:
            name: 地点名称

        Returns:
            LocationInfo 或 None
        """
        # 精确匹配预设地点
        if name in cls.PRESET_LOCATIONS:
            data = cls.PRESET_LOCATIONS[name]
            return LocationInfo(
                name=name,
                lat=data["lat"],
                lng=data["lng"],
                district=data.get("district"),
            )

        # 模糊匹配预设地点
        for preset_name, data in cls.PRESET_LOCATIONS.items():
            if name in preset_name or preset_name in name:
                return LocationInfo(
                    name=preset_name,
                    lat=data["lat"],
                    lng=data["lng"],
                    district=data.get("district"),
                )

        # 匹配行政区划
        for district_name, info in cls.BEIJING_DISTRICTS.items():
            if district_name in name:
                return LocationInfo(
                    name=district_name,
                    lat=info["lat"],
                    lng=info["lng"],
                    district=district_name,
                )

        return None

    @classmethod
    def get_nearby_districts(
        cls, lat: float, lng: float, radius_km: float
    ) -> List[Dict]:
        """获取附近的行政区划

        Args:
            lat: 纬度
            lng: 经度
            radius_km: 搜索半径

        Returns:
            按距离排序的区域列表
        """
        nearby = []
        for name, info in cls.BEIJING_DISTRICTS.items():
            distance = DistanceCalculator.calculate(lat, lng, info["lat"], info["lng"])
            # 扩大搜索范围以包含边缘区域
            if distance <= radius_km + 15:
                nearby.append(
                    {
                        "name": name,
                        "url": info["url"],
                        "distance": round(distance, 2),
                    }
                )
        return sorted(nearby, key=lambda x: x["distance"])

    @classmethod
    def estimate_coords(cls, location_text: str) -> Optional[Tuple[float, float]]:
        """根据位置文本估算坐标

        Args:
            location_text: 位置描述文本

        Returns:
            (lat, lng) 或 None
        """
        for loc_name, coords in cls.DISTRICT_LOCATIONS.items():
            if loc_name in location_text:
                return coords
        return None

    @classmethod
    def add_preset_location(
        cls, name: str, lat: float, lng: float, district: str = None
    ):
        """添加预设地点

        Args:
            name: 地点名称
            lat: 纬度
            lng: 经度
            district: 所属行政区
        """
        cls.PRESET_LOCATIONS[name] = {
            "lat": lat,
            "lng": lng,
            "district": district,
        }
