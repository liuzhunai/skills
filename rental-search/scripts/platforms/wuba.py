"""58同城平台 adapter."""

import re
from typing import List, Dict, Optional

from .base import PlatformAdapter, SearchURL
from ..models.params import SearchParams


class WubaAdapter(PlatformAdapter):
    """58同城平台适配器

    支持搜索58同城个人房源。
    """

    NAME = "wuba"
    DISPLAY_NAME = "58同城"

    # 房源类型：0=个人房源，1=经纪人房源
    # 本适配器只搜索个人房源
    PERSONAL_LISTING = "0"
    AGENT_LISTING = "1"

    # 价格区间映射
    PRICE_MAPPING = {
        (0, 1000): 9,
        (1000, 1500): 10,
        (1500, 2000): 11,
        (2000, 3000): 12,
        (3000, 5000): 13,
        (5000, 8000): 14,
        (8000, float("inf")): 15,
    }

    def build_search_urls(
        self, params: SearchParams, districts: List[Dict]
    ) -> List[SearchURL]:
        """构建58同城搜索URL

        URL格式: https://{city}.58.com/{district}/{path}/0/{filters}/
        - /0/ 表示个人房源
        - /zufang/ 整租
        - /hezu/ 合租
        - /j{n}/ 户型
        - /b{n}/ 价格区间
        """
        urls = []

        for district in districts[:3]:  # 限制搜索区域数量
            url = self._build_single_url(params, district["url"])
            urls.append(
                SearchURL(
                    url=url,
                    district=district["name"],
                    distance=district["distance"],
                    platform=self.NAME,
                )
            )

        return urls

    def _build_single_url(self, params: SearchParams, district_url: str) -> str:
        """构建单个搜索URL

        注意：/0/ 表示个人房源，/1/ 表示经纪人房源
        本方法固定使用 /0/，确保只搜索个人房源
        """
        # 根据租赁方式选择路径
        path = "hezu" if params.rental_type == "合租" else "zufang"

        # 基础URL - /0/ 表示个人房源
        url = f"https://{params.city_code}.58.com/{district_url}/{path}/{self.PERSONAL_LISTING}/"

        # 添加户型过滤
        if params.rooms:
            url = url.rstrip("/") + f"/j{params.rooms}/"

        # 添加价格过滤
        price_code = self._get_price_code(params.price_max)
        if price_code:
            url = url.rstrip("/") + f"/b{price_code}/"

        return url

    def _get_price_code(self, price_max: Optional[int]) -> Optional[int]:
        """获取价格区间代码"""
        if not price_max:
            return None

        for (low, high), code in self.PRICE_MAPPING.items():
            if price_max <= high:
                return code
        return None

    def parse_list_page(self, html: str) -> List[Dict]:
        """解析58同城列表页

        使用正则表达式提取房源信息。
        """
        listings = []

        # 简化的解析逻辑，实际使用时需要配合浏览器自动化
        # 这里提供数据结构的模板
        pattern = r'<li[^>]*class="[^"]*house-cell[^"]*"[^>]*>(.*?)</li>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches:
            listing = self._parse_listing_item(match)
            if listing:
                listings.append(listing)

        return listings

    def _parse_listing_item(self, html: str) -> Optional[Dict]:
        """解析单个房源项"""
        # 提取标题
        title_match = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # 提取链接
        link_match = re.search(r'href="([^"]*58\.com[^"]*)"', html)
        url = link_match.group(1) if link_match else ""

        # 提取价格
        price_match = re.search(r"(\d+)\s*元/月", html)
        price = int(price_match.group(1)) if price_match else None

        # 提取面积
        area_match = re.search(r"(\d+(?:\.\d+)?)\s*[平㎡]", html)
        area = float(area_match.group(1)) if area_match else None

        if not title:
            return None

        return {
            "title": title,
            "url": url,
            "price": price,
            "area": area,
            "platform": self.NAME,
        }

    def parse_detail_page(self, html: str, url: str) -> Dict:
        """解析58同城详情页"""
        # 提取详细信息
        data = {"url": url, "platform": self.NAME}

        # 提取小区名称
        community_match = re.search(r"小区[名称：:]*([^<\n]+)", html)
        if community_match:
            data["community"] = community_match.group(1).strip()

        # 提取位置
        location_match = re.search(r"位置[：:]*([^<\n]+)", html)
        if location_match:
            data["location"] = location_match.group(1).strip()

        # 提取发布时间
        time_match = re.search(r"(\d+天前|\d+小时前|今天|昨天)", html)
        if time_match:
            data["publish_time"] = time_match.group(1)

        # 提取图片
        img_match = re.search(r'data-src="(https?://[^"]+\.(jpg|png|jpeg))"', html)
        if img_match:
            data["image_url"] = img_match.group(1)

        return data

    def supports_rental_type(self, rental_type: Optional[str]) -> bool:
        """58同城支持整租和合租"""
        return rental_type in [None, "整租", "合租"]

    @classmethod
    def get_javascript_extractor(cls) -> str:
        """获取用于浏览器自动化的JavaScript提取代码

        过滤规则：
        1. 排除包含"经纪人"、"中介"、"代理"等关键词的房源
        2. 排除带有经纪人标识的房源（如 class 包含 agent）
        3. 只保留个人房源
        """
        return """
        Array.from(document.querySelectorAll("li")).filter(li => {
            const h2 = li.querySelector("h2");
            if (!h2) return false;
            
            const title = h2.textContent.trim();
            
            // 必须包含整租或合租
            if (!title.includes("整租") && !title.includes("合租")) return false;
            
            // 排除经纪人房源关键词
            const text = li.innerText;
            const agentKeywords = ["经纪人", "中介", "代理", "房产经纪", "置业顾问"];
            if (agentKeywords.some(kw => text.includes(kw))) return false;
            
            // 排除带有经纪人标识的元素
            const agentTag = li.querySelector(".agent, .broker, [class*='agent'], [class*='broker']");
            if (agentTag) return false;
            
            return true;
        }).map(li => {
            const h2 = li.querySelector("h2");
            const title = h2 ? h2.textContent.trim() : "";
            const link = h2 ? h2.querySelector("a") : null;
            const url = link ? link.href : "";
            const allText = li.innerText.split("\\n");
            const priceLine = allText.find(t => t.includes("元/月"));
            const price = priceLine ? parseInt(priceLine) : null;
            const areaLine = allText.find(t => t.includes("㎡") || t.includes("平"));
            const area = areaLine ? parseFloat(areaLine) : null;
            const img = li.querySelector("img");
            const imageUrl = img ? (img.src || img.dataset.src) : "";
            
            // 提取租赁类型
            const rentalType = title.includes("合租") ? "合租" : "整租";
            
            // 提取小区名称（通常在标题中）
            const communityMatch = title.match(/(?:整租|合租)\\s*[-·]?\\s*(.+?)\\s*\\d室/);
            const community = communityMatch ? communityMatch[1].trim() : "";
            
            return {
                title: title,
                url: url,
                price: price,
                area: area,
                image_url: imageUrl,
                rental_type: rentalType,
                community: community,
                platform: "wuba",
                is_personal: true  // 标记为个人房源
            };
        });
        """
