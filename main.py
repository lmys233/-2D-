"""2D游戏素材生成器 - FastAPI 后端。"""
import base64
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import API_KEY, OUTPUT_DIR
from prompts import build_t2i_prompt, build_style_change_prompt
from api import generate_images, edit_single_image
from image_utils import url_to_png, resize_image, save_as_format, remove_green_background

# ============================================================
# Pydantic Models
# ============================================================
class GenerateRequest(BaseModel):
    content: str
    style: str
    size: str = "2048*2048"

class EditRequest(BaseModel):
    instruction: str
    image_url: str
    style: str
    keep_content: bool = False

class StyleChangeRequest(BaseModel):
    new_style: str
    keep_content: bool = True
    image_url: str
    gen_prompt: str = ""

class PathPayload(BaseModel):
    path: str
    width: int | None = None
    height: int | None = None
    format: str = "PNG"

# ============================================================
# Helpers
# ============================================================
def _display_url(filepath: str) -> str:
    return f"/api/outputs/{Path(filepath).name}"

def _resolve_image(image_ref: str) -> str:
    """将图片引用转为可传给DashScope的格式：URL原样返回，本地路径转base64 data URL。"""
    if image_ref.startswith("http://") or image_ref.startswith("https://"):
        return image_ref
    p = Path(image_ref)
    if not p.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_ref}")
    data = p.read_bytes()
    ext = p.suffix.lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp"}.get(ext, "image/png")
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

# ============================================================
# App
# ============================================================
app = FastAPI(title="2D游戏素材生成器")

# ============================================================
# API Routes
# ============================================================
@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    if not req.content.strip():
        return {"success": False, "error": "请输入内容描述"}
    if not req.style.strip():
        return {"success": False, "error": "请输入风格描述"}
    try:
        prompt = build_t2i_prompt(req.content.strip(), req.style.strip())
        urls = generate_images(prompt, req.size)
        paths = [remove_green_background(url_to_png(u)) for u in urls]
        images = [
            {"path": p, "url": u, "display_url": _display_url(p)}
            for p, u in zip(paths, urls)
        ]
        return {"success": True, "images": images, "prompt": prompt}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/edit")
async def api_edit(req: EditRequest):
    if not req.instruction.strip():
        return {"success": False, "error": "请输入编辑指令"}
    try:
        image_ref = _resolve_image(req.image_url)
        new_url, new_path = edit_single_image(
            req.instruction.strip(), image_ref, req.style, req.keep_content)
        final_path = remove_green_background(new_path)
        return {
            "success": True,
            "image": {
                "path": final_path,
                "url": new_url,
                "display_url": _display_url(final_path),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/style-change")
async def api_style_change(req: StyleChangeRequest):
    if not req.new_style.strip():
        return {"success": False, "error": "请输入新风格"}
    try:
        prompt = build_style_change_prompt(
            req.new_style.strip(), req.keep_content, req.gen_prompt)
        image_ref = _resolve_image(req.image_url)
        new_url, new_path = edit_single_image(
            prompt, image_ref, req.new_style.strip())
        final_path = remove_green_background(new_path)
        return {
            "success": True,
            "image": {
                "path": final_path,
                "url": new_url,
                "display_url": _display_url(final_path),
            },
            "prompt": prompt,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/resize")
async def api_resize(req: PathPayload):
    if not req.path:
        return {"success": False, "error": "没有可编辑的图片"}
    if not req.width or not req.height:
        return {"success": False, "error": "请输入有效的宽高"}
    try:
        new_path = resize_image(req.path, req.width, req.height)
        return {"success": True, "path": new_path, "display_url": _display_url(new_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/save")
async def api_save(req: PathPayload):
    if not req.path:
        return {"success": False, "error": "没有可保存的图片"}
    try:
        new_path = save_as_format(req.path, req.format)
        return {
            "success": True,
            "path": new_path,
            "display_url": _display_url(new_path),
            "filename": Path(new_path).name,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = f"upload_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        filepath.write_bytes(content)
        path_str = str(filepath)
        return {
            "success": True,
            "path": path_str,
            "display_url": _display_url(path_str),
            "filename": filename,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/outputs/{filename}")
async def serve_output(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path))

# ============================================================
# Serve Frontend (must be after API routes)
# ============================================================
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if not API_KEY:
        print("错误: 未设置 DASHSCOPE_API_KEY")
        print("请在 .env-dev 文件中填入你的 Key，格式: DASHSCOPE_API_KEY=sk-xxx")
        exit(1)
    import dashscope
    import uvicorn
    dashscope.api_key = API_KEY
    uvicorn.run(app, host="0.0.0.0", port=7860)
