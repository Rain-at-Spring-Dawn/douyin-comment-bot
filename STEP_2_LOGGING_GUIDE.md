# Step 2: 日志系统集成指南

## 📋 创建的文件

✅ `src/utils/logger.py` - 完整的日志工具库
✅ `config.py` - 增强的配置管理

---

## 🔧 快速集成示例

### 示例 1: 在 `bot.py` 中使用日志

```python
# bot.py
from src.utils.logger import get_bot_logger

logger = get_bot_logger()

class DouyinCommentBot:
    async def run(self, video_url: str, max_comments: int = 20, auto_reply: bool = True):
        logger.info(f"开始处理视频: {video_url}")
        logger.debug(f"配置: max_comments={max_comments}, auto_reply={auto_reply}")
        
        try:
            # 现有代码...
            logger.info("视频处理完成")
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            raise
```

### 示例 2: 在 `reply_poster.py` 中使用日志

```python
# reply_poster.py
from src.utils.logger import get_poster_logger

logger = get_poster_logger()

class ReplyPoster:
    async def post_replies(self, comments_with_replies):
        logger.info(f"开始发布回复，共 {len(comments_with_replies)} 条")
        
        for i, item in enumerate(comments_with_replies):
            try:
                success = await self._post_single_reply(item["ai_reply"])
                if success:
                    self.reply_count += 1
                    logger.info(f"回复成功 [{i+1}/{len(comments_with_replies)}]")
                else:
                    logger.warning(f"回复失败 [{i+1}/{len(comments_with_replies)}]")
            except Exception as e:
                logger.error(f"回复异常: {e}", exc_info=True)
```

### 示例 3: 在 `comment_fetcher.py` 中使用日志

```python
# comment_fetcher.py
from src.utils.logger import get_fetcher_logger

logger = get_fetcher_logger()

class CommentFetcher:
    async def fetch_comments(self, max_comments: int = 50):
        logger.info(f"开始抓取评论，最多 {max_comments} 条")
        
        try:
            comments = await self._fetch_with_listener(max_comments)
            logger.info(f"成功抓到 {len(comments)} 条评论")
            return comments
        except Exception as e:
            logger.error(f"评论抓取失败: {e}", exc_info=True)
            return []
```

---

## 📊 日志级别使用规范

| 级别 | 用途 | 示例 |
|-----|------|------|
| DEBUG | 详细的调试信息 | 函数进出、变量值 |
| INFO | 普通信息流 | 任务开始/完成 |
| WARNING | 警告信息 | 配置不当、超时将至 |
| ERROR | 错误信息 | 操作失败 |
| CRITICAL | 严重错误 | 系统崩溃前兆 |

---

## 🎯 配置 .env 文件

在 `.env` 中添加：

```ini
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

在 Python 中读取：

```python
from config import config

# 自动从 .env 读取 LOG_LEVEL，默认为 INFO
print(config.log_level)  # "INFO"
```

---

## 📁 日志输出目录结构

运行程序后，自动生成：

```
douyin-comment-bot/
├── logs/
│   ├── douyin-bot.log        # 主应用日志
│   ├── bot.log               # 机器人核心日志
│   ├── fetcher.log           # 评论抓取日志
│   ├── generator.log         # 回复生成日志
│   ├── poster.log            # 回复发布日志
│   ├── login.log             # 登录日志
│   ├── bot.log.1             # 轮转日志（>10MB时）
│   └── bot.log.2
└── src/
```

每个日志文件：
- 最大 10MB
- 自动轮转，保留最近 5 个备份
- UTF-8 编码

---

## 🔍 日志输出示例

### 控制台输出（彩色）

```
[2026-06-03 10:30:45] [bot] [INFO] 开始处理视频: https://v.douyin.com/xxx
[2026-06-03 10:30:48] [fetcher] [DEBUG] 解析视频ID: 123456789
[2026-06-03 10:30:50] [fetcher] [INFO] 已加载视频页面
[2026-06-03 10:31:02] [fetcher] [INFO] 成功抓到 15 条评论
[2026-06-03 10:31:05] [generator] [INFO] 生成AI回复中...
[2026-06-03 10:31:20] [poster] [WARNING] 触发风控检测，等待验证
[2026-06-03 10:31:30] [poster] [INFO] 验证已通过，继续回复
[2026-06-03 10:31:35] [poster] [ERROR] 回复失败: 选择器不匹配
[2026-06-03 10:31:36] [poster] [INFO] 共成功回复 12/15 条
[2026-06-03 10:31:36] [bot] [INFO] 任务完成
```

### 文件输出示例（logs/bot.log）

```
[2026-06-03 10:30:45] [bot] [INFO] 开始处理视频: https://v.douyin.com/xxx
[2026-06-03 10:30:48] [bot] [DEBUG] 启动浏览器...
[2026-06-03 10:30:52] [bot] [DEBUG] 浏览器启动完成，PID=12345
[2026-06-03 10:30:54] [bot] [INFO] Step 1/4: 登录抖音
[2026-06-03 10:30:55] [login] [DEBUG] 打开登录页面
[2026-06-03 10:31:30] [login] [INFO] 登录成功
[2026-06-03 10:31:32] [bot] [INFO] Step 2/4: 抓取评论
[2026-06-03 10:31:50] [fetcher] [DEBUG] API响应: 200
[2026-06-03 10:32:05] [fetcher] [INFO] 成功抓到 15 条评论
[2026-06-03 10:32:07] [bot] [INFO] Step 3/4: 生成AI回复
[2026-06-03 10:32:25] [generator] [INFO] AI回复生成完成
[2026-06-03 10:32:27] [bot] [INFO] Step 4/4: 发布回复
[2026-06-03 10:32:30] [poster] [DEBUG] 开始回复循环
[2026-06-03 10:32:31] [poster] [INFO] 回复成功 [1/15]
[2026-06-03 10:32:46] [poster] [INFO] 回复成功 [2/15]
[2026-06-03 10:32:47] [poster] [ERROR] 回复失败 [3/15]: 选择器不匹配
Traceback (most recent call last):
  File "reply_poster.py", line 95, in _post_single_reply
    await draft_editor.type(reply_text, delay=100)
  File "site-packages/playwright/_async_api.py", line 2000, in type
    raise TimeoutError(msg)
TimeoutError: Timeout 5000ms exceeded
[2026-06-03 10:32:50] [poster] [INFO] 回复成功 [4/15]
...
[2026-06-03 10:33:00] [poster] [INFO] 共成功回复 12/15 条
[2026-06-03 10:33:01] [bot] [INFO] 任务完成
[2026-06-03 10:33:02] [bot] [INFO] 关闭浏览器
```

---

## ✅ 集成检查清单

- [ ] 在 `bot.py` 中添加日志
- [ ] 在 `reply_poster.py` 中添加日志
- [ ] 在 `comment_fetcher.py` 中添加日志
- [ ] 在 `reply_generator.py` 中添加日志
- [ ] 在 `login.py` 中添加日志
- [ ] 在 `.env` 中设置 `LOG_LEVEL`
- [ ] 验证日志文件生成在 `logs/` 目录

---

## 🚀 下一步

现在你有了：
1. ✅ Step 1: 跨平台路径工具
2. ✅ Step 2: 完整日志系统

**下一个目标是 P0-3: 异常处理与类型注解**

继续优化吗？
