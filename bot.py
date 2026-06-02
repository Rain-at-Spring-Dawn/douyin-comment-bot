"""Main bot orchestrator for Douyin Comment Bot."""
import asyncio
import subprocess
import time
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
    def __init__(self, headless: bool = False, use_cdp: bool = False):
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_port = 9222
        self.context: Optional[BrowserContext] = None
        self.login_handler = DouyinLogin()
        self.reply_generator = ReplyGenerator()

    async def run(self, video_url: str, max_comments: int = 20, auto_reply: bool = True):
        console.print(Panel.fit(
            "[bold cyan]🎵 抖音评论自动回复机器人[/bold cyan]\n"
            f"[dim]模式: {'CDP (复用Chrome登录态)' if self.use_cdp else '独立浏览器 (QR登录)'}[/dim]",
            border_style="cyan",
        ))

        async with async_playwright() as playwright:
            if self.use_cdp:
                browser = await self._connect_cdp(playwright)
            else:
                browser = await self._launch_browser(playwright)

            self.context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
            )

            try:
                if not self.use_cdp:
                    console.print("\n[bold]📋 Step 1/4: 登录抖音[/bold]")
                    logged_in = await self.login_handler.ensure_login(self.context)
                    if not logged_in:
                        console.print("[red]❌ 登录失败[/red]")
                        return
                else:
                    console.print("\n[bold]📋 Step 1/4: 复用Chrome登录态[/bold]")
                    console.print("[green]  ✅ Chrome已就绪，使用现有登录态[/green]")

                page = await self.context.new_page()
                fetcher = CommentFetcher(page)

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

                table = Table(title=f"📊 抓取到 {len(comments)} 条评论", show_header=True)
                table.add_column("#", style="dim")
                table.add_column("用户", style="cyan")
                table.add_column("评论内容", style="white")
                for i, c in enumerate(comments[:10], 1):
                    table.add_row(str(i), c.get("user_name", "?"), c.get("content", "")[:40])
                if len(comments) > 10:
                    table.add_row("...", f"共{len(comments)}条", "")
                console.print(table)

                console.print("\n[bold]📋 Step 3/4: 生成AI回复[/bold]")
                if auto_reply:
                    comments_with_replies = self.reply_generator.batch_generate(
                        video_info.get("title", ""), comments,
                    )
                else:
                    comments_with_replies = comments

                console.print("\n[bold]📋 Step 4/4: 发布回复[/bold]")
                if auto_reply:
                    poster = ReplyPoster(page)
                    await poster.post_replies(comments_with_replies)
                else:
                    console.print("[yellow]跳过发布[/yellow]")

                console.print("\n[bold green]✅ 完成![/bold green]")

            except Exception as e:
                console.print(f"[red]❌ 出错: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())

    async def run_dry(self, video_url: str, max_comments: int = 20):
        await self.run(video_url, max_comments, auto_reply=False)

    async def _launch_browser(self, playwright):
        console.print("[blue]🚀 启动独立浏览器...[/blue]")
        return await playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-dev-shm-usage"],
        )

    async def _connect_cdp(self, playwright):
        """Connect to Chrome via CDP.
        
        Uses default Chrome profile so all login sessions are preserved.
        """
        import http.client
        import json as _json

        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        # Check if Chrome is already listening on the CDP port
        already_running = False
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.cdp_port, timeout=2)
            conn.request("GET", "/json/version")
            resp = conn.getresponse()
            if resp.status == 200:
                already_running = True
            conn.close()
        except Exception:
            pass

        if not already_running:
            # Kill Chrome so we can restart with the debugging flag
            console.print("[yellow]⚠️ Chrome未以调试模式运行，正在重启Chrome...[/yellow]")
            console.print("[dim]（会关闭当前所有Chrome窗口，但登录态保留）[/dim]")
            subprocess.run(["pkill", "-9", "-f", "Google Chrome"], capture_output=True)
            time.sleep(2)

            # Start Chrome with debugging + default profile
            subprocess.Popen(
                [chrome_path, f"--remote-debugging-port={self.cdp_port}",
                 "--no-first-run", "--no-default-browser-check"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

            # Wait for it
            console.print("[dim]等待Chrome启动...[/dim]")
            for i in range(30):
                time.sleep(1)
                try:
                    conn = http.client.HTTPConnection("127.0.0.1", self.cdp_port, timeout=2)
                    conn.request("GET", "/json/version")
                    resp = conn.getresponse()
                    if resp.status == 200:
                        break
                    conn.close()
                except Exception:
                    if i % 5 == 4:
                        console.print(f"  ⏳ ({i+1}s)...")
            console.print("[green]  ✅ Chrome已就绪[/green]")
        else:
            console.print("[green]  ✅ 检测到Chrome已在调试模式运行[/green]")

        cdp_url = f"http://127.0.0.1:{self.cdp_port}"
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        console.print("[green]  ✅ 已连接到Chrome (使用你的默认登录态)[/green]")
        return browser

    async def _resolve_url(self, fetcher, video_url: str) -> str:
        if "v.douyin.com" in video_url:
            if not video_url.startswith("http"):
                video_url = f"https://{video_url}"
            console.print("[blue]🔗 解析短链接...[/blue]")
            resolved = await fetcher.resolve_short_url(video_url)
            if resolved:
                console.print(f"[green]  → {resolved[:80]}...[/green]")
                return resolved
        return video_url
