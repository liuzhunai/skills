"""Captcha Solver - 通用验证码处理工具"""

from .solver import CaptchaSolver, SolveResult
from .detector import CaptchaDetector, CaptchaType, CaptchaInfo
from .monitor import (
    CaptchaMonitor,
    DetectionSignal,
    DetectionResult,
    check_captcha_presence,
)
from .hooks import CaptchaHook, HookContext, HookResult, BrowserAutomationIntegration

__all__ = [
    # 核心类
    "CaptchaSolver",
    "SolveResult",
    "CaptchaDetector",
    "CaptchaType",
    "CaptchaInfo",
    # 自动触发
    "CaptchaMonitor",
    "DetectionSignal",
    "DetectionResult",
    "check_captcha_presence",
    # 钩子集成
    "CaptchaHook",
    "HookContext",
    "HookResult",
    "BrowserAutomationIntegration",
]
