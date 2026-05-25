"""提示词构造函数。"""


def build_t2i_prompt(content: str, style: str, transparent: bool) -> str:
    """文生图提示词。"""
    content = content.strip()
    if content and content[-1] not in "。！？.!?":
        content += "。"
    parts = [
        f"严格遵循{style}风格。",
        f"画面必须完全符合{style}的视觉特征，包括构图、色彩、笔触、光影等所有方面。",
        content,
    ]
    if transparent:
        parts.append("透明背景，无底色，PNG格式，Alpha通道。")
    return "".join(parts)


def build_edit_prompt(instruction: str, style: str, transparent: bool) -> str:
    """图编辑提示词。"""
    instruction = instruction.strip()
    if instruction and instruction[-1] not in "。！？.!?":
        instruction += "。"
    parts = [
        f"严格保持{style}风格，画面必须完全符合{style}的视觉特征。",
        instruction,
    ]
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
        return (
            f"严格遵循{new_style}风格。"
            f"画面必须完全符合{new_style}的视觉特征。"
            f"{content_part}。"
        )

    if keep_content:
        return (
            f"将这张图片的风格改为{new_style}。"
            f"严格遵循{new_style}风格，画面必须完全符合{new_style}的视觉特征。"
            f"保持画面内容、物体位置、形态完全不变。"
        )
    return (
        f"将这张图片的风格改为{new_style}。"
        f"严格遵循{new_style}风格，画面必须完全符合{new_style}的视觉特征。"
    )
