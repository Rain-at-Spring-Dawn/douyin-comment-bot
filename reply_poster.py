"""Post replies to Douyin comments via browser automation."""
import asyncio
from typing import List

from playwright.async_api import Page
from rich.console import Console
from rich.panel import Panel
from datetime import datetime

from config import config

console = Console()


class ReplyPoster:
    """Post AI-generated replies by clicking reply button → typing → Enter."""

    def __init__(self, page: Page):
        self.page = page
        self.reply_count = 0
        self.skip_count = 0

    async def post_replies(self, comments_with_replies: List[dict]) -> int:
        """Post replies to comments. Returns number of successfully posted replies."""
        self.reply_count = 0
        self.skip_count = 0

        # Scroll to load comments first
        for _ in range(3):
            await self.page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(2)

        for i, item in enumerate(comments_with_replies):
            if not item.get("ai_reply"):
                continue

            console.print(f"\n[blue]📤 [{i+1}/{len(comments_with_replies)}] 回复: {item.get('content', '')[:30]}...[/blue]")

            # Check verification before each reply attempt
            if await self._wait_for_verification():
                # User completed verification, try to reply
                pass

            success = await self._post_single_reply(item["ai_reply"])
            if success:
                self.reply_count += 1
                console.print(f"[green]  ✅ 已回复: {item['ai_reply']}[/green]")
            else:
                console.print(f"[red]  ❌ 回复失败（可能是触发了安全验证或已达频率限制）[/red]")
                self.skip_count += 1

            # If too many consecutive failures, stop
            if self.skip_count >= 2:
                console.print("[yellow]⚠️ 连续多次失败，停止回复以避免账号风险[/yellow]")
                break

            # Wait between replies
            if i < len(comments_with_replies) - 1:
                wait = config.reply_interval_seconds
                console.print(f"[dim]⏳ 等待 {wait} 秒...[/dim]")
                await asyncio.sleep(wait)

        console.print(f"\n[bold green]📊 共成功回复 {self.reply_count}/{len(comments_with_replies)} 条[/bold green]")
        return self.reply_count

    async def _post_single_reply(self, reply_text: str) -> bool:
        """Post a single reply: find 回复 button → click → type → Enter."""
        try:
            # Step 1: Find and click a "回复" button
            target_btn_coro = self._find_reply_button()
            target_btn = await target_btn_coro
            if not target_btn:
                return False

            await target_btn.click()
            await asyncio.sleep(2)

            # Step 2: Check if verification appeared after click
            if await self._is_verification_shown():
                console.print(Panel(
                    "[yellow]🔐 抖音安全验证已触发[/yellow]\n"
                    "请在浏览器窗口中完成验证（输入短信验证码等）\n"
                    "[dim]程序将等待你完成验证后自动继续...[/dim]",
                ))
                if not await self._wait_for_verification(300):  # 5 minute timeout
                    return False
                await asyncio.sleep(2)

            # Step 3: Find the DraftEditor
            draft_editor = self.page.locator(
                '.public-DraftEditor-content[contenteditable="true"]'
            ).first

            if not await draft_editor.is_visible(timeout=5000):
                return False

            # Step 4: Click and type
            await draft_editor.click()
            await asyncio.sleep(0.5)
            await draft_editor.type(reply_text, delay=100)
            await asyncio.sleep(1)

            # Step 5: Press Enter to send
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(2)

            # Step 6: Check if verification appeared after sending
            if await self._is_verification_shown():
                console.print(Panel(
                    "[yellow]🔐 发送后触发安全验证[/yellow]\n"
                    "请在浏览器窗口中完成验证...",
                ))
                await self._wait_for_verification(300)

            # Step 7: Verify send success
            still_visible = await draft_editor.is_visible(timeout=3000)
            return not still_visible

        except Exception as e:
            console.print(f"[red]  ❌ 异常: {e}[/red]")
            return False

    def _find_reply_button(self):
        """Find an available '回复' button (synchronous)."""
        all_els = self.page.locator('span, div').filter(has_text='回复')

        async def find():
            count = await all_els.count()
            for i in range(count):
                try:
                    text = await all_els.nth(i).text_content()
                    if text and text.strip() == "回复" and await all_els.nth(i).is_visible():
                        return all_els.nth(i)
                except Exception:
                    continue
            return None

        return find()

    async def _wait_for_verification(self, timeout: int = 300) -> bool:
        """Wait for security verification to be completed by user.
        Returns True when verification is gone, False on timeout."""
        if not await self._is_verification_shown():
            return True

        # Take a screenshot to help user see
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            path = f"/Users/mouwenhu/Desktop/抖音验证_{timestamp}.png"
            await self.page.screenshot(path=path)
            console.print(f"[dim]已截图保存到: {path}[/dim]")
        except Exception:
            pass

        console.print(f"[yellow]⏳ 等待验证完成（最长{timeout}秒）...[/yellow]")
        for i in range(timeout):
            await asyncio.sleep(1)
            if not await self._is_verification_shown():
                console.print("[green]  ✅ 验证已通过，继续回复[/green]")
                return True
            if i % 30 == 0 and i > 0:
                console.print(f"[dim]  仍在等待验证...（已等待{i}秒）[/dim]")

        console.print("[red]  ❌ 验证超时，跳过[/red]")
        return False

    async def _is_verification_shown(self) -> bool:
        """Check if security verification overlay is visible."""
        try:
            # Check for various verification popup patterns
            selectors = [
                '.second-verify-mask',
                '[class*="captcha"]',
                '[class*="verify"]',
                '#uc-second-verify',
                'div:has-text("短信验证码")',
                'div:has-text("安全验证")',
            ]
            for sel in selectors:
                el = self.page.locator(sel).first
                if await el.is_visible(timeout=500):
                    return True
            return False
        except Exception:
            return False
