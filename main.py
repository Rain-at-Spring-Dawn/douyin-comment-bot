"""Douyin Comment Bot - CLI entry point."""
import asyncio

import typer
from rich.console import Console

from bot import DouyinCommentBot
from config import config

app = typer.Typer(
    name="douyin-comment-bot",
    help="🎵 抖音评论自动回复机器人",
    rich_markup_mode="rich",
)
console = Console()


@app.callback()
def callback():
    """Douyin Comment Bot - 自动抓取评论并AI回复"""
    pass


@app.command()
def run(
    video_url: str = typer.Argument(
        ...,
        help="抖音视频链接 (支持短链接 v.douyin.com/xxx 和标准链接)",
    ),
    max_comments: int = typer.Option(
        20,
        "--max", "-m",
        help="最大回复评论数",
    ),
    headless: bool = typer.Option(
        False,
        "--headless",
        help="无头模式 (不显示浏览器窗口，仅独立浏览器模式有效)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="仅抓取评论，不发布回复",
    ),
    interval: int = typer.Option(
        15,
        "--interval", "-i",
        help="每条回复间隔秒数",
    ),
    cdp: bool = typer.Option(
        False,
        "--cdp",
        help="CDP模式 - 连接你正在使用的Chrome浏览器，使用已有登录态，避免重复登录和验证码",
    ),
    cdp_port: int = typer.Option(
        9222,
        "--cdp-port",
        help="CDP调试端口",
    ),
):
    """🚀 运行抖音评论自动回复机器人

    \b
    两种模式:
    - 默认模式: 启动独立浏览器，需扫码登录
    - --cdp 模式: 连接你已有的Chrome，用现有登录态，避免风控和验证码
    """
    config.headless = headless
    config.reply_interval_seconds = interval
    config.max_comments_to_reply = max_comments

    bot = DouyinCommentBot(headless=headless, use_cdp=cdp)
    if cdp:
        bot.cdp_port = cdp_port

    if dry_run:
        console.print("[yellow]🔍 预览模式：仅抓取评论，不发布回复[/yellow]")
        asyncio.run(bot.run_dry(video_url, max_comments))
    else:
        asyncio.run(bot.run(video_url, max_comments, auto_reply=True))


@app.command()
def config_show():
    """📋 显示当前配置"""
    from rich.table import Table

    table = Table(title="当前配置", show_header=True)
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="white")

    table.add_row("抖音首页", config.dy_index_url)
    table.add_row("OpenAI Base URL", config.openai_base_url)
    table.add_row("OpenAI Model", config.openai_model)
    table.add_row("API Key", "***已设置***" if config.openai_api_key else "[red]未设置[/red]")
    table.add_row("最大回复评论数", str(config.max_comments_to_reply))
    table.add_row("回复间隔(秒)", str(config.reply_interval_seconds))
    table.add_row("浏览器数据目录", config.browser_data_dir)

    console.print(table)


if __name__ == "__main__":
    app()
