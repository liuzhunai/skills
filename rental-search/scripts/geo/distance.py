"""Distance calculation utilities."""

import math
from typing import Tuple


class DistanceCalculator:
    """距离计算器

    使用 Haversine 公式计算两点之间的球面距离。
    """

    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def calculate(cls, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点之间的距离(公里)

        Args:
            lat1: 点1纬度
            lng1: 点1经度
            lat2: 点2纬度
            lng2: 点2经度

        Returns:
            两点之间的距离(公里)
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )

        return cls.EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def is_within_radius(
        cls, center: Tuple[float, float], point: Tuple[float, float], radius_km: float
    ) -> bool:
        """判断点是否在半径范围内

        Args:
            center: 中心点坐标 (lat, lng)
            point: 目标点坐标 (lat, lng)
            radius_km: 半径(公里)

        Returns:
            是否在范围内
        """
        distance = cls.calculate(center[0], center[1], point[0], point[1])
        return distance <= radius_km

    @classmethod
    def find_nearest(
        cls, center: Tuple[float, float], points: dict, max_distance_km: float = None
    ) -> Tuple[str, float]:
        """查找最近的点

        Args:
            center: 中心点坐标 (lat, lng)
            points: 点字典 {name: (lat, lng)}
            max_distance_km: 最大距离限制

        Returns:
            (最近点名称, 距离) 或 (None, None)
        """
        nearest_name = None
        min_distance = float("inf")

        for name, coords in points.items():
            distance = cls.calculate(center[0], center[1], coords[0], coords[1])
            if distance < min_distance:
                min_distance = distance
                nearest_name = name

        if max_distance_km and min_distance > max_distance_km:
            return None, None

        return nearest_name, min_distance
