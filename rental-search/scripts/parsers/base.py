"""Base parser handler using Chain of Responsibility pattern."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ParserHandler(ABC):
    """解析器处理器基类 (责任链模式)

    每个处理器负责解析特定类型的参数，并传递给下一个处理器。
    """

    def __init__(self):
        self._next_handler: Optional[ParserHandler] = None

    def set_next(self, handler: "ParserHandler") -> "ParserHandler":
        """设置下一个处理器

        Args:
            handler: 下一个处理器

        Returns:
            下一个处理器，支持链式调用
        """
        self._next_handler = handler
        return handler

    def parse(self, query: str, params: dict) -> dict:
        """解析查询

        Args:
            query: 查询字符串
            params: 已解析的参数字典

        Returns:
            更新后的参数字典
        """
        # 执行当前处理器的解析
        result = self._do_parse(query, params)

        # 传递给下一个处理器
        if self._next_handler:
            return self._next_handler.parse(query, result)

        return result

    @abstractmethod
    def _do_parse(self, query: str, params: dict) -> dict:
        """执行具体的解析逻辑

        Args:
            query: 查询字符串
            params: 已解析的参数字典

        Returns:
            更新后的参数字典
        """
        pass

    @abstractmethod
    def get_pattern(self) -> str:
        """获取此处理器匹配的模式描述"""
        pass
