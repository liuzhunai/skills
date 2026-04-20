"""识别器基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class RecognizerResult:
    """识别结果"""

    success: bool  # 是否成功
    action: Optional[Dict[str, Any]]  # 操作指令
    confidence: float  # 置信度
    message: str  # 说明信息
    fallback: Optional[str] = None  # 降级方案


class BaseRecognizer(ABC):
    """识别器基类

    定义验证码识别器的标准接口。
    """

    @abstractmethod
    def recognize(
        self, image_path: str, selectors: Dict[str, str] = None
    ) -> RecognizerResult:
        """识别验证码

        Args:
            image_path: 验证码图片路径
            selectors: 相关元素选择器

        Returns:
            RecognizerResult 识别结果
        """
        pass

    def _build_click_action(self, x: int, y: int) -> Dict[str, Any]:
        """构建点击操作

        Args:
            x: X 坐标
            y: Y 坐标

        Returns:
            操作指令
        """
        return {
            "type": "click",
            "x": x,
            "y": y,
        }

    def _build_drag_action(
        self, selector: str, offset_x: int, offset_y: int = 0
    ) -> Dict[str, Any]:
        """构建拖动操作

        Args:
            selector: 元素选择器
            offset_x: X 偏移量
            offset_y: Y 偏移量

        Returns:
            操作指令
        """
        return {
            "type": "drag",
            "selector": selector,
            "offset_x": offset_x,
            "offset_y": offset_y,
        }

    def _build_input_action(self, selector: str, text: str) -> Dict[str, Any]:
        """构建输入操作

        Args:
            selector: 元素选择器
            text: 输入文本

        Returns:
            操作指令
        """
        return {
            "type": "input",
            "selector": selector,
            "text": text,
        }

    def _build_multi_click_action(self, points: list) -> Dict[str, Any]:
        """构建多点点击操作

        Args:
            points: 坐标列表 [(x1, y1), (x2, y2), ...]

        Returns:
            操作指令
        """
        return {
            "type": "multi_click",
            "points": points,
        }
