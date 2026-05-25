"""图片下载、缩放、格式转换。"""
import uuid
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from config import OUTPUT_DIR


def url_to_png(url: str) -> str:
    """下载图片并保存为PNG，返回本地路径。"""
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    filename = f"{uuid.uuid4().hex[:8]}.png"
    path = OUTPUT_DIR / filename
    img.save(str(path), "PNG")
    return str(path)


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


def save_as_format(path: str, fmt: str) -> str:
    """按指定格式保存图片，返回新路径。"""
    img = Image.open(path)
    ext = {"PNG": ".png", "JPEG": ".jpg", "WebP": ".webp"}[fmt]
    new_path = str(OUTPUT_DIR / f"saved_{uuid.uuid4().hex[:8]}{ext}")
    save_fmt = "JPEG" if fmt == "JPEG" else fmt
    if fmt in ("JPEG", "WebP") and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(new_path, save_fmt)
    return new_path
