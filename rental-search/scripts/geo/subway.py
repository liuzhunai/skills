"""Subway station service."""

from typing import Dict, Optional, Tuple

from .distance import DistanceCalculator


class SubwayService:
    """地铁站服务

    提供地铁站坐标查询和最近站点查找功能。
    """

    # 北京地铁站坐标
    BEIJING_SUBWAY_STATIONS: Dict[str, Tuple[float, float]] = {
        # 13号线
        "西二旗": (40.0569, 116.3015),
        "上地": (40.0310, 116.2870),
        "五道口": (39.9929, 116.3370),
        "知春路": (39.9756, 116.3394),
        "芍药居": (39.9672, 116.4283),
        "望京西": (40.0022, 116.4194),
        "东直门": (39.9444, 116.4344),
        # 昌平线
        "昌平": (40.2161, 116.2311),
        "沙河": (40.1489, 116.2911),
        "生命科学园": (40.0889, 116.2911),
        # 16号线
        "西北旺": (40.0444, 116.2733),
        "马连洼": (40.0289, 116.2822),
        "西苑": (40.0061, 116.2839),
        # 4号线
        "中关村": (39.9841, 116.3075),
        "海淀黄庄": (39.9806, 116.3125),
        "人民大学": (39.9656, 116.3228),
        "魏公村": (39.9533, 116.3267),
        "国家图书馆": (39.9333, 116.3194),
        # 10号线
        "苏州街": (39.9711, 116.3061),
        "巴沟": (39.9644, 116.2894),
        "慈寿寺": (39.9489, 116.2794),
        # 1号线
        "五棵松": (39.9089, 116.2567),
        "万寿路": (39.9061, 116.2739),
        "公主坟": (39.9006, 116.3211),
        "军事博物馆": (39.9089, 116.3256),
        # 6号线
        "海淀五路居": (39.9267, 116.2639),
        "花园桥": (39.9378, 116.3433),
        # 8号线
        "永泰庄": (40.0239, 116.3489),
        "西小口": (40.0361, 116.3511),
        "育新": (40.0489, 116.3511),
        # 其他
        "回龙观": (40.0711, 116.3150),
        "龙泽": (40.0633, 116.3089),
        "霍营": (40.0711, 116.3711),
    }

    @classmethod
    def find_nearest(
        cls, lat: float, lng: float, max_distance_km: float = 3.0
    ) -> Optional[str]:
        """查找最近的地铁站

        Args:
            lat: 纬度
            lng: 经度
            max_distance_km: 最大距离限制(公里)

        Returns:
            格式化的地铁站信息，如 "西二旗 (800m)" 或 None
        """
        name, distance = DistanceCalculator.find_nearest(
            (lat, lng),
            cls.BEIJING_SUBWAY_STATIONS,
            max_distance_km,
        )

        if name and distance is not None:
            return f"{name} ({int(distance * 1000)}m)"

        return None

    @classmethod
    def get_station_coords(cls, name: str) -> Optional[Tuple[float, float]]:
        """获取地铁站坐标

        Args:
            name: 站名

        Returns:
            (lat, lng) 或 None
        """
        return cls.BEIJING_SUBWAY_STATIONS.get(name)

    @classmethod
    def add_station(cls, name: str, lat: float, lng: float):
        """添加地铁站

        Args:
            name: 站名
            lat: 纬度
            lng: 经度
        """
        cls.BEIJING_SUBWAY_STATIONS[name] = (lat, lng)

    @classmethod
    def list_stations(cls) -> list:
        """列出所有地铁站"""
        return list(cls.BEIJING_SUBWAY_STATIONS.keys())
