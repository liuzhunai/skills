"""文字验证码识别器"""

import re
import cv2
import numpy as np
from typing import Dict, Optional, List

from .base import BaseRecognizer, RecognizerResult


class TextRecognizer(BaseRecognizer):
    """文字验证码识别器

    使用 PaddleOCR + 图像预处理增强。
    支持：文字验证码、计算验证码

    识别策略：
    1. 图像预处理（去噪、增强）
    2. 多种预处理方式尝试
    3. 结果合并与修正
    """

    def __init__(self, use_paddleocr: bool = True):
        """初始化

        Args:
            use_paddleocr: 是否使用 PaddleOCR（更准确），否则使用 pytesseract
        """
        self.use_paddleocr = use_paddleocr
        self._ocr = None

    def _get_ocr(self):
        """延迟加载 OCR 引擎"""
        if self._ocr is not None:
            return self._ocr

        if self.use_paddleocr:
            try:
                from paddleocr import PaddleOCR

                self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
                return self._ocr
            except ImportError:
                pass

        # 降级到 pytesseract
        try:
            import pytesseract

            self._ocr = "pytesseract"
            return self._ocr
        except ImportError:
            return None

    def recognize(
        self, image_path: str, selectors: Dict[str, str] = None
    ) -> RecognizerResult:
        """识别文字验证码

        Args:
            image_path: 验证码图片路径
            selectors: 元素选择器

        Returns:
            RecognizerResult 识别结果
        """
        try:
            # 获取 OCR 引擎
            ocr = self._get_ocr()

            if ocr is None:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.0,
                    message="OCR 引擎未安装",
                    fallback="请安装 paddleocr 或 pytesseract",
                )

            # 多种预处理方式识别
            results = self._multi_preprocess_ocr(image_path, ocr)

            if not results:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.3,
                    message="OCR 未识别到文字",
                    fallback="请手动输入验证码",
                )

            # 选择最佳结果
            text, confidence = self._select_best_result(results)

            if not text:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.3,
                    message="OCR 识别结果无效",
                    fallback="请手动输入验证码",
                )

            # 检查是否为计算验证码
            calc_result = self._try_calculate(text)
            if calc_result:
                text = calc_result
                confidence = 0.99

            # 清理识别结果
            text = self._clean_text(text)

            # 获取输入框选择器
            input_selector = (
                selectors.get("input", ".captcha-input")
                if selectors
                else ".captcha-input"
            )

            # 构建操作指令
            action = self._build_input_action(
                selector=input_selector,
                text=text,
            )

            return RecognizerResult(
                success=True,
                action=action,
                confidence=confidence,
                message=f"识别结果: {text}",
            )

        except Exception as e:
            return RecognizerResult(
                success=False,
                action=None,
                confidence=0.0,
                message=f"识别出错: {str(e)}",
                fallback="请手动输入验证码",
            )

    def _multi_preprocess_ocr(self, image_path: str, ocr) -> List[tuple]:
        """多种预处理方式 OCR

        Args:
            image_path: 图片路径
            ocr: OCR 引擎

        Returns:
            [(text, confidence), ...] 结果列表
        """
        results = []

        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            return results

        # 预处理方式列表
        preprocessors = [
            ("original", lambda img: img),
            ("grayscale", self._to_grayscale),
            ("binary", self._to_binary),
            ("enhance", self._enhance_contrast),
            ("denoise", self._denoise),
            (
                "binary_enhance",
                lambda img: self._to_binary(self._enhance_contrast(img)),
            ),
        ]

        for name, preprocessor in preprocessors:
            try:
                processed = preprocessor(image)

                # 保存临时图片
                temp_path = f"/tmp/captcha_{name}.png"
                cv2.imwrite(temp_path, processed)

                # OCR 识别
                text, conf = self._do_ocr(temp_path, ocr)

                if text:
                    results.append((text, conf, name))

            except Exception:
                continue

        return results

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """转灰度"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def _to_binary(self, image: np.ndarray) -> np.ndarray:
        """二值化"""
        gray = self._to_grayscale(image)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """增强对比度"""
        gray = self._to_grayscale(image)

        # CLAHE 自适应直方图均衡化
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        return enhanced

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """去噪"""
        gray = self._to_grayscale(image)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        return denoised

    def _do_ocr(self, image_path: str, ocr) -> tuple:
        """执行 OCR 识别

        Args:
            image_path: 图片路径
            ocr: OCR 引擎

        Returns:
            (text, confidence) 识别的文字和置信度
        """
        if ocr == "pytesseract":
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
            data = pytesseract.image_to_data(
                image, lang="chi_sim+eng", output_type=pytesseract.Output.DICT
            )

            text = " ".join([d for d in data["text"] if d.strip()])
            conf = (
                sum([c for c in data["conf"] if c > 0])
                / len([c for c in data["conf"] if c > 0])
                / 100
                if data["conf"]
                else 0
            )

            return text.strip(), conf
        else:
            # PaddleOCR
            result = ocr.ocr(image_path, cls=True)
            if result and result[0]:
                texts = []
                confs = []
                for line in result[0]:
                    texts.append(line[1][0])
                    confs.append(line[1][1])

                text = "".join(texts)
                conf = sum(confs) / len(confs) if confs else 0

                return text, conf
            return "", 0

    def _select_best_result(self, results: List[tuple]) -> tuple:
        """选择最佳识别结果

        Args:
            results: [(text, confidence, method), ...]

        Returns:
            (text, confidence)
        """
        if not results:
            return "", 0

        # 按置信度排序
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        # 返回最高置信度的结果
        best = sorted_results[0]
        return best[0], best[1]

    def _try_calculate(self, text: str) -> Optional[str]:
        """尝试计算数学表达式

        Args:
            text: 可能包含数学表达式的文本

        Returns:
            计算结果，如果不是计算题返回 None
        """
        # 匹配数学表达式
        patterns = [
            (r"(\d+)\s*\+\s*(\d+)", lambda a, b: a + b),
            (r"(\d+)\s*-\s*(\d+)", lambda a, b: a - b),
            (r"(\d+)\s*[×xX]\s*(\d+)", lambda a, b: a * b),
            (
                r"(\d+)\s*[÷/]\s*(\d+)",
                lambda a, b: a // b if a % b == 0 else round(a / b, 2),
            ),
        ]

        for pattern, operation in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    a, b = int(match.group(1)), int(match.group(2))
                    result = operation(a, b)
                    return str(
                        int(result)
                        if isinstance(result, float) and result.is_integer()
                        else result
                    )
                except:
                    pass

        return None

    def _clean_text(self, text: str) -> str:
        """清理 OCR 结果

        Args:
            text: 原始识别结果

        Returns:
            清理后的文字
        """
        # 移除空格和特殊字符
        text = re.sub(r"[\s\-_=+]", "", text)

        # 常见 OCR 错误修正
        corrections = {
            "O": "0",
            "o": "0",
            "l": "1",
            "I": "1",
            "S": "5",
            "Z": "2",
            "B": "8",
            "G": "6",
        }

        # 仅对纯字母验证码进行修正
        if text.isalpha() and not any(c in text for c in "零一二三四五六七八九十"):
            for old, new in corrections.items():
                text = text.replace(old, new)

        return text

    def get_ocr_detail(self, image_path: str) -> Dict:
        """获取 OCR 详细信息

        用于调试和分析。

        Args:
            image_path: 图片路径

        Returns:
            详细信息字典
        """
        ocr = self._get_ocr()
        if not ocr:
            return {"error": "OCR 引擎未安装"}

        results = self._multi_preprocess_ocr(image_path, ocr)

        return {
            "results": [
                {"text": r[0], "confidence": r[1], "method": r[2]} for r in results
            ],
            "best_text": self._select_best_result(results)[0] if results else None,
        }
