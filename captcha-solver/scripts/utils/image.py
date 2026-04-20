"""图像处理工具"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ImageProcessor:
    """图像处理工具类

    提供验证码图像预处理功能。
    """

    @staticmethod
    def load_image(path: str) -> Optional[np.ndarray]:
        """加载图片

        Args:
            path: 图片路径

        Returns:
            图片数组
        """
        return cv2.imread(path)

    @staticmethod
    def to_gray(image: np.ndarray) -> np.ndarray:
        """转灰度图

        Args:
            image: 图片数组

        Returns:
            灰度图
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        """去噪

        Args:
            image: 图片数组

        Returns:
            去噪后的图片
        """
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    @staticmethod
    def binarize(image: np.ndarray, threshold: int = 127) -> np.ndarray:
        """二值化

        Args:
            image: 灰度图
            threshold: 阈值

        Returns:
            二值图
        """
        _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        return binary

    @staticmethod
    def detect_edges(image: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
        """边缘检测

        Args:
            image: 灰度图
            low: 低阈值
            high: 高阈值

        Returns:
            边缘图
        """
        return cv2.Canny(image, low, high)

    @staticmethod
    def find_contours(image: np.ndarray) -> list:
        """查找轮廓

        Args:
            image: 二值图

        Returns:
            轮廓列表
        """
        contours, _ = cv2.findContours(
            image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        return contours

    @staticmethod
    def crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """裁剪图片

        Args:
            image: 图片数组
            x, y, w, h: 裁剪区域

        Returns:
            裁剪后的图片
        """
        return image[y : y + h, x : x + w]

    @staticmethod
    def resize(image: np.ndarray, width: int, height: int) -> np.ndarray:
        """调整大小

        Args:
            image: 图片数组
            width: 目标宽度
            height: 目标高度

        Returns:
            调整后的图片
        """
        return cv2.resize(image, (width, height))

    @staticmethod
    def save(image: np.ndarray, path: str) -> bool:
        """保存图片

        Args:
            image: 图片数组
            path: 保存路径

        Returns:
            是否成功
        """
        return cv2.imwrite(path, image)
