"""滑动验证码识别器"""

import cv2
import numpy as np
from typing import Dict, Optional, List, Tuple

from .base import BaseRecognizer, RecognizerResult


class SliderRecognizer(BaseRecognizer):
    """滑动验证码识别器

    使用 OpenCV 边缘检测 + PaddleOCR 增强。
    支持：滑动验证码、拼图验证码

    识别策略：
    1. OpenCV 边缘检测定位缺口
    2. OCR 文字检测辅助定位
    3. 模板匹配（如有滑块图）
    """

    def __init__(self, use_ocr_enhance: bool = True):
        """初始化

        Args:
            use_ocr_enhance: 是否启用 OCR 增强
        """
        self.method = cv2.TM_CCOEFF_NORMED
        self.use_ocr_enhance = use_ocr_enhance
        self._ocr = None

    def _get_ocr(self):
        """延迟加载 OCR"""
        if self._ocr is not None:
            return self._ocr

        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            return self._ocr
        except ImportError:
            return None

    def recognize(
        self, image_path: str, selectors: Dict[str, str] = None
    ) -> RecognizerResult:
        """识别滑动验证码

        流程：
        1. 加载图片
        2. OCR 识别提示文字（可选）
        3. 检测缺口位置
        4. 计算拖动距离
        5. 返回操作指令

        Args:
            image_path: 验证码截图路径
            selectors: 元素选择器

        Returns:
            RecognizerResult 识别结果
        """
        try:
            # 加载图片
            image = cv2.imread(image_path)
            if image is None:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.0,
                    message="无法加载图片",
                    fallback="请检查图片路径",
                )

            # OCR 增强识别
            ocr_hint = None
            if self.use_ocr_enhance:
                ocr_hint = self._ocr_detect(image)

            # 检测缺口位置（多种方法）
            gap_x = self._detect_gap_multi(image, ocr_hint)

            if gap_x is None:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.3,
                    message="未能检测到缺口位置",
                    fallback="尝试使用多模态 AI 识别",
                )

            # 获取滑块选择器
            slider_selector = (
                selectors.get("slider", ".slider-btn") if selectors else ".slider-btn"
            )

            # 构建操作指令
            action = self._build_drag_action(
                selector=slider_selector,
                offset_x=gap_x,
                offset_y=0,
            )

            # 构建消息
            message = f"检测到缺口位置: {gap_x}px"
            if ocr_hint:
                message += f" (OCR提示: {ocr_hint})"

            return RecognizerResult(
                success=True,
                action=action,
                confidence=0.85,
                message=message,
            )

        except Exception as e:
            return RecognizerResult(
                success=False,
                action=None,
                confidence=0.0,
                message=f"识别出错: {str(e)}",
                fallback="请手动完成验证",
            )

    def _ocr_detect(self, image: np.ndarray) -> Optional[str]:
        """OCR 检测文字

        Args:
            image: 图片数组

        Returns:
            识别到的提示文字
        """
        ocr = self._get_ocr()
        if not ocr:
            return None

        try:
            result = ocr.ocr(image, cls=True)
            if result and result[0]:
                texts = [line[1][0] for line in result[0]]
                return " ".join(texts)
        except:
            pass

        return None

    def _detect_gap_multi(
        self, image: np.ndarray, ocr_hint: str = None
    ) -> Optional[int]:
        """多种方法检测缺口位置

        Args:
            image: 图片数组
            ocr_hint: OCR 识别的提示

        Returns:
            缺口 X 坐标
        """
        # 方法1: 边缘检测
        gap_x = self._detect_gap_by_edge(image)
        if gap_x:
            return gap_x

        # 方法2: OCR 文字区域检测
        if self.use_ocr_enhance:
            gap_x = self._detect_gap_by_ocr(image)
            if gap_x:
                return gap_x

        # 方法3: 颜色差异检测
        gap_x = self._detect_gap_by_color(image)
        if gap_x:
            return gap_x

        return None

    def _detect_gap_by_edge(self, image: np.ndarray) -> Optional[int]:
        """通过边缘检测定位缺口

        Args:
            image: 图片数组

        Returns:
            缺口 X 坐标
        """
        # 转灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 边缘检测
        edges = cv2.Canny(blurred, 50, 150)

        # 检测缺口特征
        # 方法1: 检测垂直边缘线
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 2,
            threshold=100,
            minLineLength=50,
            maxLineGap=10,
        )

        if lines is not None:
            # 找最右侧的垂直线（可能是缺口边缘）
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(x1 - x2) < 5 and abs(y2 - y1) > 50:  # 垂直线
                    return x1

        # 方法2: 边缘密度变化
        edge_density = np.sum(edges, axis=0)
        diff = np.diff(edge_density.astype(float))
        if len(diff) > 0:
            gap_x = np.argmax(np.abs(diff))
            if gap_x > 50:
                return int(gap_x)

        return None

    def _detect_gap_by_ocr(self, image: np.ndarray) -> Optional[int]:
        """通过 OCR 文字区域辅助定位缺口

        PaddleOCR 返回文字边界框，可以用来：
        1. 排除文字区域（避免误判）
        2. 定位滑块位置（滑块通常在文字旁边）

        Args:
            image: 图片数组

        Returns:
            缺口 X 坐标
        """
        ocr = self._get_ocr()
        if not ocr:
            return None

        try:
            result = ocr.ocr(image, cls=True)
            if not result or not result[0]:
                return None

            # 获取所有文字区域
            text_boxes = []
            for line in result[0]:
                box = line[0]  # 四个角点坐标
                x_coords = [p[0] for p in box]
                y_coords = [p[1] for p in box]
                text_boxes.append(
                    {
                        "x_min": min(x_coords),
                        "x_max": max(x_coords),
                        "y_min": min(y_coords),
                        "y_max": max(y_coords),
                    }
                )

            # 寻找文字区域之间的空白区域（可能是缺口位置）
            if len(text_boxes) >= 2:
                # 按 x_min 排序
                text_boxes.sort(key=lambda b: b["x_min"])

                # 找最大的空白区域
                max_gap = 0
                gap_x = None

                for i in range(len(text_boxes) - 1):
                    gap = text_boxes[i + 1]["x_min"] - text_boxes[i]["x_max"]
                    if gap > max_gap:
                        max_gap = gap
                        gap_x = int(
                            (text_boxes[i]["x_max"] + text_boxes[i + 1]["x_min"]) / 2
                        )

                if gap_x and max_gap > 30:  # 空白区域足够大
                    return gap_x

        except:
            pass

        return None

    def _detect_gap_by_color(self, image: np.ndarray) -> Optional[int]:
        """通过颜色差异检测缺口

        缺口区域通常颜色与周围不同。

        Args:
            image: 图片数组

        Returns:
            缺口 X 坐标
        """
        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 计算 V 通道（亮度）的垂直投影
        v_channel = hsv[:, :, 2]
        v_projection = np.mean(v_channel, axis=0)

        # 寻找亮度突变点
        diff = np.abs(np.diff(v_projection))

        # 找到显著变化的位置
        threshold = np.mean(diff) + np.std(diff)
        significant_changes = np.where(diff > threshold)[0]

        if len(significant_changes) > 0:
            # 返回第一个显著变化点
            return int(significant_changes[0])

        return None

    def detect_gap_by_template(
        self, background: np.ndarray, slider: np.ndarray
    ) -> Optional[int]:
        """通过模板匹配检测缺口

        Args:
            background: 背景图
            slider: 滑块图

        Returns:
            缺口 X 坐标
        """
        # 转灰度
        bg_gray = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
        slider_gray = cv2.cvtColor(slider, cv2.COLOR_BGR2GRAY)

        # 模板匹配
        result = cv2.matchTemplate(bg_gray, slider_gray, self.method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > 0.8:  # 置信度阈值
            return max_loc[0]

        return None

    def get_slider_info(self, image_path: str) -> Dict:
        """获取滑动验证码详细信息

        用于调试和分析。

        Args:
            image_path: 图片路径

        Returns:
            详细信息字典
        """
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "无法加载图片"}

        info = {
            "image_size": image.shape[:2],
            "ocr_text": None,
            "gap_candidates": [],
        }

        # OCR 识别
        if self.use_ocr_enhance:
            info["ocr_text"] = self._ocr_detect(image)

        # 多种方法检测
        gap_edge = self._detect_gap_by_edge(image)
        if gap_edge:
            info["gap_candidates"].append({"method": "edge", "x": gap_edge})

        gap_ocr = self._detect_gap_by_ocr(image)
        if gap_ocr:
            info["gap_candidates"].append({"method": "ocr", "x": gap_ocr})

        gap_color = self._detect_gap_by_color(image)
        if gap_color:
            info["gap_candidates"].append({"method": "color", "x": gap_color})

        return info
