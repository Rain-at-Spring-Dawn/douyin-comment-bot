"""Fetch Douyin comments using Playwright."""
import asyncio
import json
import re
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

from playwright.async_api import Page
from rich.console import Console

from config import config

console = Console()


class CommentFetcher:
    """Fetch comments from a Douyin video."""

    def __init__(self, page: Page):
        self.page = page
        self._video_title: str = ""
        self._aweme_id: str = ""

    def parse_video_id(self, url: str) -> Optional[str]:
        """Extract video/aweme ID from various Douyin URL formats."""
        if url.isdigit():
            return url
        for pat in [r'/video/(\d+)', r'/share/video/(\d+)']:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "modal_id" in qs:
            return qs["modal_id"][0]
        return None

    async def resolve_short_url(self, url: str) -> Optional[str]:
        """Resolve a v.douyin.com short link to a douyin.com/video/ URL."""
        try:
            import httpx
            async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                location = resp.headers.get("location", "")
                if location:
                    full_url = location if location.startswith("http") else f"https:{location}"
                    aweme_id = self.parse_video_id(full_url)
                    if aweme_id:
                        return f"https://www.douyin.com/video/{aweme_id}"
        except Exception as e:
            console.print(f"[red]短链接解析失败: {e}[/red]")
        return None

    async def fetch_video_info(self, video_url: str) -> Optional[dict]:
        """Load video page and extract basic info."""
        console.print(f"[blue]📄 加载视频页面: {video_url}[/blue]")
        try:
            await self.page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            title = await self.page.title()
            self._video_title = title.replace(" - 抖音", "").strip()
            console.print(f"[green]📌 视频标题: {self._video_title}[/green]")

            self._aweme_id = self.parse_video_id(self.page.url) or ""
            console.print(f"[dim]Aweme ID: {self._aweme_id}[/dim]")

            return {
                "aweme_id": self._aweme_id,
                "title": self._video_title,
                "url": self.page.url,
            }
        except Exception as e:
            console.print(f"[red]加载视频页面失败: {e}[/red]")
            return None

    async def fetch_comments(self, max_comments: int = 50) -> List[dict]:
        """Fetch comments by intercepting API and using browser fetch."""
        if not self._aweme_id:
            console.print("[red]❌ 缺少 aweme_id[/red]")
            return []

        console.print(f"[blue]💬 抓取评论 (最多{max_comments}条)...[/blue]")

        # Strategy: Intercept by re-navigating with listener already attached
        comments = await self._fetch_with_listener(max_comments)
        if comments:
            console.print(f"[green]✅ 抓到 {len(comments)} 条评论[/green]")
            return comments

        console.print("[yellow]⚠️ 未抓到评论[/yellow]")
        return []

    async def _fetch_with_listener(self, max_comments: int) -> List[dict]:
        """Navigate to page with listener already attached to catch API calls."""
        captured = []

        async def handle_response(response):
            nonlocal captured
            if "/aweme/v1/web/comment/list/" in response.url and len(captured) < max_comments:
                try:
                    body = await response.json()
                    for c in body.get("comments", []):
                        captured.append({
                            "comment_id": c.get("cid", ""),
                            "user_name": c.get("user", {}).get("nickname", "") if c.get("user") else "",
                            "content": c.get("text", ""),
                            "digg_count": c.get("digg_count", 0),
                            "create_time": c.get("create_time", 0),
                        })
                except Exception:
                    pass

        # Attach listener before navigation
        self.page.on("response", handle_response)

        try:
            # Navigate fresh
            await self.page.goto(
                f"https://www.douyin.com/video/{self._aweme_id}",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Wait for page to load and API to respond
            for i in range(15):
                await asyncio.sleep(2)
                if len(captured) >= max_comments:
                    break
                # Scroll to trigger more comment loading
                if i > 2:
                    await self.page.evaluate("window.scrollBy(0, 800)")
        except Exception as e:
            console.print(f"[yellow]页面加载时出错: {e}[/yellow]")

        self.page.remove_listener("response", handle_response)
        return captured[:max_comments]
