"""提示词构造函数。"""

_GREEN_BG = (
    "【格式要求】画面主体之外的所有背景区域必须是纯绿色(#00FF00)，"
    "背景必须填充为统一的#00FF00纯绿色，不能是白色、黑色或任何其他颜色。"
)


def build_t2i_prompt(content: str, style: str) -> str:
    """文生图提示词。"""
    content = content.strip()
    if content and content[-1] not in "。！？.!?":
        content += "。"
    return "".join([
        _GREEN_BG,
        f"严格遵循{style}风格。",
        f"画面必须完全符合{style}的视觉特征，包括构图、色彩、笔触、光影等所有方面。",
        content,
    ])


def build_edit_prompt(instruction: str, style: str,
                      keep_content: bool = False) -> str:
    """图编辑提示词。"""
    instruction = instruction.strip()
    if instruction and instruction[-1] not in "。！？.!?":
        instruction += "。"
    parts = [
        _GREEN_BG,
        f"严格保持{style}风格，画面必须完全符合{style}的视觉特征。",
    ]
    if keep_content:
        parts.append("保持画面内容、物体位置、形态完全不变。")
    parts.append(instruction)
    return "".join(parts)


def build_style_change_prompt(new_style: str, keep_content: bool,
                               gen_prompt: str = "") -> str:
    """改风格提示词：复用原始prompt的内容部分+新风格。"""
    if gen_prompt:
        content_part = (
            gen_prompt.split("。")[0] if "。" in gen_prompt else gen_prompt
        )
        return (
            f"{_GREEN_BG}"
            f"严格遵循{new_style}风格。"
            f"画面必须完全符合{new_style}的视觉特征。"
            f"{content_part}。"
        )

    if keep_content:
        return (
            f"{_GREEN_BG}"
            f"将这张图片的风格改为{new_style}。"
            f"严格遵循{new_style}风格，画面必须完全符合{new_style}的视觉特征。"
            f"保持画面内容、物体位置、形态完全不变。"
        )
    return (
        f"{_GREEN_BG}"
        f"将这张图片的风格改为{new_style}。"
        f"严格遵循{new_style}风格，画面必须完全符合{new_style}的视觉特征。"
    )
