"""Configuration management for Douyin Comment Bot."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Auto-load .env file
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Config:
    # Douyin
    dy_index_url: str = "https://www.douyin.com"
    
    # OpenAI-compatible API for reply generation
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Bot behavior
    max_comments_to_reply: int = 20
    reply_interval_seconds: int = 15
    max_reply_history: int = 100
    headless: bool = False
    
    # Browser data directory (for persisting login state)
    browser_data_dir: str = os.path.join(os.path.dirname(__file__), "browser_data")
    
    # Reply style prompt
    reply_prompt_template: str = (
        "你是一个抖音评论区回复助手。请根据以下视频标题和评论内容，"
        "生成一条自然、友好的回复。回复要口语化、简短（20字以内），"
        "带有抖音风格，可以适当使用表情符号。\n\n"
        "视频标题：{video_title}\n"
        "评论内容：{comment_content}\n\n"
        "请只输出回复内容，不要加引号或其他格式："
    )


config = Config()
