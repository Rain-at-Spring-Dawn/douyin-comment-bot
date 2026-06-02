# 🎵 Douyin Comment Bot (开发中 / WIP)

> 抖音评论自动回复机器人 — 自动抓取评论区内容，用 AI 生成回复并自动发布

## ⚠️ 项目状态：未完成

本项目处于 **功能验证阶段**，核心链路已验证通过，但存在以下已知问题：

### 已知问题

1. **短信验证码风控** — 抖音网页版对自动回复行为有安全检测机制，连续回复 1-2 条后可能触发短信验证（"为确保是本人操作抖音账号，请输入手机号收到的短信验证码"）。这是抖音的反滥用机制，非程序 Bug。
2. **CDP 模式受阻** — 计划通过 Chrome DevTools Protocol 连接用户已有 Chrome 浏览器来复用登录态、绕过风控，但因用户环境中的代理（`ALL_PROXY`）拦截了本地 CDP 端口通信，目前未能稳定实现。
3. **独立浏览器模式有局限** — 使用 Playwright 独立浏览器需扫码登录，且登录态持久化在部分场景下不稳定。

### 解决方向参考

参考了 [jackwener/OpenCLI](https://github.com/jackwener/OpenCLI) 的思路：
- 通过 Chrome 扩展桥接用户已有浏览器会话，无需处理登录和验证码
- 利用用户真实浏览器的登录态和信任度，避免触发风控
- 详见下方 [致谢](#-致谢与借鉴) 部分

---

## ✨ 当前已实现功能

- ✅ **抖音登录** — QR 扫码登录，支持持久化登录态
- ✅ **评论抓取** — 通过 API 拦截自动抓取指定视频的评论
- ✅ **AI 回复生成** — 接入大模型 API，支持 OpenAI / DeepSeek / 阶跃星辰等任意兼容接口
- ✅ **自动发布回复** — 通过浏览器 DraftEditor 交互自动回复（已验证单条成功）
- ✅ **预览模式** — 只抓不回复，安全试跑

## 🚀 快速开始

```bash
# 安装依赖
uv sync

# 配置 API Key（用于 AI 回复生成）
# 编辑 .env 文件

# 预览模式（只抓评论，不回复）
uv run python main.py run "https://v.douyin.com/xxx" --dry-run

# 全自动模式（抓评论 → AI生成 → 自动回复）
uv run python main.py run "https://v.douyin.com/xxx"

# CDP 模式（实验性，需要 Chrome 以调试模式启动）
uv run python main.py run "链接" --cdp
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
| `--headless` | false | 无头模式（不显示浏览器） |
| `--dry-run, -d` | false | 仅抓取，不发布回复 |
| `--cdp` | false | CDP 模式（实验性，连接已有 Chrome） |
| `--cdp-port` | 9222 | CDP 调试端口 |

## ⚙️ 配置

### 🤖 AI 模型配置（完全自定义）

本项目的 AI 回复生成支持任意兼容 OpenAI API 接口的大模型，**端点、模型名、API Key 均可自由配置**。

通过 `.env` 文件配置：

**OpenAI**
```ini
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

**DeepSeek**
```ini
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

**阶跃星辰（StepFun）**
```ini
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://api.stepfun.com/step_plan/v1
OPENAI_MODEL=step-router-v1
```

> 不配置 API Key 时，机器人会使用预设文案回复，不影响基本功能。

### 浏览器数据目录

登录状态自动保存在 `browser_data/` 目录下，下次运行无需重复扫码。

## 📦 项目结构

```
douyin-comment-bot/
├── main.py              # CLI 入口
├── bot.py               # 主控流程编排
├── config.py            # 配置管理（自动加载 .env）
├── login.py             # 抖音 QR 扫码登录
├── comment_fetcher.py   # 评论抓取模块
├── reply_generator.py   # AI 回复生成
├── reply_poster.py      # 自动发布回复
├── .env                 # 环境变量配置（不提交）
├── .env.example         # 配置模板
├── pyproject.toml       # 项目配置 + 依赖
└── README.md
```

## 🔧 技术栈

- **Python 3.11+**
- **Playwright** — 浏览器自动化（登录、评论抓取、回复发布）
- **OpenAI Python SDK** — AI 回复生成（兼容任何 OpenAI API 接口）
- **Typer + Rich** — CLI 交互
- **python-dotenv** — 环境变量管理

## 🙏 致谢与借鉴

本项目在开发过程中参考了以下开源项目：

### [jackwener/OpenCLI](https://github.com/jackwener/OpenCLI) ⭐23K+

- **借鉴内容**：通过 Chrome 扩展 / CDP 桥接用户已有浏览器会话，复用登录态的思路
- **目标**：本项目计划实现类似的 CDP 连接能力，以解决抖音风控和短信验证问题
- **当前状态**：CDP 模式尚未稳定实现（受限于用户环境的代理设置），作为后续改进方向
- **许可证**：MIT

### [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) ⭐50K+

- **借鉴内容**：抖音登录流程设计、评论 API 端点发现、a-bogus 签名处理思路
- **不同之处**：本项目使用 Playwright 浏览器自动化方式替代纯 API 调用，通过浏览器上下文自动处理签名和登录态
- **许可证**：Non-Commercial Learning License 1.1

### [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) ⭐18K

- **借鉴内容**：抖音 URL 格式解析、API 端点参考
- **许可证**：AGPL-3.0

### 其他参考

- [lizeyujack/douyin_auto-reply](https://github.com/lizeyujack/douyin_auto-reply) — 使用 Selenium 自动回复评论的思路参考

## 📄 许可证

MIT License — 本项目采用 MIT 许可证，但请遵守目标平台的使用条款。

**免责声明：** 本工具仅供学习和研究使用。禁止用于任何非法用途或侵犯他人权益。使用者应自行承担所有法律责任。
