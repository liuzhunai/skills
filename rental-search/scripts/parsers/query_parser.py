"""Query parser with Chain of Responsibility pattern."""

import re
from typing import Dict, Optional

from .base import ParserHandler


class DistanceParser(ParserHandler):
    """距离解析器"""

    def _do_parse(self, query: str, params: dict) -> dict:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(km|公里|米|m)", query)
        if match:
            value = float(match.group(1))
            unit = match.group(2).lower()
            params["radius_km"] = value if unit in ["km", "公里"] else value / 1000
        return params

    def get_pattern(self) -> str:
        return "距离: 5km, 3公里, 500米"


class TimeParser(ParserHandler):
    """时间解析器"""

    def _do_parse(self, query: str, params: dict) -> dict:
        match = re.search(r"(\d+)\s*天", query)
        if match:
            params["days"] = int(match.group(1))
        return params

    def get_pattern(self) -> str:
        return "时间: 15天, 30天内"


class PriceParser(ParserHandler):
    """价格解析器"""

    def _do_parse(self, query: str, params: dict) -> dict:
        # 区间价格: 价格3000-5000
        match = re.search(r"价格?(\d+)-(\d+)", query)
        if match:
            params["price_min"] = int(match.group(1))
            params["price_max"] = int(match.group(2))
            return params

        # 上限价格: 3000以内
        match = re.search(r"(\d+)以[内下]", query)
        if match:
            params["price_max"] = int(match.group(1))

        return params

    def get_pattern(self) -> str:
        return "价格: 3000-5000, 2000以内"


class AreaParser(ParserHandler):
    """面积解析器"""

    def _do_parse(self, query: str, params: dict) -> dict:
        # 区间面积: 面积30-50, 30-50平
        match = re.search(r"面积?(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*(?:平|平米)?", query)
        if match:
            params["area_min"] = float(match.group(1))
            params["area_max"] = float(match.group(2))
            return params

        # 上限面积: 50平以内
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:平|平米)\s*以[内下]", query)
        if match:
            params["area_max"] = float(match.group(1))

        return params

    def get_pattern(self) -> str:
        return "面积: 30-50平, 50平以内"


class RoomParser(ParserHandler):
    """户型解析器"""

    ROOM_PATTERNS = {
        1: ["一居", "一室", "开间"],
        2: ["两居", "两室", "二居", "二室"],
        3: ["三居", "三室"],
    }

    def _do_parse(self, query: str, params: dict) -> dict:
        for rooms, patterns in self.ROOM_PATTERNS.items():
            if any(p in query for p in patterns):
                params["rooms"] = rooms
                break
        return params

    def get_pattern(self) -> str:
        return "户型: 一居, 两居, 三居, 开间"


class RentalTypeParser(ParserHandler):
    """租赁方式解析器"""

    def _do_parse(self, query: str, params: dict) -> dict:
        if "整租" in query:
            params["rental_type"] = "整租"
        elif "合租" in query:
            params["rental_type"] = "合租"
        return params

    def get_pattern(self) -> str:
        return "类型: 整租, 合租"


class LocationParser(ParserHandler):
    """地点解析器 (责任链末端)"""

    # 需要移除的关键词
    REMOVE_PATTERNS = [
        r"(\d+(?:\.\d+)?)\s*(km|公里|米|m)",
        r"(\d+)\s*天[内以]?",
        r"价格?(\d+)-(\d+)",
        r"(\d+)以[内下]",
        r"面积?(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*(?:平|平米)?",
        r"(\d+(?:\.\d+)?)\s*(?:平|平米)\s*以[内下]",
        r"(一居|两居|三居|一室|两室|三室|开间|整租|合租)",
        r"(附近|周边|的|房源|租房|房子|个人)",
    ]

    def _do_parse(self, query: str, params: dict) -> dict:
        location = query
        for pattern in self.REMOVE_PATTERNS:
            location = re.sub(pattern, "", location)
        params["location"] = location.strip()
        return params

    def get_pattern(self) -> str:
        return "地点: 剩余文本作为地点名称"


class QueryParser:
    """查询解析器

    使用责任链模式组合多个解析器。
    """

    def __init__(self):
        # 构建责任链
        self._chain = self._build_chain()

    def _build_chain(self) -> ParserHandler:
        """构建解析器责任链"""
        distance = DistanceParser()
        time = TimeParser()
        price = PriceParser()
        area = AreaParser()
        room = RoomParser()
        rental_type = RentalTypeParser()
        location = LocationParser()

        # 设置责任链顺序
        distance.set_next(time)
        time.set_next(price)
        price.set_next(area)
        area.set_next(room)
        room.set_next(rental_type)
        rental_type.set_next(location)

        return distance

    def parse(self, query: str) -> Dict:
        """解析查询字符串

        Args:
            query: 用户输入的查询字符串

        Returns:
            解析后的参数字典
        """
        default_params = {
            "location": "",
            "radius_km": 5.0,
            "days": 15,
            "price_min": None,
            "price_max": None,
            "area_min": None,
            "area_max": None,
            "rooms": None,
            "rental_type": None,
        }
        return self._chain.parse(query, default_params)

    def get_supported_patterns(self) -> Dict[str, str]:
        """获取支持的解析模式"""
        patterns = {}
        handler = self._chain
        while handler:
            patterns[handler.__class__.__name__] = handler.get_pattern()
            handler = handler._next_handler
        return patterns
