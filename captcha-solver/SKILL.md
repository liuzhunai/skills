---
name: captcha-solver
description: 通用网页验证码处理工具，支持滑动验证码、点击验证码、文字验证码等多种类型，采用本地处理与AI视觉混合方案。在网页自动化流程中自动检测并处理验证码。
metadata:
  openclaw:
    requires:
      bins:
        - python3
      packages:
        - opencv-python
        - paddleocr
---

# 验证码处理 Skill

通用网页验证码处理工具，支持多种验证码类型，采用混合识别方案。

> **自动触发**: 在使用 `dumate-browser-use` 进行网页操作时，自动检测并处理验证码弹窗。

## 触发场景

### 自动触发（推荐）

在以下场景自动触发：

1. **网页自动化流程中** - 使用 `dumate-browser-use` 时自动检测验证码
2. **检测到验证码元素** - 页面出现滑块、验证码图片等元素
3. **检测到验证码文本** - 页面出现"请完成验证"、"拖动滑块"等提示

### 手动触发

```
/captcha-solver 处理验证码
/captcha-solver 检测当前页面是否有验证码
```

## 自动检测机制

### 检测验证码出现的信号

| 检测方式 | 检测内容 | 示例 |
|----------|----------|------|
| 元素检测 | 滑块、验证码图片、输入框 | `.slider-btn`, `.captcha-img` |
| 文本检测 | 验证码提示文字 | "请完成安全验证"、"拖动滑块" |
| 页面变化 | 弹窗、遮罩层 | 验证码弹窗覆盖 |
| 请求拦截 | 验证码相关请求 | `/captcha`, `/verify` |

### 检测信号类型

```python
from captcha_solver import DetectionSignal

# 支持的检测信号
DetectionSignal.ELEMENT   # 元素检测（滑块、验证码图片等）
DetectionSignal.TEXT      # 文本检测（提示文字）
DetectionSignal.URL       # URL 检测（/captcha, /verify）
DetectionSignal.OVERLAY   # 遮罩层检测（弹窗、模态框）
```

### 使用 CaptchaMonitor

```python
from captcha_solver import CaptchaMonitor

monitor = CaptchaMonitor()

# 检查 HTML
result = monitor.check_html(page_html)

# 检查文本
result = monitor.check_text(page_text)

# 综合检查
result = monitor.check_all(html=page_html, text=page_text, url=page_url)

if result.detected:
    print(f"检测到验证码: {result.description}")
    print(f"置信度: {result.confidence}")
```

### 快速检测函数

```python
from captcha_solver import check_captcha_presence

# 快速检查页面是否有验证码
has_captcha = check_captcha_presence(html=page_html, text=page_text)
```

### 工作流集成

```python
from captcha_solver import CaptchaHook, HookContext

# 创建钩子
hook = CaptchaHook(auto_solve=True, max_retries=3)

# 在页面操作后检查
context = HookContext(
    page_url="https://example.com",
    page_html=page_html,
    page_text=page_text,
    screenshot_path="/tmp/screenshot.png",
)

result = hook.after_action(context)

if result.captcha_detected:
    print(f"验证码处理结果: {result.message}")
    if result.captcha_solved:
        print("验证码已自动处理")
```

### 与 dumate-browser-use 集成

```python
from captcha_solver import BrowserAutomationIntegration

integration = BrowserAutomationIntegration(auto_solve=True)

# 在自动化流程中调用
result = integration.check_and_solve(
    page_url=page.url,
    page_html=page.content(),
    page_text=page.inner_text(),
    screenshot_path=screenshot_path,
)

# 获取操作指令
if result.solve_result:
    instructions = integration.get_action_instructions(result.solve_result)
    # 传递给 dumate-browser-use 执行
```

## 触发场景（Usage）

### 适合使用本技能的场景
- 网页自动化流程中遇到验证码
- 用户明确要求处理验证码
- 检测到页面出现滑块、验证码图片等元素
- 页面出现"请完成验证"、"拖动滑块"等提示文字

### 触发词
- 验证码、captcha、人机验证、滑动验证、点击验证
- 遇到"请完成安全验证"、"拖动滑块"、"点击图中"等提示

## 支持的验证码类型

| 类型 | 识别方案 | 准确率 | 说明 |
|------|----------|--------|------|
| 滑动验证码 | OpenCV 本地 | 85%+ | 拖动滑块到缺口位置 |
| 拼图验证码 | OpenCV 本地 | 80%+ | 拖动拼图块对齐 |
| 文字验证码 | OCR 本地 | 90%+ | 识别并输入文字 |
| 计算验证码 | 本地计算 | 99% | 计算并输入结果 |
| 点击验证码 | DuMate 多模态 | 85%+ | 使用内置视觉能力识别 |
| 选择验证码 | DuMate 多模态 | 85%+ | 使用内置视觉能力识别 |

> **点击验证码说明**: 使用 DuMate 内置的多模态能力识别，无需配置外部 API。

## 工作流程

### 1. 检测验证码类型

自动检测当前页面的验证码类型：
- 滑动验证码：检测滑块元素
- 点击验证码：检测图片网格
- 文字验证码：检测文字图片
- 计算验证码：检测计算表达式

### 2. 选择识别方案

根据验证码类型选择最优方案：
- 简单验证码 → 本地处理（OpenCV/OCR）
- 复杂验证码 → AI 视觉模型

### 3. 执行验证操作

生成操作指令，由 `dumate-browser-use` 执行：
- 点击坐标
- 拖动轨迹
- 输入内容

## 输出格式

### 成功输出

```json
{
  "status": "success",
  "captcha_type": "slider",
  "action": {
    "type": "drag",
    "selector": ".slider-btn",
    "offset_x": 120,
    "offset_y": 0
  },
  "confidence": 0.85
}
```

### 失败输出

```json
{
  "status": "failed",
  "captcha_type": "click",
  "error": "无法识别目标图片",
  "suggestion": "请手动完成验证"
}
```

## 使用方式

### 方式一：自动处理

配合 `dumate-browser-use` 自动处理验证码：

```python
# 检测到验证码时自动调用
result = captcha_solver.solve(page_screenshot)
```

### 方式二：手动触发

用户遇到验证码时手动触发：

```
/captcha-solver 处理当前页面的验证码
```

### 方式三：点击验证码处理流程

点击验证码使用 DuMate 内置多模态能力：

1. **截图验证码** - 使用 `dumate-browser-use` 截取验证码图片
2. **DuMate 识别** - DuMate 使用多模态能力分析图片，识别目标位置
3. **返回坐标** - 返回需要点击的坐标列表
4. **执行点击** - 由 `dumate-browser-use` 执行点击操作

## 依赖

- `dumate-browser-use`: 浏览器操作、截图
- `opencv-python`: 图像处理（滑动验证码）
- `pytesseract` 或 `paddleocr`: OCR 识别（文字验证码）
- **DuMate 多模态能力**: 点击验证码识别（内置，无需配置）

## 注意事项

1. **人类行为模拟**: 拖动轨迹模拟真实人类操作，避免被检测
2. **重试机制**: 识别失败时自动重试，最多3次
3. **降级策略**: 本地处理失败时尝试 AI 视觉
4. **隐私保护**: 验证码图片仅在本地处理，不上传第三方

## 错误处理

| 错误 | 处理方式 |
|------|----------|
| 无法识别验证码类型 | 提示用户手动处理 |
| 识别置信度过低 | 尝试其他识别方案 |
| 操作执行失败 | 重试或提示用户 |
| AI API 调用失败 | 降级到本地处理 |

## 示例对话

**场景：链家滑动验证码**

**助手:**
检测到滑动验证码，正在处理...
1. 分析缺口位置：距离左侧 120px
2. 生成拖动轨迹（模拟人类操作）
3. 执行拖动操作
4. 验证通过

**场景：点击验证码（"点击红绿灯"）**

**助手:**
检测到点击验证码，正在处理...
1. 截取验证码图片
2. 使用多模态能力分析图片
3. 识别到 3 个红绿灯位置：[(45, 120), (89, 120), (133, 120)]
4. 执行多点点击操作
5. 验证通过
