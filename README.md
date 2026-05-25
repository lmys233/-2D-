# 2D游戏素材生成器

基于阿里云百炼 DashScope API 的 AI 图像生成工具，支持文生图、图片编辑、风格转换、尺寸调整。

## 功能

- **图片生成** — 文本描述 + 风格控制 → 3 张候选图
- **图片编辑** — AI 局部修改，可选保持内容不变，自动同步原图尺寸
- **改风格** — 保持内容不变，替换为新风格
- **改尺寸** — 等比缩放居中，空余区域透明，实时绿框预览
- **绿幕去底** — numpy 矢量化去绿幕，输出透明 PNG
- **格式转换** — PNG / JPEG / WebP

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env-dev
```

编辑 `.env-dev`，填入你的百炼 API Key：

```
DASHSCOPE_API_KEY=sk-xxxxx
```

### 3. 启动

```bash
python main.py
```

浏览器访问 `http://localhost:7860`

## 项目结构

```
.
├── main.py          # FastAPI 后端 + API 路由
├── api.py           # DashScope API 调用封装
├── prompts.py       # 提示词构造函数
├── image_utils.py   # 图片下载、缩放、绿幕去底、格式转换
├── config.py        # API Key 加载、模型名配置
├── static/
│   └── index.html   # 前端 SPA 页面
├── outputs/         # 生成的图片（已加入 .gitignore）
├── .env.example     # API Key 配置模板
├── .env-dev         # 本地 API Key（已加入 .gitignore）
└── requirements.txt
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/generate` | 文生图 |
| POST | `/api/edit` | 图编辑 |
| POST | `/api/style-change` | 改风格 |
| POST | `/api/resize` | 改尺寸 |
| POST | `/api/save` | 格式转换 |
| POST | `/api/upload` | 上传图片 |
| GET | `/api/outputs/{filename}` | 获取图片文件 |
