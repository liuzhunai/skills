"""输入执行器"""

from typing import Dict, Any

from .base import BaseExecutor


class InputExecutor(BaseExecutor):
    """输入执行器

    执行文本输入操作。
    """

    def execute(self, action: Dict[str, Any], page) -> bool:
        """执行输入

        Args:
            action: 操作指令 {
                "type": "input",
                "selector": ".captcha-input",
                "text": "abc123"
            }
            page: 页面对象

        Returns:
            是否成功
        """
        try:
            selector = action.get("selector")
            text = action.get("text", "")

            if not selector or not text:
                return False

            # 获取输入框
            element = page.query_selector(selector)
            if not element:
                return False

            # 清空并输入
            element.fill("")
            element.type(text, delay=50)  # 模拟人类输入速度

            return True

        except Exception:
            return False

    def get_javascript(self, action: Dict[str, Any]) -> str:
        """获取输入的 JavaScript"""
        selector = action.get("selector", "")
        text = action.get("text", "")

        return f"""
        (function() {{
            const input = document.querySelector('{selector}');
            if (!input) return false;
            
            input.value = '{text}';
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            return true;
        }})();
        """
