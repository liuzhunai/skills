"""Listing data model."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Listing:
    """房源数据类

    Attributes:
        title: 房源标题
        price: 租金(元/月)
        area: 面积(平方米)
        location: 位置描述
        community: 小区名称
        rooms: 房间数
        rental_type: 租赁类型(整租/合租)
        distance: 距目标点距离(km)
        nearest_subway: 最近地铁站
        publish_time: 发布时间
        url: 房源链接
        image_url: 图片链接
        image_path: 本地图片路径
    """

    title: str
    price: Optional[int] = None
    area: Optional[float] = None
    location: str = ""
    community: str = ""
    rooms: int = 1
    rental_type: str = "整租"
    distance: Optional[float] = None
    nearest_subway: Optional[str] = None
    publish_time: Optional[str] = None
    url: str = ""
    image_url: str = ""
    image_path: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "price": self.price,
            "area": self.area,
            "location": self.location,
            "community": self.community,
            "rooms": self.rooms,
            "rental_type": self.rental_type,
            "distance": self.distance,
            "nearest_subway": self.nearest_subway,
            "publish_time": self.publish_time,
            "url": self.url,
            "image_url": self.image_url,
            "image_path": self.image_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        """从字典创建实例"""
        return cls(
            title=data.get("title", ""),
            price=data.get("price"),
            area=data.get("area"),
            location=data.get("location", ""),
            community=data.get("community", ""),
            rooms=data.get("rooms", 1),
            rental_type=data.get("rental_type", "整租"),
            distance=data.get("distance"),
            nearest_subway=data.get("nearest_subway"),
            publish_time=data.get("publish_time"),
            url=data.get("url", ""),
            image_url=data.get("image_url", ""),
            image_path=data.get("image_path", ""),
            raw_data=data,
        )

    def __str__(self) -> str:
        parts = [self.title]
        if self.price:
            parts.append(f"{self.price}元/月")
        if self.area:
            parts.append(f"{self.area}㎡")
        if self.distance is not None:
            parts.append(f"距离{self.distance}km")
        return " | ".join(parts)
