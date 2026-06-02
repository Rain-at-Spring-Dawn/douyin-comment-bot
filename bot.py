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

    def __init__(self, headless: bool = False, use_cdp: bool = False):
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_port = 9222
        self.context: Optional[BrowserContext] = None
        self.login_handler = DouyinLogin()
        self.reply_generator = ReplyGenerator()

    async def run(self, video_url: str, max_comments: int = 20, auto_reply: bool = True):
        """Run the full bot pipeline."""
        console.print(Panel.fit(
            "[bold cyan]🎵 抖音评论自动回复机器人[/bold cyan]\n"
            f"[dim]模式: {'CDP (连接现有Chrome)' if self.use_cdp else '独立浏览器 (QR登录)'}[/dim]",
            border_style="cyan",
        ))

        async with async_playwright() as playwright:
            if self.use_cdp:
                # CDP Mode: connect to user's existing Chrome
                browser = await self._connect_cdp(playwright)
            else:
                # Standard mode: launch our own browser
                browser = await self._launch_browser(playwright)

            self.context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
            )

            try:
                # Step 1: Login (only needed in standard mode)
                if not self.use_cdp:
                    console.print("\n[bold]📋 Step 1/4: 登录抖音[/bold]")
                    logged_in = await self.login_handler.ensure_login(self.context)
                    if not logged_in:
                        console.print("[red]❌ 登录失败，终止运行[/red]")
                        return
                else:
                    console.print("\n[bold]📋 Step 1/4: 使用已有Chrome会话[/bold]")
                    console.print("[green]  ✅ 已连接你的Chrome浏览器，使用现有登录态[/green]")

                page = await self.context.new_page()
                fetcher = CommentFetcher(page)

                # Step 2: Fetch video info and comments
                console.print("\n[bold]📋 Step 2/4: 抓取评论[/bold]")

                resolved_url = await self._resolve_url(fetcher, video_url)
                video_info = await fetcher.fetch_video_info(resolved_url)
                if not video_info:
                    console.print("[red]❌ 无法获取视频信息[/red]")
                    return

                comments = await fetcher.fetch_comments(max_comments)
                if not comments:
                    console.print("[yellow]⚠️ 未抓到评论[/yellow]")
                    return

                # Display comments table
                table = Table(title=f"📊 抓取到 {len(comments)} 条评论", show_header=True)
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
                        video_info.get("title", ""), comments,
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
                if not self.use_cdp:
                    await browser.close()
                # In CDP mode, don't close the user's browser

    async def run_dry(self, video_url: str, max_comments: int = 20):
        """Dry run: fetch comments only, no replies."""
        await self.run(video_url, max_comments, auto_reply=False)

    async def _launch_browser(self, playwright):
        """Launch a fresh browser instance."""
        console.print("[blue]🚀 启动独立浏览器...[/blue]")
        return await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

    async def _connect_cdp(self, playwright):
        """Connect to user's existing Chrome via CDP."""
        cdp_url = f"http://127.0.0.1:{self.cdp_port}"
        console.print(f"[blue]🔗 连接到已有Chrome浏览器 (CDP端口: {self.cdp_port})...[/blue]")
        console.print(Panel(
            "[yellow]使用前请确保已用以下命令启动Chrome:[/yellow]\n"
            f"  [bold]open -a 'Google Chrome' --args --remote-debugging-port={self.cdp_port}[/bold]\n\n"
            "[dim]或者在终端运行:[/dim]\n"
            f"  [bold]/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={self.cdp_port}[/bold]",
        ))
        try:
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            console.print(f"[green]  ✅ 已连接到Chrome[/green]")
            return browser
        except Exception as e:
            console.print(f"[red]  ❌ 连接失败: {e}[/red]")
            console.print("[yellow]请确保Chrome已用 --remote-debugging-port 参数启动[/yellow]")
            raise

    async def _resolve_url(self, fetcher, video_url: str) -> str:
        """Resolve short URLs to full douyin.com URLs."""
        if "v.douyin.com" in video_url:
            if not video_url.startswith("http"):
                video_url = f"https://{video_url}"
            console.print("[blue]🔗 解析短链接...[/blue]")
            resolved = await fetcher.resolve_short_url(video_url)
            if resolved:
                console.print(f"[green]  → 解析到: {resolved[:80]}...[/green]")
                return resolved
            console.print("[yellow]  ⚠️ 短链接解析失败，直接访问[/yellow]")
        return video_url
