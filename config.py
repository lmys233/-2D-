"""API Key 加载、模型名、常量配置。"""
import os
from pathlib import Path


def load_api_key() -> str:
    env_file = Path(__file__).parent / ".env-dev"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key.strip() == "DASHSCOPE_API_KEY":
                    return value.strip().strip('"').strip("'")
    return os.environ.get("DASHSCOPE_API_KEY", "")


API_KEY = load_api_key()
T2I_MODEL = "qwen-image-2.0-pro"
I2I_MODEL = "qwen-image-2.0-pro"
BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

SIZE_OPTIONS = [
    "2048*2048", "2688*1536", "1536*2688", "2368*1728", "1728*2368",
]
