"""点击执行器"""

from typing import Dict, Any

from .base import BaseExecutor


class ClickExecutor(BaseExecutor):
    """点击执行器

    执行点击操作。
    """

    def execute(self, action: Dict[str, Any], page) -> bool:
        """执行点击

        Args:
            action: 操作指令 {"type": "click", "x": 100, "y": 200}
            page: 页面对象

        Returns:
            是否成功
        """
        try:
            x = action.get("x")
            y = action.get("y")

            if x is None or y is None:
                return False

            page.mouse.click(x, y)
            return True

        except Exception:
            return False

    def get_javascript(self, action: Dict[str, Any]) -> str:
        """获取点击的 JavaScript"""
        x = action.get("x", 0)
        y = action.get("y", 0)
        return f"document.elementFromPoint({x}, {y})?.click();"


class MultiClickExecutor(BaseExecutor):
    """多点点击执行器"""

    def execute(self, action: Dict[str, Any], page) -> bool:
        """执行多点点击

        Args:
            action: 操作指令 {"type": "multi_click", "points": [[x1, y1], [x2, y2]]}
            page: 页面对象

        Returns:
            是否成功
        """
        try:
            points = action.get("points", [])

            for point in points:
                x, y = point[0], point[1]
                page.mouse.click(x, y)
                # 添加短暂延迟，模拟人类操作
                page.wait_for_timeout(100)

            return True

        except Exception:
            return False

    def get_javascript(self, action: Dict[str, Any]) -> str:
        """获取多点点击的 JavaScript"""
        points = action.get("points", [])
        js_code = ""
        for point in points:
            x, y = point[0], point[1]
            js_code += f"document.elementFromPoint({x}, {y})?.click();\n"
        return js_code
