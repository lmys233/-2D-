"""2D游戏素材生成器 - UI + 回调 + 入口。"""
import dashscope
import gradio as gr

from config import API_KEY, SIZE_OPTIONS, OUTPUT_DIR
from prompts import build_t2i_prompt, build_style_change_prompt
from api import generate_images, edit_single_image
from image_utils import url_to_png, resize_image, save_as_format

# ============================================================
# 导航辅助
# ============================================================
def _show(page_name: str):
    return (
        gr.update(visible=(page_name == "home")),
        gr.update(visible=(page_name == "generate")),
        gr.update(visible=(page_name == "edit")),
    )

def _triple_img(paths: list) -> tuple:
    return (
        paths[0] if len(paths) > 0 else None,
        paths[1] if len(paths) > 1 else None,
        paths[2] if len(paths) > 2 else None,
    )

def _radio_for(count: int):
    choices = [f"图{i + 1}" for i in range(count)]
    return gr.update(choices=choices, value=choices[0])

STEPS = [
    ("home", "选择模式"),
    ("generate", "图片生成"),
    ("edit", "图片编辑"),
    ("save", "图片保存"),
]

def render_steps(current_page: str) -> str:
    """生成左侧流程条HTML，带连接线和圆点。"""
    current_idx = next(
        (i for i, (s, _) in enumerate(STEPS) if s == current_page), 0)

    items = []
    for i, (sname, label) in enumerate(STEPS):
        if i < current_idx:
            dot_color = "#4caf50"
            dot_char = "✓"
            bg = "#e8f5e9"
            text_color = "#2e7d32"
            line_color = "#4caf50"
        elif i == current_idx:
            dot_color = "#1976d2"
            dot_char = "●"
            bg = "#e3f2fd"
            text_color = "#0d47a1"
            line_color = "#e0e0e0"
        else:
            dot_color = "#e0e0e0"
            dot_char = ""
            bg = "transparent"
            text_color = "#bdbdbd"
            line_color = "#e0e0e0"

        line_html = ""
        if i < len(STEPS) - 1:
            line_html = (
                f'<div style="width:2px;height:22px;'
                f'background:{line_color};margin:0 auto;"></div>'
            )

        items.append(f"""
        <div style="display:flex;align-items:stretch;gap:0;">
            <div style="display:flex;flex-direction:column;align-items:center;
                        width:30px;flex-shrink:0;">
                <div style="width:28px;height:28px;border-radius:50%;
                            background:{dot_color};display:flex;
                            align-items:center;justify-content:center;
                            color:#fff;font-size:13px;font-weight:bold;
                            flex-shrink:0;line-height:1;">
                    {dot_char}
                </div>
                {line_html}
            </div>
            <div style="padding:4px 10px;margin-bottom:2px;border-radius:4px;
                        background:{bg};color:{text_color};
                        font-size:13px;font-weight:{'bold' if i == current_idx else 'normal'};
                        flex:1;align-self:center;">
                {label}
            </div>
        </div>
        """)

    html = '<div style="padding:20px 10px;font-size:14px;">'
    html += '<div style="font-weight:bold;margin-bottom:16px;color:#333;">流程进度</div>'
    html += "".join(items)
    html += '</div>'
    return html

# ============================================================
# 回调: 首页导航
# ============================================================
def nav_to_generate():
    return ("generate",) + _show("generate") + (
        render_steps("generate"),
        "",
        gr.update(choices=["图1"], value="图1"),
        "", "", "2048*2048", False,
        [], [],
        "", "", "",
        False,
    )

def nav_to_edit_upload():
    return ("edit",) + _show("edit") + (
        render_steps("edit"),
    )

# ============================================================
# 回调: 生成页
# ============================================================
def _empty_gen_result(msg):
    return (None, None, None, msg, gr.update(),
            [], [], "", "", "", False)

def on_generate(content, style, size, transparent):
    if not content or not content.strip():
        return _empty_gen_result("请输入内容描述")
    if not style or not style.strip():
        return _empty_gen_result("请输入风格描述")

    try:
        prompt = build_t2i_prompt(content.strip(), style.strip(), transparent)
        urls = generate_images(prompt, size)
        paths = [url_to_png(u) for u in urls]

        return _triple_img(paths) + (
            f"生成成功，共{len(urls)}张",
            _radio_for(len(urls)),
            paths, urls,
            prompt, content.strip(), style.strip(),
            transparent,
        )
    except Exception as e:
        return _empty_gen_result(f"生成失败: {e}")

def on_regenerate(content, style, size, transparent):
    return on_generate(content, style, size, transparent)

def on_reset_gen():
    return (
        None, None, None, "",
        gr.update(choices=["图1"], value="图1"),
        "", "", "2048*2048", False,
        [], [],
        "", "", "",
        False,
    )

def on_enter_edit(selected, gen_paths, gen_urls, gen_prompt, gen_style,
                  gen_transparent):
    if not gen_paths or not gen_urls:
        return ("generate",) + _show("generate") + (
            False,
            render_steps("generate"),
            None,
            "", "", "", "",
            "", "", "",
            gr.update(visible=False),
            "", False,
        )
    idx = 0
    if selected:
        idx = int(selected[1]) - 1
        if idx >= len(gen_paths):
            idx = 0

    return ("edit",) + _show("edit") + (
        False,
        render_steps("edit"),
        gen_paths[idx],
        gen_paths[idx], gen_urls[idx],
        "", "",
        gen_style, gen_prompt,
        "",
        gr.update(visible=False),
        "", gen_transparent,
    )

# ============================================================
# 回调: 编辑页
# ============================================================
def on_edit_submit(instruction, edit_url, edit_style, edit_path, edit_prompt,
                   gen_transparent):
    if not instruction or not instruction.strip():
        return (
            None, "请输入编辑指令", edit_path, edit_url,
            edit_style, edit_prompt, gr.update(visible=False),
        )
    try:
        new_url, new_path = edit_single_image(
            instruction.strip(), edit_url, edit_style, gen_transparent)
        return (
            new_path,
            "编辑成功",
            new_path, new_url,
            edit_style, edit_prompt,
            gr.update(visible=True),
        )
    except Exception as e:
        return (
            edit_path, f"编辑失败: {e}",
            edit_path, edit_url,
            edit_style, edit_prompt,
            gr.update(visible=False),
        )

def on_undo(prev_path, prev_url, edit_style, edit_prompt):
    if not prev_path:
        return (None, "没有可撤销的编辑", prev_path or "", prev_url or "",
                edit_style, edit_prompt, gr.update(visible=False))
    return (
        prev_path, "已撤销",
        prev_path, prev_url,
        edit_style, edit_prompt,
        gr.update(visible=False),
    )

def on_save_image(edit_path, save_format):
    if not edit_path:
        return None, "没有可保存的图片"
    try:
        saved = save_as_format(edit_path, save_format)
        return saved, f"已保存: {saved}"
    except Exception as e:
        return None, f"保存失败: {e}"

def on_resize_image(edit_path, w, h, edit_url, edit_style, edit_prompt):
    if not edit_path:
        return (None, "没有可编辑的图片", edit_path, edit_url,
                edit_style, edit_prompt)
    try:
        new_path = resize_image(edit_path, int(w), int(h))
        return (new_path, f"尺寸已改为 {w}x{h}",
                new_path, edit_url, edit_style, edit_prompt)
    except Exception as e:
        return (edit_path, f"改尺寸失败: {e}",
                edit_path, edit_url, edit_style, edit_prompt)

def on_style_change(edit_path, edit_url, new_style, keep_content,
                    edit_style, edit_prompt, gen_transparent):
    if not edit_path or not edit_url or not new_style.strip():
        return (edit_path, "请输入新风格", edit_path, edit_url,
                edit_style, edit_prompt)
    try:
        prompt = build_style_change_prompt(
            new_style.strip(), keep_content, edit_prompt)
        new_url, new_path = edit_single_image(
            prompt, edit_url, new_style.strip(), gen_transparent)
        return (
            new_path, f"风格已改为 {new_style.strip()}",
            new_path, new_url,
            new_style.strip(), prompt,
        )
    except Exception as e:
        return (edit_path, f"改风格失败: {e}",
                edit_path, edit_url, edit_style, edit_prompt)

def on_upload_for_edit(uploaded_file):
    if uploaded_file is None:
        return None, "", ""
    path = uploaded_file if isinstance(uploaded_file, str) else uploaded_file.name
    return path, path, ""

# ============================================================
# UI 构建
# ============================================================
def create_ui():
    with gr.Blocks(title="2D游戏素材生成器") as demo:

        # ========== State ==========
        page = gr.State("home")

        gen_paths = gr.State([])
        gen_urls = gr.State([])
        gen_prompt = gr.State("")
        gen_content_st = gr.State("")
        gen_style_st = gr.State("")
        gen_transparent_st = gr.State(False)

        edit_path = gr.State("")
        edit_url = gr.State("")
        prev_path = gr.State("")
        prev_url = gr.State("")
        edit_style = gr.State("")
        edit_prompt = gr.State("")

        with gr.Row():
            # ===== 左侧流程条 =====
            with gr.Column(scale=1, min_width=180):
                step_html = gr.HTML(render_steps("home"))

            # ===== 右侧主内容 =====
            with gr.Column(scale=5):
                # ========== 首页 ==========
                with gr.Column(visible=True) as home_col:
                        gr.Markdown("# 2D游戏素材生成器")
                        gr.Markdown("### 选择模式")
                        with gr.Row():
                            gen_nav_btn = gr.Button(
                                "图片生成", variant="primary", size="lg")
                            edit_nav_btn = gr.Button(
                                "图片编辑", variant="secondary", size="lg")

                # ========== 生成页 ==========
                with gr.Column(visible=False) as generate_col:
                        gr.Markdown("## 图片生成")
                        with gr.Row():
                            with gr.Column(scale=1):
                                gen_content = gr.Textbox(
                                    label="内容描述",
                                    placeholder="描述你想要生成的图片内容...",
                                    lines=3,
                                )
                                gen_style = gr.Textbox(
                                    label="风格描述",
                                    placeholder="例如：像素风格、水墨风格、水彩风格",
                                    lines=1,
                                )
                                gen_size = gr.Dropdown(
                                    label="图片尺寸", choices=SIZE_OPTIONS,
                                    value="2048*2048", interactive=True,
                                )
                                gen_transparent = gr.Checkbox(
                                    label="透明背景", value=False)
                                with gr.Row():
                                    gen_btn = gr.Button(
                                        "生成图像", variant="primary")
                                    regen_btn = gr.Button(
                                        "重新生成", variant="secondary")
                                reset_gen_btn = gr.Button(
                                    "重置", variant="stop", size="sm")
                                back_gen_btn = gr.Button(
                                    "← 返回首页", size="sm")

                            with gr.Column(scale=2):
                                gen_status = gr.Textbox(
                                    label="状态", interactive=False)
                                with gr.Row():
                                    gen_img1 = gr.Image(
                                        label="图1", interactive=False)
                                    gen_img2 = gr.Image(
                                        label="图2", interactive=False)
                                    gen_img3 = gr.Image(
                                        label="图3", interactive=False)
                                gen_select = gr.Dropdown(
                                    label="选择编辑目标",
                                    choices=["图1"], value="图1",
                                    interactive=True,
                                )
                                enter_edit_btn = gr.Button(
                                    "进入编辑 →", variant="primary", size="lg")

                # ========== 编辑页 ==========
                with gr.Column(visible=False) as edit_col:
                        with gr.Row():
                            gr.Markdown("## 图片编辑")
                            back_edit_btn = gr.Button(
                                "← 返回首页", size="sm")

                        with gr.Row():
                            with gr.Column(scale=1):
                                edit_upload = gr.File(
                                    label="上传新图片（或从生成页进入已加载）")
                                edit_image = gr.Image(
                                    label="当前图片", interactive=False)
                                edit_status = gr.Textbox(
                                    label="状态", interactive=False)

                            with gr.Column(scale=1):
                                gr.Markdown("### 编辑操作")
                                edit_instruction = gr.Textbox(
                                    label="编辑指令",
                                    placeholder="描述你要修改的内容...",
                                    lines=2,
                                )
                                with gr.Row():
                                    edit_submit_btn = gr.Button(
                                        "提交编辑", variant="primary")
                                    undo_btn = gr.Button(
                                        "撤销编辑", variant="stop",
                                        visible=False)

                                gr.Markdown("---")
                                gr.Markdown("### 保存图片")
                                with gr.Row():
                                    save_format = gr.Dropdown(
                                        choices=["PNG", "JPEG", "WebP"],
                                        value="PNG", label="格式", scale=1,
                                    )
                                    save_btn = gr.Button(
                                        "保存", variant="secondary", scale=1)
                                save_file = gr.File(label="下载文件")

                                gr.Markdown("---")
                                gr.Markdown("### 改尺寸")
                                with gr.Row():
                                    resize_w = gr.Number(
                                        label="宽(px)", value=512, precision=0)
                                    resize_h = gr.Number(
                                        label="高(px)", value=512, precision=0)
                                    resize_btn = gr.Button(
                                        "应用尺寸", variant="secondary")

                                gr.Markdown("---")
                                gr.Markdown("### 改风格")
                                new_style_input = gr.Textbox(
                                    label="新风格",
                                    placeholder="例如：水墨风格", lines=1,
                                )
                                keep_content_cb = gr.Checkbox(
                                    label="保持画面内容不变", value=True)
                                style_btn = gr.Button(
                                    "应用风格", variant="secondary")

        # ============================================================
        # 事件绑定
        # ============================================================

        # -- 首页导航 --
        gen_nav_btn.click(
            fn=nav_to_generate, inputs=[],
            outputs=[
                page, home_col, generate_col, edit_col, step_html,
                gen_status, gen_select,
                gen_content, gen_style, gen_size, gen_transparent,
                gen_paths, gen_urls,
                gen_prompt, gen_content_st, gen_style_st, gen_transparent_st,
            ],
        )
        edit_nav_btn.click(
            fn=nav_to_edit_upload, inputs=[],
            outputs=[page, home_col, generate_col, edit_col, step_html],
        )

        # -- 生成页 --
        gen_btn.click(
            fn=on_generate,
            inputs=[gen_content, gen_style, gen_size, gen_transparent],
            outputs=[
                gen_img1, gen_img2, gen_img3, gen_status, gen_select,
                gen_paths, gen_urls,
                gen_prompt, gen_content_st, gen_style_st, gen_transparent_st,
            ],
        )
        regen_btn.click(
            fn=on_regenerate,
            inputs=[gen_content, gen_style, gen_size, gen_transparent],
            outputs=[
                gen_img1, gen_img2, gen_img3, gen_status, gen_select,
                gen_paths, gen_urls,
                gen_prompt, gen_content_st, gen_style_st, gen_transparent_st,
            ],
        )
        reset_gen_btn.click(
            fn=on_reset_gen, inputs=[],
            outputs=[
                gen_img1, gen_img2, gen_img3, gen_status, gen_select,
                gen_content, gen_style, gen_size, gen_transparent,
                gen_paths, gen_urls,
                gen_prompt, gen_content_st, gen_style_st, gen_transparent_st,
            ],
        )
        enter_edit_btn.click(
            fn=on_enter_edit,
            inputs=[gen_select, gen_paths, gen_urls,
                    gen_prompt, gen_style_st, gen_transparent_st],
            outputs=[
                page, home_col, generate_col, edit_col, step_html,
                edit_image,
                edit_path, edit_url, prev_path, prev_url,
                edit_style, edit_prompt,
                edit_status, undo_btn,
                gen_content_st, gen_transparent_st,
            ],
        )

        # -- 编辑页: 上传 --
        edit_upload.upload(
            fn=on_upload_for_edit, inputs=[edit_upload],
            outputs=[edit_image, edit_path, edit_url],
        )

        # -- 编辑页: 提交编辑 --
        edit_submit_btn.click(
            fn=on_edit_submit,
            inputs=[edit_instruction, edit_url, edit_style,
                    edit_path, edit_prompt, gen_transparent_st],
            outputs=[
                edit_image, edit_status,
                edit_path, edit_url,
                edit_style, edit_prompt,
                undo_btn,
            ],
        )

        # -- 编辑页: 撤销 --
        undo_btn.click(
            fn=on_undo,
            inputs=[prev_path, prev_url, edit_style, edit_prompt],
            outputs=[edit_image, edit_status,
                     edit_path, edit_url,
                     edit_style, edit_prompt, undo_btn],
        )

        # -- 编辑页: 保存 --
        save_btn.click(
            fn=on_save_image, inputs=[edit_path, save_format],
            outputs=[save_file, edit_status],
        )

        # -- 编辑页: 改尺寸 --
        resize_btn.click(
            fn=on_resize_image,
            inputs=[edit_path, resize_w, resize_h,
                    edit_url, edit_style, edit_prompt],
            outputs=[edit_image, edit_status,
                     edit_path, edit_url,
                     edit_style, edit_prompt],
        )

        # -- 编辑页: 改风格 --
        style_btn.click(
            fn=on_style_change,
            inputs=[edit_path, edit_url, new_style_input,
                    keep_content_cb, edit_style, edit_prompt,
                    gen_transparent_st],
            outputs=[edit_image, edit_status,
                     edit_path, edit_url,
                     edit_style, edit_prompt],
        )

        # -- 返回首页 --
        back_gen_btn.click(
            fn=lambda: ("home",) + _show("home") + (
                render_steps("home"),),
            inputs=[],
            outputs=[page, home_col, generate_col, edit_col, step_html],
        )
        back_edit_btn.click(
            fn=lambda: ("home",) + _show("home") + (
                render_steps("home"),),
            inputs=[],
            outputs=[page, home_col, generate_col, edit_col, step_html],
        )

    return demo

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    if not API_KEY:
        print("错误: 未设置 DASHSCOPE_API_KEY")
        print("请在 .env-dev 文件中填入你的 Key，格式: DASHSCOPE_API_KEY=sk-xxx")
        exit(1)

    dashscope.api_key = API_KEY
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
