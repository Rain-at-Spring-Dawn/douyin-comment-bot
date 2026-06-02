"""Post replies to Douyin comments via browser automation."""
import asyncio
from typing import List

from playwright.async_api import Page
from rich.console import Console

from config import config

console = Console()


class ReplyPoster:
    """Post AI-generated replies by clicking reply button → typing → Enter."""

    def __init__(self, page: Page):
        self.page = page
        self.reply_count = 0

    async def post_replies(self, comments_with_replies: List[dict]) -> int:
        """Post replies to comments. Returns number of successfully posted replies."""
        self.reply_count = 0

        # Scroll to load comments first
        for _ in range(3):
            await self.page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(2)

        for i, item in enumerate(comments_with_replies):
            if not item.get("ai_reply"):
                continue

            console.print(f"\n[blue]📤 [{i+1}/{len(comments_with_replies)}] 回复: {item.get('content', '')[:30]}...[/blue]")

            success = await self._post_single_reply(item["ai_reply"])
            if success:
                self.reply_count += 1
                console.print(f"[green]  ✅ 已回复: {item['ai_reply']}[/green]")
            else:
                console.print(f"[red]  ❌ 回复失败[/red]")

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
            # Step 1: Check for and dismiss any security verification
            await self._dismiss_verification_if_needed()

            # Step 2: Find and click a "回复" button (exact text match)
            target_btn = await self._find_reply_button()
            if not target_btn:
                console.print("[yellow]  ⚠️ 未找到可点击的回复按钮[/yellow]")
                return False

            await target_btn.click()
            await asyncio.sleep(2)

            # Step 3: Check if verification appeared after click
            if await self._is_verification_shown():
                console.print("[yellow]  ⚠️ 触发安全验证，等待手动处理...[/yellow]")
                # Wait a bit for user to handle it
                for _ in range(30):
                    await asyncio.sleep(1)
                    if not await self._is_verification_shown():
                        console.print("[green]  ✅ 验证已通过[/green]")
                        break
                else:
                    console.print("[red]  ❌ 验证超时[/red]")
                    return False

            # Step 4: Find the DraftEditor
            draft_editor = self.page.locator(
                '.public-DraftEditor-content[contenteditable="true"]'
            ).first

            if not await draft_editor.is_visible(timeout=5000):
                console.print("[yellow]  ⚠️ 未找到回复输入框[/yellow]")
                return False

            # Step 5: Click and type
            await draft_editor.click()
            await asyncio.sleep(0.5)
            await draft_editor.type(reply_text, delay=80)
            await asyncio.sleep(1)

            # Step 6: Press Enter to send
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(2)

            # Step 7: Verify - editor should disappear
            still_visible = await draft_editor.is_visible(timeout=3000)
            return not still_visible

        except Exception as e:
            console.print(f"[red]  ❌ 回复异常: {e}[/red]")
            return False

    async def _find_reply_button(self):
        """Find an available '回复' button."""
        all_els = self.page.locator('span, div').filter(has_text='回复')
        count = await all_els.count()

        for i in range(count):
            try:
                text = await all_els.nth(i).text_content()
                if text and text.strip() == "回复":
                    btn = all_els.nth(i)
                    if await btn.is_visible():
                        return btn
            except Exception:
                continue
        return None

    async def _dismiss_verification_if_needed(self):
        """Check and dismiss any verification popup."""
        if await self._is_verification_shown():
            console.print("[yellow]  ⚠️ 检测到安全验证弹窗，请手动完成验证...[/yellow]")
            # Wait for user to complete it
            for _ in range(60):
                await asyncio.sleep(1)
                if not await self._is_verification_shown():
                    console.print("[green]  ✅ 验证已通过[/green]")
                    return True
            console.print("[red]  ❌ 验证超时（60秒）[/red]")
            return False
        return True

    async def _is_verification_shown(self) -> bool:
        """Check if security verification overlay is visible."""
        try:
            mask = self.page.locator('.second-verify-mask').first
            return await mask.is_visible(timeout=1000)
        except Exception:
            return False
