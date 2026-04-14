"""Search parameters data model."""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SearchParams:
    """搜索参数数据类

    Attributes:
        location: 目标地点名称
        radius_km: 搜索半径(公里)
        days: 发布时间限制(天)
        price_min: 最低租金
        price_max: 最高租金
        area_min: 最小面积(平方米)
        area_max: 最大面积(平方米)
        rooms: 户型 (1=一居, 2=两居, 3=三居)
        rental_type: 租赁方式 ("整租" 或 "合租")
        city: 城市名称
        city_code: 城市代码
    """

    location: str
    radius_km: float = 5.0
    days: int = 15
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    rooms: Optional[int] = None
    rental_type: Optional[str] = None
    city: str = "北京"
    city_code: str = "bj"

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    def __str__(self) -> str:
        parts = [f"地点: {self.location}"]
        if self.radius_km:
            parts.append(f"距离: {self.radius_km}km")
        if self.days:
            parts.append(f"时间: {self.days}天内")
        if self.price_min or self.price_max:
            if self.price_min and self.price_max:
                parts.append(f"价格: {self.price_min}-{self.price_max}元")
            elif self.price_max:
                parts.append(f"价格: {self.price_max}元以内")
            else:
                parts.append(f"价格: {self.price_min}元以上")
        if self.area_min or self.area_max:
            if self.area_min and self.area_max:
                parts.append(f"面积: {self.area_min}-{self.area_max}㎡")
            elif self.area_max:
                parts.append(f"面积: {self.area_max}㎡以内")
        if self.rooms:
            room_names = {1: "一居", 2: "两居", 3: "三居"}
            parts.append(f"户型: {room_names.get(self.rooms, f'{self.rooms}居')}")
        if self.rental_type:
            parts.append(f"类型: {self.rental_type}")
        return ", ".join(parts)
