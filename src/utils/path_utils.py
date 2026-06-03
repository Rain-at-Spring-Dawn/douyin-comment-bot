"""跨平台路径工具"""
import platform
from pathlib import Path
from typing import Optional


def get_screenshot_dir() -> Path:
    """获取跨平台截图目录
    
    Returns:
        Path: 截图目录路径
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Desktop"
    elif system == "Windows":
        return Path.home() / "Pictures"
    else:  # Linux and others
        return Path.home() / "Pictures"


def get_screenshot_path(prefix: str = "douyin") -> str:
    """获取跨平台截图文件路径
    
    Args:
        prefix: 文件名前缀，默认 "douyin"
    
    Returns:
        str: 完整的截图文件路径
    
    Example:
        >>> path = get_screenshot_path("douyin_verify")
        >>> # macOS: /Users/username/Desktop/douyin_verify_120530.png
        >>> # Windows: C:\\Users\\username\\Pictures\\douyin_verify_120530.png
    """
    from datetime import datetime
    
    screenshot_dir = get_screenshot_dir()
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    
    return str(screenshot_dir / filename)


def ensure_cache_dir(cache_name: str = "comments") -> Path:
    """确保缓存目录存在
    
    Args:
        cache_name: 缓存子目录名称
    
    Returns:
        Path: 缓存目录路径
    """
    cache_dir = Path("cache") / cache_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def ensure_log_dir() -> Path:
    """确保日志目录存在
    
    Returns:
        Path: 日志目录路径
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir


def get_browser_data_dir() -> Path:
    """获取浏览器数据目录
    
    Returns:
        Path: 浏览器数据目录路径
    """
    data_dir = Path("browser_data")
    data_dir.mkdir(exist_ok=True)
    return data_dir
