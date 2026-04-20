"""验证码自动检测监控器

用于在网页自动化流程中自动检测验证码出现。
"""

import re
from enum import Enum
from typing import Optional, List, Callable, Any
from dataclasses import dataclass, field


class DetectionSignal(Enum):
    """检测信号类型"""

    ELEMENT = "element"  # 元素检测
    TEXT = "text"  # 文本检测
    URL = "url"  # URL 检测
    OVERLAY = "overlay"  # 遮罩层检测


@dataclass
class DetectionRule:
    """检测规则"""

    signal: DetectionSignal
    patterns: List[str]  # 匹配模式列表
    description: str
    priority: int = 0  # 优先级，越高越先检测


@dataclass
class DetectionResult:
    """检测结果"""

    detected: bool
    signal: Optional[DetectionSignal] = None
    matched_pattern: Optional[str] = None
    confidence: float = 0.0
    description: str = ""


class CaptchaMonitor:
    """验证码监控器

    在网页自动化流程中持续监控验证码出现。
    支持多种检测信号：元素、文本、URL、遮罩层。
    """

    # 默认检测规则
    DEFAULT_RULES = [
        # 元素检测规则
        DetectionRule(
            signal=DetectionSignal.ELEMENT,
            patterns=[
                # 滑块元素
                r'class="[^"]*slider[^"]*"',
                r'class="[^"]*slide-btn[^"]*"',
                r'class="[^"]*drag[^"]*"',
                # 验证码图片
                r'class="[^"]*captcha[^"]*"',
                r'class="[^"]*verify[^"]*"',
                # 点击验证码网格
                r'class="[^"]*captcha-grid[^"]*"',
                r'class="[^"]*verify-grid[^"]*"',
                # 拼图元素
                r'class="[^"]*puzzle[^"]*"',
                # iframe 验证码
                r"iframe[^>]*captcha",
                r"iframe[^>]*verify",
            ],
            description="检测到验证码元素",
            priority=10,
        ),
        # 文本检测规则
        DetectionRule(
            signal=DetectionSignal.TEXT,
            patterns=[
                r"请完成.*验证",
                r"安全验证",
                r"拖动滑块",
                r"向右滑动",
                r"点击图中",
                r"选择.*图片",
                r"请输入验证码",
                r"人机验证",
                r"验证码.*错误",
                r"滑动验证",
                r"点击验证",
            ],
            description="检测到验证码提示文本",
            priority=8,
        ),
        # URL 检测规则
        DetectionRule(
            signal=DetectionSignal.URL,
            patterns=[
                r"/captcha",
                r"/verify",
                r"/validate",
                r"/check",
                r"captcha\.",
                r"verify\.",
            ],
            description="检测到验证码相关 URL",
            priority=5,
        ),
        # 遮罩层检测规则
        DetectionRule(
            signal=DetectionSignal.OVERLAY,
            patterns=[
                r'class="[^"]*modal[^"]*"',
                r'class="[^"]*overlay[^"]*"',
                r'class="[^"]*mask[^"]*"',
                r'class="[^"]*popup[^"]*"',
                r'style="[^"]*position:\s*fixed[^"]*"',
            ],
            description="检测到遮罩层/弹窗",
            priority=3,
        ),
    ]

    def __init__(self, custom_rules: List[DetectionRule] = None):
        """初始化监控器

        Args:
            custom_rules: 自定义检测规则（会与默认规则合并）
        """
        self.rules = self.DEFAULT_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)
            # 按优先级排序
            self.rules.sort(key=lambda r: r.priority, reverse=True)

        # 回调函数
        self._on_detected: Optional[Callable[[DetectionResult], Any]] = None

    def set_callback(self, callback: Callable[[DetectionResult], Any]):
        """设置检测到验证码时的回调函数

        Args:
            callback: 回调函数，接收 DetectionResult 参数
        """
        self._on_detected = callback

    def check_html(self, html: str) -> DetectionResult:
        """检查 HTML 中是否有验证码

        Args:
            html: 页面 HTML 内容

        Returns:
            DetectionResult 检测结果
        """
        for rule in self.rules:
            if rule.signal not in [DetectionSignal.ELEMENT, DetectionSignal.OVERLAY]:
                continue

            for pattern in rule.patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    result = DetectionResult(
                        detected=True,
                        signal=rule.signal,
                        matched_pattern=pattern,
                        confidence=0.7 + (rule.priority / 100),
                        description=rule.description,
                    )
                    self._trigger_callback(result)
                    return result

        return DetectionResult(detected=False)

    def check_text(self, text: str) -> DetectionResult:
        """检查页面文本中是否有验证码提示

        Args:
            text: 页面文本内容

        Returns:
            DetectionResult 检测结果
        """
        for rule in self.rules:
            if rule.signal != DetectionSignal.TEXT:
                continue

            for pattern in rule.patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result = DetectionResult(
                        detected=True,
                        signal=rule.signal,
                        matched_pattern=pattern,
                        confidence=0.8 + (rule.priority / 100),
                        description=rule.description,
                    )
                    self._trigger_callback(result)
                    return result

        return DetectionResult(detected=False)

    def check_url(self, url: str) -> DetectionResult:
        """检查 URL 是否为验证码相关

        Args:
            url: 页面 URL

        Returns:
            DetectionResult 检测结果
        """
        for rule in self.rules:
            if rule.signal != DetectionSignal.URL:
                continue

            for pattern in rule.patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    result = DetectionResult(
                        detected=True,
                        signal=rule.signal,
                        matched_pattern=pattern,
                        confidence=0.6 + (rule.priority / 100),
                        description=rule.description,
                    )
                    self._trigger_callback(result)
                    return result

        return DetectionResult(detected=False)

    def check_all(
        self, html: str = None, text: str = None, url: str = None
    ) -> DetectionResult:
        """综合检查所有信号

        Args:
            html: 页面 HTML
            text: 页面文本
            url: 页面 URL

        Returns:
            DetectionResult 检测结果（返回置信度最高的）
        """
        results = []

        if html:
            results.append(self.check_html(html))
        if text:
            results.append(self.check_text(text))
        if url:
            results.append(self.check_url(url))

        # 过滤掉未检测到的
        detected = [r for r in results if r.detected]

        if not detected:
            return DetectionResult(detected=False)

        # 返回置信度最高的
        return max(detected, key=lambda r: r.confidence)

    def _trigger_callback(self, result: DetectionResult):
        """触发回调函数"""
        if self._on_detected and result.detected:
            self._on_detected(result)


class PageChangeDetector:
    """页面变化检测器

    检测页面变化以判断是否有验证码出现。
    """

    def __init__(self):
        self._last_html_hash: Optional[str] = None
        self._last_text_hash: Optional[str] = None

    def detect_change(self, html: str = None, text: str = None) -> bool:
        """检测页面是否有变化

        Args:
            html: 当前页面 HTML
            text: 当前页面文本

        Returns:
            是否有变化
        """
        import hashlib

        changed = False

        if html:
            html_hash = hashlib.md5(html.encode()).hexdigest()
            if self._last_html_hash and html_hash != self._last_html_hash:
                changed = True
            self._last_html_hash = html_hash

        if text:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if self._last_text_hash and text_hash != self._last_text_hash:
                changed = True
            self._last_text_hash = text_hash

        return changed

    def reset(self):
        """重置状态"""
        self._last_html_hash = None
        self._last_text_hash = None


# 便捷函数
def check_captcha_presence(html: str = None, text: str = None, url: str = None) -> bool:
    """快速检查页面是否存在验证码

    Args:
        html: 页面 HTML
        text: 页面文本
        url: 页面 URL

    Returns:
        是否检测到验证码
    """
    monitor = CaptchaMonitor()
    result = monitor.check_all(html=html, text=text, url=url)
    return result.detected
