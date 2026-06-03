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
    """应用配置类"""
    
    # =============== 抖音配置 ===============
    dy_index_url: str = "https://www.douyin.com"
    
    # =============== OpenAI 配置 ===============
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # =============== 机器人行为配置 ===============
    max_comments_to_reply: int = 20
    reply_interval_seconds: int = 15
    max_reply_history: int = 100
    headless: bool = False
    
    # =============== 浏览器数据配置 ===============
    browser_data_dir: str = os.path.join(os.path.dirname(__file__), "browser_data")
    
    # =============== 日志配置 ===============
    log_level: str = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir: str = "logs"
    
    # =============== 缓存配置 ===============
    use_cache: bool = True
    cache_ttl_hours: int = 24
    cache_dir: str = "cache"
    
    # =============== 回复风格配置 ===============
    reply_prompt_template: str = (
        "你是一个抖音评论区回复助手。请根据以下视频标题和评论内容，"
        "生成一条自然、友好的回复。回复要口语化、简短（20字以内），"
        "带有抖音风格，可以适当使用表情符��。\n\n"
        "视频标题：{video_title}\n"
        "评论内容：{comment_content}\n\n"
        "请只输出回复内容，不要加引号或其他格式："
    )
    
    def validate(self) -> bool:
        """验证配置的有效性
        
        Returns:
            bool: 配置是否有效
            
        Raises:
            ValueError: 配置无效时抛出
        """
        # 验证 max_comments_to_reply
        if self.max_comments_to_reply < 1:
            raise ValueError("max_comments_to_reply 必须 >= 1")
        
        # 验证 reply_interval_seconds
        if self.reply_interval_seconds < 5:
            import warnings
            warnings.warn("回复间隔过短（<5秒），可能触发风控！", UserWarning)
        
        # 验证 log_level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"log_level 必须是 {valid_levels} 之一")
        
        # 验证 OpenAI 配置
        if not self.openai_api_key:
            import warnings
            warnings.warn(
                "未设置 OPENAI_API_KEY，将使用预设回复",
                UserWarning
            )
        
        return True
    
    def get_log_level_int(self) -> int:
        """获取日志级别的整数值
        
        Returns:
            int: 日志级别
        """
        import logging
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self.log_level.upper(), logging.INFO)


# 全局配置实例
config = Config()

# 初始化时验证配置
try:
    config.validate()
except Exception as e:
    import warnings
    warnings.warn(f"配置验证失败: {e}", UserWarning)
