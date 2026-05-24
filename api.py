"""DashScope API 调用。"""
import dashscope

from config import API_KEY, T2I_MODEL, I2I_MODEL, BASE_URL
from prompts import build_edit_prompt
from image_utils import url_to_png


def generate_images(prompt: str, size: str) -> list[str]:
    """文生图：一次调用 n=3，返回3张URL列表。"""
    dashscope.base_http_api_url = BASE_URL
    messages = [{"role": "user", "content": [{"text": prompt}]}]
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
    return [c["image"] for c in resp.output.choices[0].message.content]


def edit_single_image(instruction: str, prev_url: str, style: str,
                       transparent: bool = False) -> tuple[str, str]:
    """图编辑：返回 (新URL, 新本地路径)。"""
    dashscope.base_http_api_url = BASE_URL
    prompt = build_edit_prompt(instruction, style, transparent)
    messages = [{
        "role": "user",
        "content": [
            {"image": prev_url},
            {"text": prompt},
        ]
    }]
    resp = dashscope.MultiModalConversation.call(
        api_key=API_KEY,
        model=I2I_MODEL,
        messages=messages,
        n=1,
        watermark=False,
        prompt_extend=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.code}: {resp.message}")
    new_url = resp.output.choices[0].message.content[0]["image"]
    new_path = url_to_png(new_url)
    return new_url, new_path
