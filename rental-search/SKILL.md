---
name: rental-search
description: 智能搜索多平台个人房源，支持地点关键词、距离过滤、时间过滤。目前已支持58同城，后续可拓展其他房源平台。
---

# 租房搜索 Skill

智能搜索多平台个人房源，支持地点关键词、距离过滤、时间过滤。目前已支持58同城，后续可拓展其他房源平台。

## 触发词

- 附近房源、租房搜索、58租房、个人房源搜索、找房子
- 用户输入类似"百度科技园附近5km的房源"、"中关村附近的个人房源"等查询

## 支持平台

| 平台 | 数据类型 | 状态 |
|------|----------|------|
| 58同城 | 个人房源 | ✅ 已支持 |
| 链家 | 待开发 | 🔄 规划中 |
| 自如 | 待开发 | 🔄 规划中 |
| 豆瓣租房 | 待开发 | 🔄 规划中 |

## 使用方式

用户输入自然语言查询，系统自动解析并生成搜索配置。

**示例查询:**
- "百度科技园附近5km的房源"
- "中关村附近3km 15天内的房源"
- "国贸附近 价格3000-5000的整租"
- "望京附近2km 一居室"
- "西二旗附近 面积30-50平的合租"
- "上地附近 50平以内的房源"

## 参数解析规则

| 参数 | 提取规则 | 默认值 |
|------|----------|--------|
| 地点 | 移除其他参数后的剩余文本 | 必填 |
| 距离 | 匹配 `\d+(?:\.\d+)?\s*(km|公里|米|m)` | 5km |
| 时间 | 匹配 `\d+\s*天` | 15天 |
| 价格 | 匹配 `价格?\d+-\d+` 或 `\d+以[内下]` | 不限 |
| 面积 | 匹配 `面积?\d+-\d+` 或 `\d+平以[内下]` | 不限 |
| 户型 | 匹配 `一居|两居|三居|开间` | 不限 |
| 租赁方式 | 匹配 `整租|合租` | 不限 |

## 输出格式

### 1. 搜索配置输出 (JSON)

```json
{
  "status": "success",
  "params": {
    "location": "百度科技园",
    "radius_km": 5.0,
    "days": 15,
    "price_min": null,
    "price_max": null,
    "area_min": null,
    "area_max": null,
    "rooms": null,
    "rental_type": null
  },
  "location_info": {
    "name": "百度科技园",
    "lat": 40.0569,
    "lng": 116.3015,
    "district": "海淀"
  },
  "search_urls": [
    {
      "district": "海淀",
      "url": "https://bj.58.com/haidian/zufang/0/",
      "distance": 2.5
    }
  ],
  "javascript_extractor": "Array.from(document.querySelectorAll('li'))...",
  "created_at": "2026-04-14T17:00:00"
}
```

### 2. 房源数据输出 (JSON)

每条房源数据结构：

```json
{
  "title": "整租 软件园二期 1室1厅",
  "price": 3500,
  "area": 45.0,
  "location": "西二旗",
  "community": "软件园二期",
  "rooms": 1,
  "rental_type": "整租",
  "distance": 1.2,
  "nearest_subway": "西二旗 (800m)",
  "publish_time": "今天",
  "url": "https://bj.58.com/...",
  "image_url": "https://pic.58.com/...",
  "platform": "wuba"
}
```

### 3. Excel 输出

生成文件：`{地点}附近房源.xlsx`

| 字段 | 类型 | 说明 |
|------|------|------|
| 标题 | string | 房源标题 |
| 类型 | string | 整租/合租 |
| 小区 | string | 小区名称 |
| 房间数 | int | 室数 |
| 面积(㎡) | float | 平方米 |
| 租金(元/月) | int | 月租金 |
| 距离(km) | float | 距目标点距离 |
| 最近地铁站 | string | 最近的地铁站名称及距离（3km内） |
| 发布时间 | string | 房源发布日期 |
| 链接 | string | 房源详情页URL |

### 4. 错误输出

```json
{
  "status": "error",
  "error_code": "LOCATION_NOT_FOUND",
  "error_message": "未找到地点: xxx",
  "suggestion": "请确认地点名称是否正确"
}
```

**错误码定义：**

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| LOCATION_NOT_FOUND | 地点未找到 | 确认地点名称 |
| NO_LISTINGS | 无符合条件的房源 | 扩大搜索范围 |
| ANTI_CRAWL | 触发反爬验证 | 点击认证按钮 |
| NETWORK_ERROR | 网络错误 | 重试请求 |

## 工作流程

### 1. 解析用户输入

```bash
python scripts/main.py "百度科技园附近5km的房源"
```

或使用 RentalSearchEngine:

```python
from scripts.main import RentalSearchEngine

engine = RentalSearchEngine()
result = engine.search("百度科技园附近5km的房源")
# 返回标准 JSON 格式的搜索配置
```

### 2. 地理定位

使用预设坐标或百度地图API获取地点坐标:
- 优先匹配预设地点库
- 未匹配时调用百度地图地理编码API

**预设地点坐标 (北京):**
- 百度科技园: (40.0569, 116.3015)
- 中关村: (39.9841, 116.3075)
- 国贸: (39.9087, 116.4594)
- 望京: (40.0032, 116.4773)
- 西二旗: (40.0569, 116.3015)
- 上地: (40.0310, 116.2870)
- 五道口: (39.9929, 116.3370)

### 3. 确定搜索区域

根据目标点坐标，筛选距离范围内的行政区划:
- 计算各区域中心与目标点的距离
- 筛选距离 ≤ 半径 + 10km 的区域（留余量）
- 按距离排序

### 4. 生成搜索配置

本 Skill 生成搜索 URL 和数据提取代码，**网页抓取由调用方负责**。

**58同城 URL构建规则:**
```
https://{city_code}.58.com/{district}/zufang/0/{filters}/  # 整租
https://{city_code}.58.com/{district}/hezu/0/{filters}/    # 合租

参数说明:
- city_code: 城市代码 (如 bj=北京, sh=上海)
- district: 区域URL名 (如 haidian=海淀)
- /0/: 个人房源 (固定)
```

**价格过滤URL:**
```
/b9/  = 600-1000元
/b10/ = 1000-1500元
/b11/ = 1500-2000元
/b12/ = 2000-3000元
/b13/ = 3000-5000元
/b14/ = 5000-8000元
/b15/ = 8000元以上
```

**户型过滤URL:**
```
/j1/ = 一室
/j2/ = 两室
/j3/ = 三室
```

### 5. 数据提取代码

本 Skill 提供可在浏览器中执行的 JavaScript 提取代码:

```javascript
// 58同城数据提取脚本 (WubaAdapter.get_javascript_extractor())
Array.from(document.querySelectorAll("li")).filter(li => {
  const h2 = li.querySelector("h2");
  return h2 && (h2.textContent.includes("整租") || h2.textContent.includes("合租"));
}).map(li => {
  // 提取房源信息...
});
```

完整代码见 `scripts/platforms/wuba.py` 中的 `get_javascript_extractor()` 方法。

### 6. 过滤与排序

**距离过滤:**
- 根据小区位置估算坐标
- 计算与目标点的实际距离
- 过滤距离 > 半径的房源

**时间过滤:**
- 解析发布时间字符串
- 过滤发布时间 > 天数限制的房源

**排序:**
- 按距离升序排列

## 架构设计

### 模块结构

```
scripts/
├── __init__.py          # 包入口
├── main.py              # 主程序入口
├── config.py            # 配置管理(单例模式)
├── models/
│   ├── __init__.py
│   ├── params.py        # SearchParams 数据类
│   └── listing.py       # Listing 数据类
├── parsers/
│   ├── __init__.py
│   ├── base.py          # 解析器基类
│   └── query_parser.py  # 查询解析器(责任链模式)
├── platforms/
│   ├── __init__.py
│   ├── base.py          # 平台适配器基类(策略模式)
│   ├── wuba.py          # 58同城实现
│   └── factory.py       # 平台工厂(工厂模式)
├── geo/
│   ├── __init__.py
│   ├── distance.py      # 距离计算
│   ├── location.py      # 地点服务
│   └── subway.py        # 地铁站服务
└── exporters/
    ├── __init__.py
    ├── base.py          # 导出器基类
    └── excel_exporter.py # Excel导出
```

### 设计模式

| 模式 | 应用场景 | 实现位置 |
|------|----------|----------|
| 责任链模式 | 查询参数解析 | `parsers/query_parser.py` |
| 策略模式 | 平台适配器 | `platforms/base.py` |
| 工厂模式 | 平台创建 | `platforms/factory.py` |
| 单例模式 | 配置管理 | `config.py` |
| 数据类模式 | 数据模型 | `models/` |

## 可选依赖

- `baidu-map-webapi`: 地理定位（未配置时使用预设坐标）
- `openpyxl`: Excel 生成

## 注意事项

1. **反爬机制**: 58同城有反爬验证，处理方式:
   - 遇到验证页面时，点击"点击按钮进行认证"完成验证
   - 控制请求频率（每页间隔2-3秒）
   - 使用浏览器自动化而非直接HTTP请求

2. **距离计算**: 
   - 使用直线距离，实际通勤距离可能不同
   - 可考虑使用百度地图路线规划API获取实际距离

3. **数据时效性**:
   - 部分房源可能已下架
   - 建议优先查看最新发布的房源

4. **API配置**:
   - 百度地图API需要申请AK
   - 如未配置，使用预设区域坐标

## 示例对话

**用户:** 百度科技园附近5km的房源

**助手:** 
```json
{
  "status": "success",
  "params": {
    "location": "百度科技园",
    "radius_km": 5.0,
    "days": 15
  },
  "location_info": {
    "lat": 40.0569,
    "lng": 116.3015,
    "district": "海淀"
  },
  "search_urls": [
    {
      "district": "海淀",
      "url": "https://bj.58.com/haidian/zufang/0/",
      "distance": 2.5
    }
  ],
  "javascript_extractor": "..."
}
```

**用户:** 中关村附近3km 30天内的

**助手:**
```json
{
  "status": "success",
  "params": {
    "location": "中关村",
    "radius_km": 3.0,
    "days": 30
  },
  "location_info": {
    "lat": 39.9841,
    "lng": 116.3075,
    "district": "海淀"
  },
  "search_urls": [
    {
      "district": "海淀",
      "url": "https://bj.58.com/haidian/zufang/0/",
      "distance": 1.2
    }
  ],
  "javascript_extractor": "..."
}
```
