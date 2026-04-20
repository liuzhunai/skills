"""验证码类型检测"""

import re
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class CaptchaType(Enum):
    """验证码类型"""

    SLIDER = "slider"  # 滑动验证码
    PUZZLE = "puzzle"  # 拼图验证码
    TEXT = "text"  # 文字验证码
    CALCULATE = "calculate"  # 计算验证码
    CLICK = "click"  # 点击验证码
    SELECT = "select"  # 选择验证码
    UNKNOWN = "unknown"  # 未知类型


@dataclass
class CaptchaInfo:
    """验证码信息"""

    captcha_type: CaptchaType
    selectors: Dict[str, str]  # 相关元素选择器
    description: str  # 验证码描述
    confidence: float  # 检测置信度


class CaptchaDetector:
    """验证码类型检测器

    通过分析页面元素和文本，判断验证码类型。
    """

    # 验证码关键词映射
    KEYWORDS_MAP = {
        CaptchaType.SLIDER: [
            "拖动滑块",
            "滑动验证",
            "向右滑动",
            "拖动到",
            "slider",
            "drag",
            "slide",
        ],
        CaptchaType.PUZZLE: ["拼图", "对齐", "缺口", "puzzle", "align"],
        CaptchaType.TEXT: ["请输入", "验证码", "看不清", "input", "captcha text"],
        CaptchaType.CALCULATE: [
            "计算",
            "等于",
            "+",
            "-",
            "×",
            "÷",
            "calculate",
            "equals",
        ],
        CaptchaType.CLICK: ["点击图中", "选择", "请点击", "click", "select all"],
        CaptchaType.SELECT: ["选择包含", "选择所有", "选出", "select images", "choose"],
    }

    # 元素选择器映射
    SELECTORS_MAP = {
        CaptchaType.SLIDER: {
            "slider": ".slider-btn, .slide-btn, [class*='slider'], [class*='slide-btn']",
            "track": ".slider-track, .slide-track, [class*='track']",
            "background": ".slider-bg, .slide-bg, [class*='slider-bg']",
        },
        CaptchaType.PUZZLE: {
            "puzzle": ".puzzle-piece, .puzzle-block, [class*='puzzle']",
            "target": ".puzzle-target, .puzzle-hole, [class*='target']",
        },
        CaptchaType.TEXT: {
            "image": ".captcha-img, .verify-img, [class*='captcha-img']",
            "input": ".captcha-input, .verify-input, [class*='captcha-input']",
        },
        CaptchaType.CLICK: {
            "grid": ".captcha-grid, .verify-grid, [class*='grid']",
            "images": ".captcha-image, .verify-image, [class*='captcha-img']",
        },
    }

    @classmethod
    def detect_from_text(cls, text: str) -> CaptchaInfo:
        """从页面文本检测验证码类型

        Args:
            text: 页面文本内容

        Returns:
            CaptchaInfo 验证码信息
        """
        text_lower = text.lower()

        # 匹配关键词
        for captcha_type, keywords in cls.KEYWORDS_MAP.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return CaptchaInfo(
                        captcha_type=captcha_type,
                        selectors=cls.SELECTORS_MAP.get(captcha_type, {}),
                        description=f"检测到关键词: {keyword}",
                        confidence=0.7,
                    )

        return CaptchaInfo(
            captcha_type=CaptchaType.UNKNOWN,
            selectors={},
            description="未识别到验证码类型",
            confidence=0.0,
        )

    @classmethod
    def detect_from_html(cls, html: str) -> CaptchaInfo:
        """从 HTML 检测验证码类型

        Args:
            html: 页面 HTML

        Returns:
            CaptchaInfo 验证码信息
        """
        html_lower = html.lower()

        # 检测滑块元素
        if any(s in html_lower for s in ["slider", "slide-btn", "滑块"]):
            return CaptchaInfo(
                captcha_type=CaptchaType.SLIDER,
                selectors=cls.SELECTORS_MAP.get(CaptchaType.SLIDER, {}),
                description="检测到滑块元素",
                confidence=0.8,
            )

        # 检测拼图元素
        if any(s in html_lower for s in ["puzzle", "拼图"]):
            return CaptchaInfo(
                captcha_type=CaptchaType.PUZZLE,
                selectors=cls.SELECTORS_MAP.get(CaptchaType.PUZZLE, {}),
                description="检测到拼图元素",
                confidence=0.8,
            )

        # 检测点击验证码网格
        if "grid" in html_lower and "captcha" in html_lower:
            return CaptchaInfo(
                captcha_type=CaptchaType.CLICK,
                selectors=cls.SELECTORS_MAP.get(CaptchaType.CLICK, {}),
                description="检测到验证码网格",
                confidence=0.7,
            )

        # 检测文字验证码
        if any(s in html_lower for s in ["captcha-img", "verify-img"]):
            return CaptchaInfo(
                captcha_type=CaptchaType.TEXT,
                selectors=cls.SELECTORS_MAP.get(CaptchaType.TEXT, {}),
                description="检测到验证码图片",
                confidence=0.6,
            )

        return CaptchaInfo(
            captcha_type=CaptchaType.UNKNOWN,
            selectors={},
            description="未识别到验证码元素",
            confidence=0.0,
        )

    @classmethod
    def detect_calculation(cls, text: str) -> Optional[str]:
        """检测并计算数学表达式

        Args:
            text: 包含数学表达式的文本

        Returns:
            计算结果字符串，如果不是计算题返回 None
        """
        # 匹配简单的加减乘除
        patterns = [
            r"(\d+)\s*\+\s*(\d+)",  # 加法
            r"(\d+)\s*-\s*(\d+)",  # 减法
            r"(\d+)\s*[×x]\s*(\d+)",  # 乘法
            r"(\d+)\s*[÷/]\s*(\d+)",  # 除法
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    a, b = int(match.group(1)), int(match.group(2))
                    if "+" in pattern:
                        return str(a + b)
                    elif "-" in pattern:
                        return str(a - b)
                    elif "×" in pattern or "x" in pattern.lower():
                        return str(a * b)
                    elif "÷" in pattern or "/" in pattern:
                        return str(a // b) if a % b == 0 else str(round(a / b, 2))
                except:
                    pass

        return None
