"""图片下载、缩放、格式转换。"""
import time
import uuid
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from config import OUTPUT_DIR

_CHROMA_TOLERANCE = 40


def url_to_png(url: str, max_retries: int = 3) -> str:
    """下载图片并保存为PNG，返回本地路径。超时自动重试。"""
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            filename = f"{uuid.uuid4().hex[:8]}.png"
            path = OUTPUT_DIR / filename
            img.save(str(path), "PNG")
            return str(path)
        except (requests.Timeout, requests.ConnectionError,
                requests.HTTPError, requests.RequestException) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2)
    raise RuntimeError(f"图片下载失败（已重试{max_retries}次）: {last_err}")


def resize_image(path: str, w: int, h: int) -> str:
    """扩展画布到目标尺寸，图片等比缩放居中放置，空余区域透明。"""
    img = Image.open(path)
    orig_w, orig_h = img.size
    scale = min(w / orig_w, h / orig_h)
    new_w = round(orig_w * scale)
    new_h = round(orig_h * scale)
    resized = img.resize((new_w, new_h), Image.NEAREST)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    offset_x = (w - new_w) // 2
    offset_y = (h - new_h) // 2
    if resized.mode == "RGBA":
        canvas.paste(resized, (offset_x, offset_y), resized)
    else:
        canvas.paste(resized, (offset_x, offset_y))
    new_path = str(OUTPUT_DIR / f"resized_{uuid.uuid4().hex[:8]}.png")
    canvas.save(new_path, "PNG")
    return new_path


def remove_green_background(path: str) -> str:
    """去除绿幕背景，将绿色像素变为透明（numpy矢量化）。"""
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mask = (g > r + _CHROMA_TOLERANCE) & (g > b + _CHROMA_TOLERANCE)
    arr[mask, 3] = 0
    result = Image.fromarray(arr, "RGBA")
    new_path = str(OUTPUT_DIR / f"nobg_{uuid.uuid4().hex[:8]}.png")
    result.save(new_path, "PNG")
    return new_path


_FORMAT_MAP = {"PNG": ".png", "JPEG": ".jpg", "WebP": ".webp"}


def save_as_format(path: str, fmt: str) -> str:
    """按指定格式保存图片，返回新路径。"""
    if fmt not in _FORMAT_MAP:
        raise ValueError(f"不支持的格式: {fmt}")
    img = Image.open(path)
    ext = _FORMAT_MAP[fmt]
    new_path = str(OUTPUT_DIR / f"saved_{uuid.uuid4().hex[:8]}{ext}")
    save_fmt = "JPEG" if fmt == "JPEG" else fmt
    if fmt in ("JPEG", "WebP") and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(new_path, save_fmt)
    return new_path
