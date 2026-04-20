"""点击验证码识别器"""

import os
import json
import base64
import re
from typing import Dict, List, Tuple, Optional

from .base import BaseRecognizer, RecognizerResult


class ClickRecognizer(BaseRecognizer):
    """点击验证码识别器

    使用多模态 AI 识别目标位置。
    支持：点击验证码、选择验证码

    识别方式：
    1. 内置多模态能力（DuMate）- 直接识别图片
    2. 外部 AI 视觉 API - 需要配置
    """

    def __init__(self, use_ai_vision: bool = True, api_config: Dict = None):
        """初始化

        Args:
            use_ai_vision: 是否使用 AI 视觉
            api_config: API 配置（endpoint, key）
        """
        self.use_ai_vision = use_ai_vision
        self.api_config = api_config or {}

    def recognize(
        self, image_path: str, selectors: Dict[str, str] = None, prompt: str = None
    ) -> RecognizerResult:
        """识别点击验证码

        Args:
            image_path: 验证码图片路径
            selectors: 元素选择器
            prompt: 验证码提示（如"点击红绿灯"）

        Returns:
            RecognizerResult 识别结果
        """
        if not self.use_ai_vision:
            return RecognizerResult(
                success=False,
                action=None,
                confidence=0.0,
                message="AI 视觉识别未启用",
                fallback="请启用 AI 视觉或手动完成验证",
            )

        try:
            # 调用 AI 视觉识别
            result = self._call_ai_vision(image_path, prompt)

            if not result:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.3,
                    message="AI 视觉识别失败",
                    fallback="请手动完成验证",
                )

            # 解析返回的坐标
            points = self._parse_coordinates(result)

            if not points:
                return RecognizerResult(
                    success=False,
                    action=None,
                    confidence=0.3,
                    message="无法解析坐标",
                    fallback="请手动完成验证",
                )

            # 构建操作指令
            if len(points) == 1:
                action = self._build_click_action(points[0][0], points[0][1])
            else:
                action = self._build_multi_click_action(points)

            return RecognizerResult(
                success=True,
                action=action,
                confidence=0.7,
                message=f"识别到 {len(points)} 个目标位置",
            )

        except Exception as e:
            return RecognizerResult(
                success=False,
                action=None,
                confidence=0.0,
                message=f"识别出错: {str(e)}",
                fallback="请手动完成验证",
            )

    def _call_ai_vision(self, image_path: str, prompt: str = None) -> Optional[Dict]:
        """调用 AI 视觉识别

        优先级：
        1. 使用内置多模态能力（通过 baidu-content-parser）
        2. 使用外部 API

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            识别结果
        """
        # 构建 prompt
        if not prompt:
            prompt = "请分析这张验证码图片"

        analysis_prompt = f"""{prompt}

请识别需要点击的目标位置，返回 JSON 格式：
{{
    "description": "描述验证码内容",
    "target": "需要点击的目标（如红绿灯、斑马线等）",
    "points": [[x1, y1], [x2, y2], ...]
}}

注意：
1. 坐标是相对于图片左上角的像素坐标
2. 如果有多个目标需要点击，返回所有坐标
3. 只返回 JSON，不要其他说明"""

        # 方式1: 使用内置多模态能力（推荐）
        result = self._call_builtin_vision(image_path, analysis_prompt)
        if result:
            return result

        # 方式2: 使用外部 API
        if self.api_config.get("endpoint"):
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            return self._call_external_api(image_data, analysis_prompt)

        return None

    def _call_builtin_vision(self, image_path: str, prompt: str) -> Optional[Dict]:
        """使用内置多模态能力识别图片

        通过 baidu-content-parser skill 或直接读取图片。

        Args:
            image_path: 图片路径
            prompt: 分析提示

        Returns:
            识别结果
        """
        # 这个方法需要由调用方（DuMate）来实现
        # 因为只有 DuMate 有多模态能力
        #
        # 使用方式：
        # 1. 调用方使用 read 工具读取图片
        # 2. 调用方分析图片内容
        # 3. 调用方返回坐标
        #
        # 这里返回一个标记，让调用方知道需要处理图片
        return {
            "need_vision_analysis": True,
            "image_path": image_path,
            "prompt": prompt,
            "message": "请使用多模态能力分析图片并返回坐标",
        }

    def _call_external_api(self, image_data: str, prompt: str) -> Optional[Dict]:
        """调用外部 AI 视觉 API

        Args:
            image_data: Base64 图片数据
            prompt: 提示词

        Returns:
            API 结果
        """
        import requests

        try:
            response = requests.post(
                self.api_config["endpoint"],
                headers={
                    "Authorization": f"Bearer {self.api_config.get('key', '')}",
                    "Content-Type": "application/json",
                },
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    },
                                },
                            ],
                        }
                    ]
                },
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        return None

    def _parse_coordinates(self, result: Dict) -> List[Tuple[int, int]]:
        """解析坐标

        Args:
            result: 识别结果

        Returns:
            坐标列表 [(x1, y1), (x2, y2), ...]
        """
        points = []

        # 如果需要视觉分析，返回空（由调用方处理）
        if result.get("need_vision_analysis"):
            return []

        # 尝试从不同格式解析
        if "points" in result:
            for point in result["points"]:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    points.append((int(point[0]), int(point[1])))

        elif "coordinates" in result:
            for coord in result["coordinates"]:
                if "x" in coord and "y" in coord:
                    points.append((int(coord["x"]), int(coord["y"])))

        # 尝试从文本中解析 JSON
        if not points and "content" in result:
            try:
                # 提取 JSON
                content = result["content"]
                json_match = re.search(r'\{[^{}]*"points"[^{}]*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    if "points" in data:
                        for point in data["points"]:
                            if isinstance(point, (list, tuple)) and len(point) >= 2:
                                points.append((int(point[0]), int(point[1])))
            except:
                pass

        return points

    @staticmethod
    def parse_vision_response(response_text: str) -> List[Tuple[int, int]]:
        """解析多模态 AI 的响应文本

        用于解析 DuMate 分析图片后返回的文本。

        Args:
            response_text: AI 响应文本

        Returns:
            坐标列表
        """
        points = []

        # 尝试提取 JSON
        try:
            json_match = re.search(
                r'\{[^{}]*"points"[^{}]*\}', response_text, re.DOTALL
            )
            if json_match:
                data = json.loads(json_match.group())
                if "points" in data:
                    for point in data["points"]:
                        if isinstance(point, (list, tuple)) and len(point) >= 2:
                            points.append((int(point[0]), int(point[1])))
        except:
            pass

        # 尝试提取坐标格式 (x, y) 或 [x, y]
        if not points:
            coord_pattern = r"[\(\[]?\s*(\d+)\s*[,\s]\s*(\d+)\s*[\)\]]?"
            matches = re.findall(coord_pattern, response_text)
            for match in matches:
                points.append((int(match[0]), int(match[1])))

        return points


# 使用说明
"""
## 使用 DuMate 多模态能力识别验证码

当 ClickRecognizer 返回 need_vision_analysis=True 时，
由 DuMate 使用 read 工具读取图片并分析：

1. 使用 read 工具读取验证码图片
2. 分析图片内容，识别需要点击的目标
3. 返回坐标 JSON

示例流程：
```python
# Step 1: 调用识别器
recognizer = ClickRecognizer()
result = recognizer.recognize("captcha.png", prompt="点击红绿灯")

# Step 2: 如果需要视觉分析
if result.action is None and hasattr(result, 'need_vision_analysis'):
    # DuMate 使用 read 工具读取图片
    # DuMate 分析图片，返回坐标
    # 例如返回: {"points": [[45, 120], [89, 120], [133, 120]]}
    
    # Step 3: 解析响应
    points = ClickRecognizer.parse_vision_response(response_text)
    
    # Step 4: 构建操作指令
    action = {
        "type": "multi_click",
        "points": points
    }
```
"""
