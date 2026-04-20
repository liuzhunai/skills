"""验证码处理主入口"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from .detector import CaptchaDetector, CaptchaType, CaptchaInfo
from .recognizers.base import RecognizerResult
from .recognizers.slider import SliderRecognizer
from .recognizers.text import TextRecognizer
from .recognizers.click import ClickRecognizer


@dataclass
class SolveResult:
    """处理结果"""

    status: str  # success / failed
    captcha_type: str  # 验证码类型
    action: Optional[Dict[str, Any]]  # 操作指令
    confidence: float  # 置信度
    message: str  # 说明信息
    fallback: Optional[str] = None  # 降级方案


class CaptchaSolver:
    """验证码处理器

    主入口类，协调检测、识别、执行流程。
    """

    def __init__(self, use_ai_vision: bool = True):
        """初始化验证码处理器

        Args:
            use_ai_vision: 是否启用 AI 视觉识别
        """
        self.use_ai_vision = use_ai_vision

        # 初始化识别器
        self._recognizers = {
            CaptchaType.SLIDER: SliderRecognizer(),
            CaptchaType.PUZZLE: SliderRecognizer(),  # 拼图和滑动类似
            CaptchaType.TEXT: TextRecognizer(),
            CaptchaType.CALCULATE: TextRecognizer(),
            CaptchaType.CLICK: ClickRecognizer(use_ai_vision=use_ai_vision),
            CaptchaType.SELECT: ClickRecognizer(use_ai_vision=use_ai_vision),
        }

    def solve(
        self,
        screenshot_path: str = None,
        page_text: str = None,
        page_html: str = None,
        captcha_type: CaptchaType = None,
    ) -> SolveResult:
        """处理验证码

        Args:
            screenshot_path: 页面截图路径
            page_text: 页面文本内容
            page_html: 页面 HTML
            captcha_type: 指定验证码类型（可选）

        Returns:
            SolveResult 处理结果
        """
        # 1. 检测验证码类型
        if captcha_type:
            info = CaptchaInfo(
                captcha_type=captcha_type,
                selectors={},
                description="用户指定类型",
                confidence=1.0,
            )
        else:
            # 优先从 HTML 检测
            if page_html:
                info = CaptchaDetector.detect_from_html(page_html)
            # 再从文本检测
            elif page_text:
                info = CaptchaDetector.detect_from_text(page_text)
            else:
                return SolveResult(
                    status="failed",
                    captcha_type="unknown",
                    action=None,
                    confidence=0.0,
                    message="缺少检测输入",
                )

        # 2. 检查是否为计算验证码
        if info.captcha_type == CaptchaType.CALCULATE and page_text:
            result = CaptchaDetector.detect_calculation(page_text)
            if result:
                return SolveResult(
                    status="success",
                    captcha_type="calculate",
                    action={
                        "type": "input",
                        "selector": ".captcha-input, input[type='text']",
                        "text": result,
                    },
                    confidence=0.99,
                    message=f"计算结果: {result}",
                )

        # 3. 获取对应识别器
        recognizer = self._recognizers.get(info.captcha_type)
        if not recognizer:
            return SolveResult(
                status="failed",
                captcha_type=info.captcha_type.value,
                action=None,
                confidence=0.0,
                message=f"不支持的验证码类型: {info.captcha_type.value}",
                fallback="请手动完成验证",
            )

        # 4. 执行识别
        if not screenshot_path or not os.path.exists(screenshot_path):
            return SolveResult(
                status="failed",
                captcha_type=info.captcha_type.value,
                action=None,
                confidence=0.0,
                message="缺少验证码截图",
            )

        result = recognizer.recognize(screenshot_path, info.selectors)

        # 5. 构建返回结果
        if result.success:
            return SolveResult(
                status="success",
                captcha_type=info.captcha_type.value,
                action=result.action,
                confidence=result.confidence,
                message=result.message,
            )
        else:
            return SolveResult(
                status="failed",
                captcha_type=info.captcha_type.value,
                action=None,
                confidence=result.confidence,
                message=result.message,
                fallback=result.fallback,
            )

    def solve_slider(self, screenshot_path: str) -> SolveResult:
        """处理滑动验证码

        Args:
            screenshot_path: 包含滑动验证码的截图

        Returns:
            SolveResult 处理结果
        """
        return self.solve(
            screenshot_path=screenshot_path,
            captcha_type=CaptchaType.SLIDER,
        )

    def solve_click(self, screenshot_path: str, prompt: str = None) -> SolveResult:
        """处理点击验证码

        Args:
            screenshot_path: 包含点击验证码的截图
            prompt: 验证码提示（如"点击红绿灯"）

        Returns:
            SolveResult 处理结果
        """
        return self.solve(
            screenshot_path=screenshot_path,
            page_text=prompt,
            captcha_type=CaptchaType.CLICK,
        )

    def solve_text(self, screenshot_path: str) -> SolveResult:
        """处理文字验证码

        Args:
            screenshot_path: 包含文字验证码的截图

        Returns:
            SolveResult 处理结果
        """
        return self.solve(
            screenshot_path=screenshot_path,
            captcha_type=CaptchaType.TEXT,
        )

    def to_json(self, result: SolveResult) -> str:
        """将结果转换为 JSON

        Args:
            result: 处理结果

        Returns:
            JSON 字符串
        """
        return json.dumps(asdict(result), ensure_ascii=False, indent=2)


# 命令行入口
def main():
    import argparse

    parser = argparse.ArgumentParser(description="验证码处理工具")
    parser.add_argument("screenshot", help="验证码截图路径")
    parser.add_argument(
        "--type", "-t", choices=["slider", "click", "text"], help="验证码类型"
    )
    parser.add_argument("--prompt", "-p", help="点击验证码提示")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    solver = CaptchaSolver()

    type_map = {
        "slider": CaptchaType.SLIDER,
        "click": CaptchaType.CLICK,
        "text": CaptchaType.TEXT,
    }

    result = solver.solve(
        screenshot_path=args.screenshot,
        captcha_type=type_map.get(args.type),
        page_text=args.prompt,
    )

    if args.json:
        print(solver.to_json(result))
    else:
        print(f"状态: {result.status}")
        print(f"类型: {result.captcha_type}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"说明: {result.message}")
        if result.action:
            print(f"操作: {result.action}")


if __name__ == "__main__":
    main()
