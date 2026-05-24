"""提示词构造函数。"""


def build_t2i_prompt(content: str, style: str, transparent: bool) -> str:
    """文生图提示词。"""
    content = content.strip()
    if content and content[-1] not in "。！？.!?":
        content += "。"
    parts = [content, f"采用{style}风格。"]
    if transparent:
        parts.append("透明背景，无底色，PNG格式，Alpha通道。")
    return "".join(parts)


def build_edit_prompt(instruction: str, style: str, transparent: bool) -> str:
    """图编辑提示词。"""
    instruction = instruction.strip()
    if instruction and instruction[-1] not in "。！？.!?":
        instruction += "。"
    parts = [instruction, f"保持{style}风格。"]
    if transparent:
        parts.append("透明背景，无底色，PNG格式，Alpha通道。")
    return "".join(parts)


def build_style_change_prompt(new_style: str, keep_content: bool,
                               gen_prompt: str = "") -> str:
    """改风格提示词：复用原始prompt的内容部分+新风格。"""
    if gen_prompt:
        content_part = (
            gen_prompt.split("。")[0] if "。" in gen_prompt else gen_prompt
        )
        return f"{content_part}。采用{new_style}风格。"

    if keep_content:
        return (
            f"将这张图片的风格改为{new_style}。"
            f"保持画面内容、物体位置、形态完全不变。"
        )
    return f"将这张图片的风格改为{new_style}。"
