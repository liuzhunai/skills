#!/usr/bin/env python3
"""
租房搜索 - 主入口

整合所有模块，提供完整的搜索流程。

设计模式:
- 责任链模式: 查询参数解析
- 策略模式: 平台适配器
- 工厂模式: 平台创建
- 单例模式: 配置管理
- 建造者模式: URL构建

模块结构:
    scripts/
    ├── __init__.py          # 包入口
    ├── main.py              # 主程序入口
    ├── config.py            # 配置管理(单例)
    ├── models/
    │   ├── params.py        # 搜索参数模型
    │   └── listing.py       # 房源模型
    ├── parsers/
    │   ├── base.py          # 解析器基类
    │   └── query_parser.py  # 查询解析器(责任链)
    ├── platforms/
    │   ├── base.py          # 平台适配器基类(策略)
    │   ├── wuba.py          # 58同城实现
    │   └── factory.py       # 平台工厂
    ├── geo/
    │   ├── distance.py      # 距离计算
    │   ├── location.py      # 地点服务
    │   └── subway.py        # 地铁站服务
    └── exporters/
        ├── base.py          # 导出器基类
        └── excel_exporter.py # Excel导出
"""

import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional

from models import SearchParams, Listing
from parsers import QueryParser
from platforms import PlatformFactory, PlatformAdapter
from exporters import ExcelExporter
from config import ConfigManager
from geo import LocationService, DistanceCalculator, SubwayService


class RentalSearchEngine:
    """租房搜索引擎

    整合所有模块，提供完整的搜索流程。
    """

    def __init__(self, platform: str = None):
        """初始化搜索引擎

        Args:
            platform: 平台名称，默认使用配置中的平台
        """
        self.config = ConfigManager.get_config()
        self.parser = QueryParser()
        self.platform = PlatformFactory.create(platform)
        self.exporter = ExcelExporter()

    def search(self, query: str, output_path: str = None) -> Dict:
        """执行搜索

        Args:
            query: 查询字符串
            output_path: 输出路径

        Returns:
            搜索结果字典
        """
        # 1. 解析查询
        params = self._parse_query(query)
        print(f"解析结果: {params}")

        # 2. 获取地点坐标
        location_info = self._get_location(params["location"])
        if not location_info:
            print(f"警告: 未找到地点 '{params['location']}'，使用默认坐标")
            location_info = {"lat": 39.9042, "lng": 116.4074, "district": "东城"}

        print(
            f"目标地点: {params['location']} ({location_info['lat']}, {location_info['lng']})"
        )

        # 3. 获取附近区域
        districts = LocationService.get_nearby_districts(
            location_info["lat"],
            location_info["lng"],
            params["radius_km"],
        )
        print(f"相关区域: {[d['name'] for d in districts[:5]]}")

        # 4. 构建搜索参数
        search_params = self._build_search_params(params)

        # 5. 构建搜索URL
        search_urls = self.platform.build_search_urls(search_params, districts)
        print(f"搜索URL: {search_urls[0].url}")

        # 6. 返回配置信息
        result = {
            "params": params,
            "location": location_info,
            "districts": districts,
            "search_urls": [vars(url) for url in search_urls],
            "created_at": datetime.now().isoformat(),
        }

        return result

    def _parse_query(self, query: str) -> dict:
        """解析查询字符串"""
        return self.parser.parse(query)

    def _get_location(self, name: str) -> Optional[Dict]:
        """获取地点坐标"""
        info = LocationService.get_location(name)
        if info:
            return {
                "lat": info.lat,
                "lng": info.lng,
                "district": info.district,
            }
        return None

    def _build_search_params(self, params: dict) -> SearchParams:
        """构建搜索参数对象"""
        return SearchParams(
            location=params.get("location", ""),
            radius_km=params.get("radius_km", self.config.default_radius_km),
            days=params.get("days", self.config.default_days),
            price_min=params.get("price_min"),
            price_max=params.get("price_max"),
            area_min=params.get("area_min"),
            area_max=params.get("area_max"),
            rooms=params.get("rooms"),
            rental_type=params.get("rental_type"),
            city=self.config.default_city,
            city_code=self.config.default_city_code,
        )

    def filter_listings(
        self,
        raw_listings: List[Dict],
        target_lat: float,
        target_lng: float,
        radius_km: float,
        area_min: float = None,
        area_max: float = None,
    ) -> List[Listing]:
        """过滤房源

        Args:
            raw_listings: 原始房源列表
            target_lat: 目标纬度
            target_lng: 目标经度
            radius_km: 搜索半径
            area_min: 最小面积
            area_max: 最大面积

        Returns:
            过滤后的房源列表
        """
        filtered = []

        for data in raw_listings:
            location_text = data.get("location", "")
            coords = LocationService.estimate_coords(location_text)

            if coords:
                distance = DistanceCalculator.calculate(
                    target_lat, target_lng, coords[0], coords[1]
                )

                if distance <= radius_km:
                    # 面积过滤
                    area = data.get("area")
                    if area:
                        if area_min and area < area_min:
                            continue
                        if area_max and area > area_max:
                            continue

                    # 查找最近地铁站
                    nearest_subway = SubwayService.find_nearest(
                        coords[0], coords[1], self.config.subway_max_distance_km
                    )

                    # 创建Listing对象
                    listing = Listing(
                        title=data.get("title", ""),
                        price=data.get("price"),
                        area=area,
                        location=location_text,
                        community=data.get("community", ""),
                        rooms=data.get("rooms", 1),
                        rental_type=data.get("rental_type", "整租"),
                        distance=round(distance, 2),
                        nearest_subway=nearest_subway,
                        publish_time=data.get("publish_time"),
                        url=data.get("url", ""),
                        image_url=data.get("image_url", ""),
                        raw_data=data,
                    )
                    filtered.append(listing)

        # 按距离排序
        return sorted(filtered, key=lambda x: x.distance or 0)

    def export_to_excel(
        self,
        listings: List[Listing],
        output_path: str = None,
        location_name: str = "房源",
    ) -> str:
        """导出到Excel

        Args:
            listings: 房源列表
            output_path: 输出路径
            location_name: 地点名称

        Returns:
            输出文件路径
        """
        return self.exporter.export(listings, output_path, location_name)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="租房搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py "百度科技园附近5km的房源"
  python main.py "中关村附近3km 30天内"
  python main.py "国贸附近 价格3000-5000的整租"
  python main.py "望京附近2km 一居室"
  python main.py "西二旗附近 面积30-50平的合租"
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="中关村附近5km的房源",
        help="搜索关键词",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出Excel文件路径",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出JSON格式",
    )
    parser.add_argument(
        "--platform",
        "-p",
        default=None,
        choices=["wuba", "58"],
        help="房源平台",
    )
    parser.add_argument(
        "--city",
        "-c",
        default=None,
        help="设置默认城市",
    )

    args = parser.parse_args()

    # 设置城市
    if args.city:
        ConfigManager.set_city(args.city)

    # 创建搜索引擎
    engine = RentalSearchEngine(platform=args.platform)

    # 执行搜索
    result = engine.search(args.query, args.output)

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        with open("search_config.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n配置已保存到: search_config.json")

    print(f"\n下一步: 使用 dumate-browser-use 访问搜索URL并提取房源数据")


if __name__ == "__main__":
    main()
