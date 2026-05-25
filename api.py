"""DashScope API 调用。"""
import base64
import logging
from io import BytesIO

import dashscope
import requests
from PIL import Image

from config import API_KEY, T2I_MODEL, I2I_MODEL, BASE_URL
from prompts import build_edit_prompt
from image_utils import url_to_png

logger = logging.getLogger("api")


def _get_image_dimensions(image_ref: str) -> tuple[int, int]:
    """从URL或base64 data URL获取图片宽高。"""
    try:
        if image_ref.startswith("data:"):
            _, b64data = image_ref.split(",", 1)
            img_data = base64.b64decode(b64data)
        else:
            resp = requests.get(image_ref, timeout=30)
            resp.raise_for_status()
            img_data = resp.content
        img = Image.open(BytesIO(img_data))
        return img.size
    except Exception as e:
        raise RuntimeError(f"无法获取图片尺寸: {e}")


def generate_images(prompt: str, size: str) -> list[str]:
    """文生图：一次调用 n=3，返回3张URL列表。"""
    dashscope.base_http_api_url = BASE_URL
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    logger.info("[文生图] model=%s size=%s\nprompt:\n%s", T2I_MODEL, size, prompt)
    resp = dashscope.MultiModalConversation.call(
        api_key=API_KEY,
        model=T2I_MODEL,
        messages=messages,
        n=3,
        size=size,
        watermark=False,
        prompt_extend=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.code}: {resp.message}")
    try:
        return [c["image"] for c in resp.output.choices[0].message.content]
    except (AttributeError, KeyError, IndexError) as e:
        raise RuntimeError(f"API返回数据异常: {e}")


def edit_single_image(instruction: str, prev_url: str, style: str,
                       keep_content: bool = False) -> tuple[str, str]:
    """图编辑：返回 (新URL, 新本地路径)。"""
    dashscope.base_http_api_url = BASE_URL
    w, h = _get_image_dimensions(prev_url)
    prompt = build_edit_prompt(instruction, style, keep_content)
    messages = [{
        "role": "user",
        "content": [
            {"image": prev_url},
            {"text": prompt},
        ]
    }]
    logger.info("[图编辑] model=%s size=%s*%s\nprompt:\n%s", I2I_MODEL, w, h, prompt)
    resp = dashscope.MultiModalConversation.call(
        api_key=API_KEY,
        model=I2I_MODEL,
        messages=messages,
        n=1,
        size=f"{w}*{h}",
        watermark=False,
        prompt_extend=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.code}: {resp.message}")
    try:
        new_url = resp.output.choices[0].message.content[0]["image"]
    except (AttributeError, KeyError, IndexError) as e:
        raise RuntimeError(f"API返回数据异常: {e}")
    new_path = url_to_png(new_url)
    return new_url, new_path
