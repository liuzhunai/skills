"""拖动执行器"""

import random
import time
from typing import Dict, Any, List, Tuple

from .base import BaseExecutor


class DragExecutor(BaseExecutor):
    """拖动执行器

    执行拖动操作，包含人类行为模拟。
    """

    def execute(self, action: Dict[str, Any], page) -> bool:
        """执行拖动

        Args:
            action: 操作指令 {
                "type": "drag",
                "selector": ".slider-btn",
                "offset_x": 120,
                "offset_y": 0
            }
            page: 页面对象

        Returns:
            是否成功
        """
        try:
            selector = action.get("selector")
            offset_x = action.get("offset_x", 0)
            offset_y = action.get("offset_y", 0)

            if not selector:
                return False

            # 获取元素
            element = page.query_selector(selector)
            if not element:
                return False

            # 获取元素位置
            box = element.bounding_box()
            if not box:
                return False

            # 计算起始和结束位置
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            end_x = start_x + offset_x
            end_y = start_y + offset_y

            # 生成人类化轨迹
            trajectory = self._generate_human_trajectory(start_x, start_y, end_x, end_y)

            # 执行拖动
            page.mouse.move(start_x, start_y)
            page.mouse.down()

            for x, y in trajectory:
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.005, 0.015))

            page.mouse.up()

            return True

        except Exception:
            return False

    def _generate_human_trajectory(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        steps: int = 20,
    ) -> List[Tuple[float, float]]:
        """生成人类化的拖动轨迹

        模拟真实人类的拖动行为：
        - 非匀速运动（开始快，结束慢）
        - 添加随机抖动
        - 轨迹略有弯曲

        Args:
            start_x, start_y: 起始坐标
            end_x, end_y: 结束坐标
            steps: 轨迹点数

        Returns:
            轨迹点列表 [(x1, y1), (x2, y2), ...]
        """
        trajectory = []

        for i in range(1, steps + 1):
            # 使用缓动函数（ease-out）
            t = i / steps
            ease_t = 1 - (1 - t) ** 3  # ease-out cubic

            # 计算基础位置
            x = start_x + (end_x - start_x) * ease_t
            y = start_y + (end_y - start_y) * ease_t

            # 添加随机抖动
            if 0.1 < t < 0.9:
                jitter_x = random.uniform(-2, 2)
                jitter_y = random.uniform(-1, 1)
                x += jitter_x
                y += jitter_y

            trajectory.append((x, y))

        return trajectory

    def get_javascript(self, action: Dict[str, Any]) -> str:
        """获取拖动的 JavaScript"""
        selector = action.get("selector", "")
        offset_x = action.get("offset_x", 0)

        return f"""
        (function() {{
            const slider = document.querySelector('{selector}');
            if (!slider) return false;
            
            const rect = slider.getBoundingClientRect();
            const startX = rect.left + rect.width / 2;
            const startY = rect.top + rect.height / 2;
            
            // 创建并触发鼠标事件
            const mousedown = new MouseEvent('mousedown', {{
                bubbles: true,
                clientX: startX,
                clientY: startY
            }});
            slider.dispatchEvent(mousedown);
            
            const mousemove = new MouseEvent('mousemove', {{
                bubbles: true,
                clientX: startX + {offset_x},
                clientY: startY
            }});
            document.dispatchEvent(mousemove);
            
            const mouseup = new MouseEvent('mouseup', {{
                bubbles: true,
                clientX: startX + {offset_x},
                clientY: startY
            }});
            document.dispatchEvent(mouseup);
            
            return true;
        }})();
        """
