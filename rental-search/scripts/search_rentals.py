#!/usr/bin/env python3
"""
58同城租房搜索脚本
根据地点关键词搜索周边个人房源
"""

import re
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
import math

# 百度地图API配置
BAIDU_MAP_AK = None  # 需要配置


def parse_query(query: str) -> Dict:
    """
    解析用户输入的查询

    示例输入:
    - "百度科技园附近5km的房源"
    - "中关村附近3km 15天内"
    - "国贸附近 个人房源 价格3000-5000"
    """
    result = {
        "location": None,
        "radius_km": 5.0,
        "days": 15,
        "source_type": "personal",  # personal/agent/all
        "price_min": None,
        "price_max": None,
        "city": "北京",
        "city_code": "bj",
    }

    # 提取距离 (支持 km/m)
    radius_match = re.search(r"(\d+(?:\.\d+)?)\s*(km|公里|米|m)", query)
    if radius_match:
        value = float(radius_match.group(1))
        unit = radius_match.group(2).lower()
        if unit in ["km", "公里"]:
            result["radius_km"] = value
        elif unit in ["m", "米"]:
            result["radius_km"] = value / 1000

    # 提取时间限制
    days_match = re.search(r"(\d+)\s*天", query)
    if days_match:
        result["days"] = int(days_match.group(1))

    # 提取价格区间
    price_match = re.search(r"价格?(\d+)-(\d+)", query)
    if price_match:
        result["price_min"] = int(price_match.group(1))
        result["price_max"] = int(price_match.group(2))
    else:
        # 尝试匹配单个价格上限
        price_max_match = re.search(r"(\d+)以[内下]", query)
        if price_max_match:
            result["price_max"] = int(price_max_match.group(1))

    # 提取房源类型
    if "经纪人" in query or "中介" in query:
        result["source_type"] = "agent"
    elif "个人" in query:
        result["source_type"] = "personal"

    # 提取地点关键词（移除其他参数后的剩余部分）
    location_query = query
    # 移除距离
    location_query = re.sub(r"(\d+(?:\.\d+)?)\s*(km|公里|米|m)", "", location_query)
    # 移除时间
    location_query = re.sub(r"(\d+)\s*天[内以]?", "", location_query)
    # 移除价格
    location_query = re.sub(r"价格?(\d+)-(\d+)", "", location_query)
    location_query = re.sub(r"(\d+)以[内下]", "", location_query)
    # 移除房源类型
    location_query = re.sub(r"(个人|经纪人|中介)房源?", "", location_query)
    # 移除通用词
    location_query = re.sub(r"(附近|周边|的|房源|租房|房子)", "", location_query)

    result["location"] = location_query.strip()

    return result


def get_location_info(location: str, city: str = "北京") -> Optional[Dict]:
    """
    使用百度地图API获取地点信息
    返回: {lat, lng, name, district}
    """
    if not BAIDU_MAP_AK:
        # 如果没有配置API Key，返回模拟数据
        print(f"警告: 未配置百度地图API Key，使用默认坐标")
        return {
            "lat": 39.984120,
            "lng": 116.307484,
            "name": location,
            "district": "海淀区",
        }

    url = "http://api.map.baidu.com/geocoding/v3/"
    params = {
        "address": f"{city}{location}",
        "city": city,
        "output": "json",
        "ak": BAIDU_MAP_AK,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == 0:
            result = data["result"]
            return {
                "lat": result["location"]["lat"],
                "lng": result["location"]["lng"],
                "name": result.get("level", location),
                "district": result.get("district", ""),
            }
    except Exception as e:
        print(f"获取地点信息失败: {e}")

    return None


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算两点之间的距离（km）
    使用Haversine公式
    """
    R = 6371  # 地球半径(km)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_58_districts(city_code: str = "bj") -> List[Dict]:
    """
    获取58同城的区域列表
    """
    # 北京区域列表（58同城URL格式）
    districts = [
        {"name": "朝阳", "url": "chaoyang"},
        {"name": "海淀", "url": "haidian"},
        {"name": "昌平", "url": "changping"},
        {"name": "丰台", "url": "fengtai"},
        {"name": "大兴", "url": "daxing"},
        {"name": "通州", "url": "tongzhouqu"},
        {"name": "房山", "url": "fangshan"},
        {"name": "顺义", "url": "shunyi"},
        {"name": "西城", "url": "xicheng"},
        {"name": "东城", "url": "dongcheng"},
        {"name": "密云", "url": "miyun"},
        {"name": "石景山", "url": "shijingshan"},
        {"name": "怀柔", "url": "huairou"},
        {"name": "门头沟", "url": "mentougou"},
        {"name": "延庆", "url": "yanqing"},
        {"name": "平谷", "url": "pinggu"},
    ]
    return districts


def get_district_center(district_name: str, city: str = "北京") -> Tuple[float, float]:
    """
    获取区域中心坐标（简化版本，使用预设数据）
    """
    # 北京各区中心坐标（简化数据）
    district_coords = {
        "朝阳": (39.9219, 116.4431),
        "海淀": (39.9563, 116.3103),
        "昌平": (40.2206, 116.2311),
        "丰台": (39.8584, 116.2863),
        "大兴": (39.7268, 116.3412),
        "通州": (39.9066, 116.6627),
        "房山": (39.7488, 115.9938),
        "顺义": (40.1301, 116.6545),
        "西城": (39.9128, 116.3662),
        "东城": (39.9289, 116.4162),
        "密云": (40.3769, 116.8432),
        "石景山": (39.9063, 116.1954),
        "怀柔": (40.3163, 116.6420),
        "门头沟": (39.9407, 116.1021),
        "延庆": (40.4654, 115.9750),
        "平谷": (40.1446, 117.1110),
    }
    return district_coords.get(district_name, (39.9042, 116.4074))


def build_58_url(
    city_code: str,
    district: str,
    source_type: str = "personal",
    price_min: int = None,
    price_max: int = None,
    page: int = 1,
) -> str:
    """
    构建58同城搜索URL

    URL格式说明:
    - 个人房源: /chuzu/0/
    - 经纪人房源: /chuzu/1/
    - 价格区间: /b{n}/ (n为价格代码)
    - 分页: /pn{n}/
    """
    base_url = f"https://{city_code}.58.com"

    # 房源类型
    source_code = "0" if source_type == "personal" else "1"

    # 构建URL路径
    if district:
        path = f"/{district}/chuzu/{source_code}/"
    else:
        path = f"/chuzu/{source_code}/"

    # 价格过滤
    if price_min or price_max:
        # 58同城价格代码映射
        price_code = get_price_code(price_min, price_max)
        if price_code:
            path = path.rstrip("/") + f"/b{price_code}/"

    # 分页
    if page > 1:
        path = path.rstrip("/") + f"/pn{page}/"

    return base_url + path


def get_price_code(price_min: int = None, price_max: int = None) -> Optional[int]:
    """
    将价格区间转换为58同城价格代码

    价格代码对照:
    b9: 600-1000元
    b10: 1000-1500元
    b11: 1500-2000元
    b12: 2000-3000元
    b13: 3000-5000元
    b14: 5000-8000元
    b15: 8000元以上
    """
    price_ranges = [
        (600, 1000, 9),
        (1000, 1500, 10),
        (1500, 2000, 11),
        (2000, 3000, 12),
        (3000, 5000, 13),
        (5000, 8000, 14),
        (8000, 999999, 15),
    ]

    if price_max and price_max <= 1000:
        return 9
    elif price_max and price_max <= 1500:
        return 10
    elif price_max and price_max <= 2000:
        return 11
    elif price_max and price_max <= 3000:
        return 12
    elif price_max and price_max <= 5000:
        return 13
    elif price_max and price_max <= 8000:
        return 14
    elif price_max:
        return 15

    return None


def parse_publish_time(time_str: str) -> Optional[datetime]:
    """
    解析发布时间
    """
    now = datetime.now()

    if "今天" in time_str:
        return now.replace(hour=0, minute=0, second=0)
    elif "昨天" in time_str:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    elif "前天" in time_str:
        return (now - timedelta(days=2)).replace(hour=0, minute=0, second=0)
    elif "小时" in time_str:
        hours = int(re.search(r"(\d+)", time_str).group(1))
        return now - timedelta(hours=hours)
    elif "分钟" in time_str:
        minutes = int(re.search(r"(\d+)", time_str).group(1))
        return now - timedelta(minutes=minutes)
    elif "天前" in time_str:
        days = int(re.search(r"(\d+)", time_str).group(1))
        return now - timedelta(days=days)
    else:
        # 尝试解析具体日期 (如 "4月10日")
        date_match = re.search(r"(\d+)月(\d+)日?", time_str)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year = now.year
            if month > now.month:
                year -= 1
            return datetime(year, month, day)

    return None


def main():
    parser = argparse.ArgumentParser(description="58同城租房搜索")
    parser.add_argument("query", help='搜索关键词，如"百度科技园附近5km的房源"')
    parser.add_argument("--radius", type=float, default=5.0, help="搜索半径(km)")
    parser.add_argument("--days", type=int, default=15, help="房源发布时间限制(天)")
    parser.add_argument("--city", default="北京", help="城市")
    parser.add_argument("--output", default="rentals.json", help="输出文件")

    args = parser.parse_args()

    # 解析查询
    params = parse_query(args.query)
    params["radius_km"] = args.radius
    params["days"] = args.days
    params["city"] = args.city

    print(f"搜索参数: {json.dumps(params, ensure_ascii=False, indent=2)}")

    # 获取地点坐标
    location_info = get_location_info(params["location"], params["city"])
    if not location_info:
        print(f"无法找到地点: {params['location']}")
        return

    print(
        f"目标地点: {location_info['name']} ({location_info['lat']}, {location_info['lng']})"
    )

    # 获取相关区域
    districts = get_58_districts(params["city_code"])
    nearby_districts = []

    for district in districts:
        district_center = get_district_center(district["name"])
        distance = calculate_distance(
            location_info["lat"],
            location_info["lng"],
            district_center[0],
            district_center[1],
        )
        if distance <= params["radius_km"] + 10:  # 多搜索一些区域
            district["distance"] = distance
            nearby_districts.append(district)

    nearby_districts.sort(key=lambda x: x["distance"])
    print(f"相关区域: {[d['name'] for d in nearby_districts]}")

    # 这里需要配合浏览器自动化来实际抓取数据
    # 返回搜索配置供后续处理
    search_config = {
        "params": params,
        "location": location_info,
        "districts": nearby_districts,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(search_config, f, ensure_ascii=False, indent=2)

    print(f"搜索配置已保存到: {args.output}")


if __name__ == "__main__":
    main()
