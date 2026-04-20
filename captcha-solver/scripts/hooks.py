"""验证码处理钩子

用于与 dumate-browser-use 集成的钩子系统。
"""

import os
import tempfile
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass

from .monitor import CaptchaMonitor, DetectionResult
from .solver import CaptchaSolver, SolveResult


@dataclass
class HookContext:
    """钩子上下文"""

    page_url: str
    page_html: Optional[str] = None
    page_text: Optional[str] = None
    screenshot_path: Optional[str] = None
    action_type: Optional[str] = None  # click, input, navigate, etc.


@dataclass
class HookResult:
    """钩子执行结果"""

    captcha_detected: bool
    captcha_solved: bool
    solve_result: Optional[SolveResult] = None
    should_retry: bool = False
    message: str = ""


class CaptchaHook:
    """验证码处理钩子

    在网页自动化流程中自动检测和处理验证码。

    使用方式:
        hook = CaptchaHook()

        # 在每次页面操作后调用
        result = hook.after_action(context)

        if result.captcha_detected:
            print("检测到验证码，已自动处理")
    """

    def __init__(
        self,
        auto_solve: bool = True,
        max_retries: int = 3,
        on_detect: Callable[[DetectionResult], Any] = None,
        on_solve: Callable[[SolveResult], Any] = None,
    ):
        """初始化钩子

        Args:
            auto_solve: 是否自动处理验证码
            max_retries: 最大重试次数
            on_detect: 检测到验证码时的回调
            on_solve: 处理验证码后的回调
        """
        self.auto_solve = auto_solve
        self.max_retries = max_retries

        self.monitor = CaptchaMonitor()
        self.solver = CaptchaSolver()

        # 设置回调
        if on_detect:
            self.monitor.set_callback(on_detect)
        self._on_solve = on_solve

        # 状态追踪
        self._retry_count = 0
        self._last_solve_result: Optional[SolveResult] = None

    def before_action(self, context: HookContext) -> HookResult:
        """在执行页面操作前调用

        Args:
            context: 钩子上下文

        Returns:
            HookResult 钩子执行结果
        """
        # 检查是否有验证码
        detection = self.monitor.check_all(
            html=context.page_html,
            text=context.page_text,
            url=context.page_url,
        )

        if detection.detected:
            return HookResult(
                captcha_detected=True,
                captcha_solved=False,
                message=f"检测到验证码: {detection.description}",
                should_retry=True,
            )

        return HookResult(captcha_detected=False, captcha_solved=False)

    def after_action(self, context: HookContext) -> HookResult:
        """在执行页面操作后调用

        这是主要的入口点，用于检测和处理验证码。

        Args:
            context: 钩子上下文

        Returns:
            HookResult 钩子执行结果
        """
        # 1. 检测验证码
        detection = self.monitor.check_all(
            html=context.page_html,
            text=context.page_text,
            url=context.page_url,
        )

        if not detection.detected:
            return HookResult(captcha_detected=False, captcha_solved=False)

        # 2. 如果不自动处理，返回检测结果
        if not self.auto_solve:
            return HookResult(
                captcha_detected=True,
                captcha_solved=False,
                message="检测到验证码，等待手动处理",
            )

        # 3. 自动处理验证码
        if not context.screenshot_path:
            return HookResult(
                captcha_detected=True,
                captcha_solved=False,
                message="检测到验证码，但缺少截图",
            )

        solve_result = self.solver.solve(
            screenshot_path=context.screenshot_path,
            page_text=context.page_text,
            page_html=context.page_html,
        )

        # 4. 触发回调
        if self._on_solve:
            self._on_solve(solve_result)

        self._last_solve_result = solve_result

        return HookResult(
            captcha_detected=True,
            captcha_solved=solve_result.status == "success",
            solve_result=solve_result,
            message=solve_result.message,
            should_retry=solve_result.status != "success"
            and self._retry_count < self.max_retries,
        )

    def should_retry(self) -> bool:
        """是否应该重试

        Returns:
            是否应该重试
        """
        if self._retry_count >= self.max_retries:
            return False

        if self._last_solve_result and self._last_solve_result.status != "success":
            self._retry_count += 1
            return True

        return False

    def reset_retry(self):
        """重置重试计数"""
        self._retry_count = 0
        self._last_solve_result = None


class BrowserAutomationIntegration:
    """浏览器自动化集成

    提供与 dumate-browser-use 的集成接口。

    使用示例:
        integration = BrowserAutomationIntegration()

        # 在自动化脚本中
        def on_page_change(page):
            result = integration.check_and_solve(page)
            if result.captcha_detected:
                print(f"验证码处理: {result.message}")
    """

    def __init__(self, auto_solve: bool = True):
        """初始化集成

        Args:
            auto_solve: 是否自动处理验证码
        """
        self.hook = CaptchaHook(auto_solve=auto_solve)
        self._screenshot_dir = tempfile.gettempdir()

    def check_and_solve(
        self,
        page_url: str,
        page_html: str = None,
        page_text: str = None,
        screenshot_path: str = None,
    ) -> HookResult:
        """检查并处理验证码

        Args:
            page_url: 页面 URL
            page_html: 页面 HTML
            page_text: 页面文本
            screenshot_path: 截图路径

        Returns:
            HookResult 处理结果
        """
        context = HookContext(
            page_url=page_url,
            page_html=page_html,
            page_text=page_text,
            screenshot_path=screenshot_path,
        )

        return self.hook.after_action(context)

    def get_action_instructions(self, solve_result: SolveResult) -> Dict[str, Any]:
        """获取操作指令

        将验证码处理结果转换为浏览器操作指令。

        Args:
            solve_result: 验证码处理结果

        Returns:
            操作指令字典
        """
        if not solve_result or solve_result.status != "success":
            return {}

        action = solve_result.action
        if not action:
            return {}

        action_type = action.get("type")

        if action_type == "drag":
            return {
                "operation": "drag",
                "selector": action.get("selector", ".slider-btn"),
                "offset_x": action.get("offset_x", 0),
                "offset_y": action.get("offset_y", 0),
                "humanize": True,  # 启用人类行为模拟
            }

        elif action_type == "click":
            return {
                "operation": "click",
                "coordinates": action.get("coordinates", []),
                "humanize": True,
            }

        elif action_type == "input":
            return {
                "operation": "input",
                "selector": action.get("selector", ".captcha-input"),
                "text": action.get("text", ""),
            }

        return {}


# 便捷函数
def create_hook(auto_solve: bool = True) -> CaptchaHook:
    """创建验证码处理钩子

    Args:
        auto_solve: 是否自动处理验证码

    Returns:
        CaptchaHook 实例
    """
    return CaptchaHook(auto_solve=auto_solve)


def quick_check(html: str = None, text: str = None, url: str = None) -> bool:
    """快速检查页面是否有验证码

    Args:
        html: 页面 HTML
        text: 页面文本
        url: 页面 URL

    Returns:
        是否检测到验证码
    """
    from .monitor import check_captcha_presence

    return check_captcha_presence(html=html, text=text, url=url)
