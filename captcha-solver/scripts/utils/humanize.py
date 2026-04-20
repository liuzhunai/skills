"""人类行为模拟"""

import random
import time
from typing import List, Tuple


class HumanBehavior:
    """人类行为模拟工具

    提供模拟真实人类操作的方法。
    """

    @staticmethod
    def random_delay(min_ms: int = 50, max_ms: int = 200) -> None:
        """随机延迟

        Args:
            min_ms: 最小延迟（毫秒）
            max_ms: 最大延迟（毫秒）
        """
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        time.sleep(delay)

    @staticmethod
    def generate_mouse_trajectory(
        start_x: float, start_y: float, end_x: float, end_y: float, steps: int = 20
    ) -> List[Tuple[float, float]]:
        """生成人类化的鼠标轨迹

        特点：
        - 非匀速运动
        - 轨迹略有弯曲
        - 添加随机抖动

        Args:
            start_x, start_y: 起始坐标
            end_x, end_y: 结束坐标
            steps: 轨迹点数

        Returns:
            轨迹点列表
        """
        trajectory = []

        # 使用贝塞尔曲线生成轨迹
        control_points = HumanBehavior._generate_bezier_control_points(
            start_x, start_y, end_x, end_y
        )

        for i in range(1, steps + 1):
            t = i / steps

            # 贝塞尔曲线插值
            x, y = HumanBehavior._bezier_interpolate(control_points, t)

            # 添加随机抖动
            if 0.1 < t < 0.9:
                x += random.uniform(-1, 1)
                y += random.uniform(-0.5, 0.5)

            trajectory.append((x, y))

        return trajectory

    @staticmethod
    def _generate_bezier_control_points(
        start_x: float, start_y: float, end_x: float, end_y: float
    ) -> List[Tuple[float, float]]:
        """生成贝塞尔曲线控制点

        Args:
            start_x, start_y: 起点
            end_x, end_y: 终点

        Returns:
            控制点列表
        """
        # 在起点和终点之间随机生成控制点
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2

        # 添加随机偏移
        offset_x = (end_x - start_x) * random.uniform(-0.1, 0.1)
        offset_y = (end_y - start_y) * random.uniform(-0.2, 0.2)

        return [
            (start_x, start_y),
            (mid_x + offset_x, mid_y + offset_y),
            (end_x, end_y),
        ]

    @staticmethod
    def _bezier_interpolate(
        points: List[Tuple[float, float]], t: float
    ) -> Tuple[float, float]:
        """贝塞尔曲线插值

        Args:
            points: 控制点
            t: 参数 [0, 1]

        Returns:
            插值点坐标
        """
        n = len(points) - 1
        x = 0.0
        y = 0.0

        for i, (px, py) in enumerate(points):
            # 二项式系数
            coef = HumanBehavior._binomial(n, i) * (t**i) * ((1 - t) ** (n - i))
            x += coef * px
            y += coef * py

        return x, y

    @staticmethod
    def _binomial(n: int, k: int) -> int:
        """计算二项式系数

        Args:
            n: 总数
            k: 选择数

        Returns:
            二项式系数
        """
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1

        result = 1
        for i in range(min(k, n - k)):
            result = result * (n - i) // (i + 1)

        return result

    @staticmethod
    def generate_typing_delays(text: str) -> List[float]:
        """生成打字延迟

        模拟真实打字速度，每个字符的延迟不同。

        Args:
            text: 要输入的文本

        Returns:
            每个字符的延迟列表（秒）
        """
        delays = []

        for i, char in enumerate(text):
            # 基础延迟
            base_delay = random.uniform(0.05, 0.15)

            # 根据字符类型调整
            if char.isupper():
                base_delay += 0.05  # 大写字母稍慢
            elif char in "!@#$%^&*()":
                base_delay += 0.1  # 特殊字符更慢

            # 偶尔停顿
            if random.random() < 0.1:
                base_delay += random.uniform(0.2, 0.5)

            delays.append(base_delay)

        return delays
