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

用户输入自然语言查询，系统自动解析并搜索。

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

### 扩展新平台

1. 创建平台适配器，继承 `PlatformAdapter`:

```python
from platforms.base import PlatformAdapter, SearchURL
from models.params import SearchParams

class LianjiaAdapter(PlatformAdapter):
    NAME = "lianjia"
    DISPLAY_NAME = "链家"
    
    def build_search_urls(self, params: SearchParams, districts: List[Dict]) -> List[SearchURL]:
        # 实现URL构建逻辑
        pass
    
    def parse_list_page(self, html: str) -> List[Dict]:
        # 实现列表页解析
        pass
    
    def parse_detail_page(self, html: str, url: str) -> Dict:
        # 实现详情页解析
        pass
    
    def supports_rental_type(self, rental_type: Optional[str]) -> bool:
        return True
```

2. 注册到工厂:

```python
from platforms.factory import PlatformFactory

PlatformFactory.register("lianjia", LianjiaAdapter)
```

### 扩展新解析器

创建解析器并添加到责任链:

```python
from parsers.base import ParserHandler

class FloorParser(ParserHandler):
    def _do_parse(self, query: str, params: dict) -> dict:
        # 解析楼层信息
        match = re.search(r"(\d+)层", query)
        if match:
            params["floor"] = int(match.group(1))
        return params
    
    def get_pattern(self) -> str:
        return "楼层: 5层, 高层, 低层"
```

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

### 4. 搜索房源

使用 `dumate-browser-use` skill 访问房源平台。

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

### 5. 提取房源数据

使用JavaScript在页面中提取数据:

```javascript
// 58同城数据提取脚本 (WubaAdapter.get_javascript_extractor())
Array.from(document.querySelectorAll("li")).filter(li => {
  const h2 = li.querySelector("h2");
  return h2 && (h2.textContent.includes("整租") || h2.textContent.includes("合租"));
}).map(li => {
  // 提取房源信息...
});
```

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

### 7. 输出结果

生成Excel表格:

| 字段 | 说明 |
|------|------|
| 标题 | 房源标题 |
| 类型 | 整租/合租 |
| 小区 | 小区名称 |
| 房间数 | 室数 |
| 面积(㎡) | 平方米 |
| 租金(元/月) | 月租金 |
| 距离(km) | 距目标点距离 |
| 最近地铁站 | 最近的地铁站名称及距离（3km内） |
| 发布时间 | 房源发布日期 |
| 链接 | 房源详情页URL |

## 依赖Skills

- `dumate-browser-use`: 网页抓取
- `baidu-map-webapi`: 地理定位（可选，可使用预设坐标）
- `xlsx`: Excel生成

## 注意事项

1. **反爬机制**: 房源平台有反爬措施，需要:
   - 控制请求频率（每页间隔2-3秒）
   - 使用浏览器自动化而非直接HTTP请求
   - 处理验证码情况

2. **距离计算**: 
   - 使用直线距离，实际通勤距离可能不同
   - 可考虑使用百度地图路线规划API获取实际距离

3. **数据时效性**:
   - 部分房源可能已下架
   - 建议优先查看最新发布的房源

4. **API配置**:
   - 百度地图API需要申请AK
   - 如未配置，使用预设区域坐标

## 错误处理

| 错误 | 处理方式 |
|------|----------|
| 地点未找到 | 提示用户确认地点名称 |
| 无房源 | 扩大搜索半径或时间范围 |
| 验证码 | 暂停并提示用户手动处理 |
| 网络错误 | 重试3次后报错 |

## 示例对话

**用户:** 百度科技园附近5km的房源

**助手:** 
1. 解析查询: 地点=百度科技园, 距离=5km, 时间=15天
2. 获取坐标: (40.0569, 116.3015)
3. 相关区域: 海淀区(2.5km), 昌平区(8.3km)
4. 搜索中...
5. 找到 45 套符合条件的房源
6. 已生成Excel文件

**用户:** 中关村附近3km 30天内的

**助手:**
1. 解析查询: 地点=中关村, 距离=3km, 时间=30天
2. 获取坐标: (39.9841, 116.3075)
3. 相关区域: 海淀区(1.2km)
4. 搜索中...
5. 找到 78 套符合条件的房源
6. 已生成Excel文件
