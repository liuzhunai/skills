"""执行器基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExecutor(ABC):
    """执行器基类

    定义验证码操作执行器的标准接口。
    实际执行由 dumate-browser-use 完成。
    """

    @abstractmethod
    def execute(self, action: Dict[str, Any], page) -> bool:
        """执行操作

        Args:
            action: 操作指令
            page: 页面对象（playwright）

        Returns:
            是否执行成功
        """
        pass

    def get_javascript(self, action: Dict[str, Any]) -> str:
        """获取执行操作的 JavaScript 代码

        Args:
            action: 操作指令

        Returns:
            JavaScript 代码
        """
        return ""
