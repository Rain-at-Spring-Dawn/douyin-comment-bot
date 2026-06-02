"""Main bot orchestrator for Douyin Comment Bot."""
import asyncio
from typing import Optional

from playwright.async_api import BrowserContext, async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import config
from login import DouyinLogin
from comment_fetcher import CommentFetcher
from reply_generator import ReplyGenerator
from reply_poster import ReplyPoster

console = Console()


class DouyinCommentBot:
    """Orchestrates the full pipeline: login → fetch comments → generate replies → post."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.context: Optional[BrowserContext] = None
        self.login_handler = DouyinLogin()
        self.reply_generator = ReplyGenerator()

    async def run(self, video_url: str, max_comments: int = 20, auto_reply: bool = True):
        """Run the full bot pipeline."""
        console.print(Panel.fit(
            "[bold cyan]🎵 抖音评论自动回复机器人[/bold cyan]\n"
            "[dim]Douyin Comment Auto-Reply Bot[/dim]",
            border_style="cyan",
        ))

        async with async_playwright() as playwright:
            # Launch browser
            console.print("[blue]🚀 启动浏览器...[/blue]")
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            self.context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            try:
                # Step 1: Login
                console.print("\n[bold]📋 Step 1/4: 登录抖音[/bold]")
                logged_in = await self.login_handler.ensure_login(self.context)
                if not logged_in:
                    console.print("[red]❌ 登录失败，终止运行[/red]")
                    return

                # Create a page for the bot
                page = await self.context.new_page()
                fetcher = CommentFetcher(page)

                # Step 2: Fetch video info and comments
                console.print("\n[bold]📋 Step 2/4: 抓取评论[/bold]")
                
                # Resolve short URL if needed
                if "v.douyin.com" in video_url and not video_url.startswith("http"):
                    video_url = f"https://{video_url}" if not video_url.startswith("https://") else video_url
                
                resolved_url = video_url
                if "v.douyin.com" in video_url:
                    console.print("[blue]🔗 解析短链接...[/blue]")
                    resolved = await fetcher.resolve_short_url(video_url)
                    if resolved:
                        resolved_url = resolved
                        console.print(f"[green]  → 解析到: {resolved_url[:80]}...[/green]")
                    else:
                        console.print("[yellow]  ⚠️ 短链接解析失败，直接尝试访问[/yellow]")

                # Fetch video info
                video_info = await fetcher.fetch_video_info(resolved_url)
                if not video_info:
                    console.print("[red]❌ 无法获取视频信息[/red]")
                    return

                # Fetch comments
                comments = await fetcher.fetch_comments(max_comments)
                if not comments:
                    console.print("[yellow]⚠️ 未抓到评论[/yellow]")
                    return

                # Display comments table
                table = Table(title="📊 抓取到的评论", show_header=True)
                table.add_column("#", style="dim")
                table.add_column("用户", style="cyan")
                table.add_column("评论内容", style="white")
                for i, c in enumerate(comments[:10], 1):
                    table.add_row(str(i), c.get("user_name", "?"), c.get("content", "")[:40])
                if len(comments) > 10:
                    table.add_row("...", f"共{len(comments)}条", "")
                console.print(table)

                # Step 3: Generate AI replies
                console.print("\n[bold]📋 Step 3/4: 生成AI回复[/bold]")
                if auto_reply:
                    comments_with_replies = self.reply_generator.batch_generate(
                        video_info.get("title", ""),
                        comments,
                    )
                else:
                    comments_with_replies = comments

                # Step 4: Post replies
                console.print("\n[bold]📋 Step 4/4: 发布回复[/bold]")
                if auto_reply:
                    poster = ReplyPoster(page)
                    await poster.post_replies(comments_with_replies)
                else:
                    console.print("[yellow]跳过发布步骤 (auto_reply=False)[/yellow]")

                console.print("\n[bold green]✅ 全部流程完成![/bold green]")

            except Exception as e:
                console.print(f"[red]❌ 运行出错: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())

            finally:
                await browser.close()

    async def run_dry(self, video_url: str, max_comments: int = 20):
        """Dry run: fetch comments only, no replies."""
        await self.run(video_url, max_comments, auto_reply=False)
