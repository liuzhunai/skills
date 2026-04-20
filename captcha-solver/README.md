# 验证码处理 Skill

通用网页验证码处理工具，支持多种验证码类型，采用混合识别方案。

## 支持的验证码类型

| 类型 | 示例 | 识别方案 | 准确率 |
|------|------|----------|--------|
| 滑动验证码 | 拖动滑块到缺口 | OpenCV + OCR 增强 | 85%+ |
| 拼图验证码 | 拼图块对齐 | OpenCV 模板匹配 | 80%+ |
| 文字验证码 | 输入图片中的文字 | PaddleOCR 多预处理 | 95%+ |
| 计算验证码 | "3+5=?" | OCR + 本地计算 | 99% |
| 点击验证码 | "点击红绿灯" | DuMate 多模态 | 85%+ |
| 选择验证码 | 选择包含汽车的图片 | DuMate 多模态 | 85%+ |

## PaddleOCR 增强能力

### 滑动验证码增强

PaddleOCR 可辅助定位缺口：
- 文字检测：识别验证码中的文字区域
- 区域排除：避免将文字误判为缺口
- 空白检测：寻找文字区域间的空白位置

### 文字验证码增强

多种预处理方式提升识别率：
- 原图识别
- 灰度化处理
- 二值化处理
- 对比度增强（CLAHE）
- 去噪处理
- 组合预处理

## 快速开始

### 基本用法

```
/captcha-solver 处理验证码
```

### 配合 dumate-browser-use

```python
from scripts.solver import CaptchaSolver

solver = CaptchaSolver()
result = solver.solve(screenshot_path)
```

### 滑动验证码详细分析

```python
from scripts.recognizers.slider import SliderRecognizer

recognizer = SliderRecognizer(use_ocr_enhance=True)

# 获取详细信息
info = recognizer.get_slider_info("captcha.png")
print(info)
# {
#   "image_size": (300, 200),
#   "ocr_text": "拖动滑块完成验证",
#   "gap_candidates": [
#     {"method": "edge", "x": 120},
#     {"method": "ocr", "x": 125}
#   ]
# }
```

### 文字验证码详细分析

```python
from scripts.recognizers.text import TextRecognizer

recognizer = TextRecognizer()

# 获取 OCR 详细结果
detail = recognizer.get_ocr_detail("captcha.png")
print(detail)
# {
#   "results": [
#     {"text": "abc123", "confidence": 0.95, "method": "original"},
#     {"text": "abc123", "confidence": 0.92, "method": "binary"},
#     ...
#   ],
#   "best_text": "abc123"
# }
```

## 输出格式

### 操作指令

```json
{
  "status": "success",
  "captcha_type": "slider",
  "action": {
    "type": "drag",
    "selector": ".slider-btn",
    "offset_x": 120
  },
  "confidence": 0.85
}
```

### 操作类型

| 类型 | 说明 | 参数 |
|------|------|------|
| click | 点击指定位置 | x, y |
| drag | 拖动元素 | selector, offset_x, offset_y |
| input | 输入文字 | selector, text |
| multi_click | 多点点击 | points: [(x,y), ...] |

## 技术实现

### 滑动验证码

```python
# 1. OpenCV 边缘检测
# 2. OCR 文字区域检测（增强）
# 3. 颜色差异检测（备选）
# 4. 多方法结果融合
# 5. 生成人类化轨迹
```

### 文字验证码

```python
# 1. 多种图像预处理
#    - 原图、灰度、二值化、增强、去噪
# 2. PaddleOCR 识别
# 3. 结果置信度排序
# 4. 文本清理与修正
```

### 点击验证码

```python
# 1. 截取验证码图片
# 2. DuMate 多模态识别
# 3. 返回点击坐标
# 4. 执行点击操作
```

## 目录结构

```
captcha-solver/
├── SKILL.md
├── README.md
└── scripts/
    ├── __init__.py
    ├── solver.py          # 主入口
    ├── detector.py        # 类型检测
    ├── recognizers/       # 识别器
    │   ├── base.py
    │   ├── slider.py      # 滑动验证码（OpenCV + OCR）
    │   ├── text.py        # 文字验证码（多预处理）
    │   └── click.py       # 点击验证码（多模态）
    ├── executors/         # 执行器
    │   ├── click.py
    │   ├── drag.py
    │   └── input.py
    └── utils/
        ├── image.py       # 图像处理
        └── humanize.py    # 行为模拟
```

## 注意事项

1. **验证码可能失败**: 建议设置重试机制
2. **人类行为模拟**: 避免被检测为机器人
3. **隐私保护**: 图片优先本地处理
4. **PaddleOCR 增强**: 显著提升识别准确率

## 依赖安装

```bash
# 基础依赖
pip install opencv-python numpy pillow

# OCR 引擎（推荐 PaddleOCR）
pip install paddleocr paddlepaddle

# 或使用 pytesseract（准确率较低）
pip install pytesseract
```

## 性能对比

| 验证码类型 | 无 OCR 增强 | 有 PaddleOCR 增强 |
|------------|-------------|-------------------|
| 滑动验证码 | 75% | 85%+ |
| 文字验证码 | 80% | 95%+ |
| 计算验证码 | 85% | 99% |
