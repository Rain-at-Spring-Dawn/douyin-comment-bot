# 🎵 Douyin Comment Bot

> 抖音评论自动回复机器人 — 自动抓取评论区内容，用 AI 生成回复并自动发布

## ✨ 功能

- ✅ **抖音登录** — QR 扫码登录，支持持久化登录态
- ✅ **评论抓取** — 自动抓取指定视频的评论区内容
- ✅ **AI 回复生成** — 接入大模型 API，根据视频标题和评论内容生成自然回复
- ✅ **自动发布回复** — 通过浏览器自动化模拟操作，自动回复评论
- ✅ **预览模式** — 只抓不回复，安全试跑

## 🚀 快速开始

```bash
# 安装依赖
uv sync

# 配置 API Key（用于 AI 回复生成）
# 编辑 .env 文件：
#   OPENAI_API_KEY=sk-your-key
#   OPENAI_BASE_URL=https://api.openai.com/v1
#   OPENAI_MODEL=gpt-4o-mini

# 预览模式（只抓评论，不回复）
uv run python main.py run "https://v.douyin.com/xxx" --dry-run

# 全自动模式（抓评论 → AI生成 → 自动回复）
uv run python main.py run "https://v.douyin.com/xxx"

# 自定义参数
uv run python main.py run "链接" --max 50 --interval 10 --headless
```

## 📋 命令说明

| 命令 | 说明 |
|------|------|
| `run <url>` | 运行机器人 |
| `run <url> --dry-run` | 预览模式，仅抓取评论 |
| `config-show` | 显示当前配置 |

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--max, -m` | 20 | 最大抓取/回复评论数 |
| `--interval, -i` | 15 | 每条回复间隔秒数 |
| `--headless, -h` | false | 无头模式（不显示浏览器） |
| `--dry-run, -d` | false | 仅抓取，不发布回复 |

## ⚙️ 配置

通过 `.env` 文件配置：

```ini
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## 📦 项目结构

```
douyin-comment-bot/
├── main.py              # CLI 入口
├── bot.py               # 主控流程编排
├── config.py            # 配置管理
├── login.py             # 抖音 QR 扫码登录
├── comment_fetcher.py   # 评论抓取模块
├── reply_generator.py   # AI 回复生成
├── reply_poster.py      # 自动发布回复
├── .env                 # 环境变量配置
└── requirements.txt     # 依赖清单
```

## 🔧 技术栈

- **Python 3.11+**
- **Playwright** — 浏览器自动化（登录、评论抓取、回复发布）
- **OpenAI Python SDK** — AI 回复生成（兼容任何 OpenAI API 接口）
- **Typer + Rich** — CLI 交互

## 🙏 致谢与借鉴

本项目在开发过程中参考了以下开源项目：

### [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) ⭐50K+

- **借鉴内容**：抖音登录流程设计、评论 API 端点发现、a-bogus 签名处理思路
- **不同之处**：本项目使用 Playwright 浏览器自动化方式替代纯 API 调用，通过浏览器上下文自动处理签名和登录态，无需单独处理 JS 逆向
- **许可证**：Non-Commercial Learning License 1.1

### [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) ⭐18K

- **借鉴内容**：抖音 URL 格式解析、API 端点参考
- **许可证**：AGPL-3.0

### 其他参考

- [lizeyujack/douyin_auto-reply](https://github.com/lizeyujack/douyin_auto-reply) ⭐5 — 使用 Selenium 自动回复评论的思路参考

## 📄 许可证

MIT License — 本项目采用 MIT 许可证，但请遵守目标平台的使用条款。

**免责声明：** 本工具仅供学习和研究使用。禁止用于任何非法用途或侵犯他人权益。使用者应自行承担所有法律责任。
