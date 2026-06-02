"""Post replies to Douyin comments using Playwright browser automation."""
import asyncio
from typing import List, Optional

from playwright.async_api import Page
from rich.console import Console

from config import config

console = Console()


class ReplyPoster:
    """Post AI-generated replies to Douyin comments via browser automation."""

    def __init__(self, page: Page):
        self.page = page
        self.reply_count = 0

    async def post_replies(self, comments_with_replies: List[dict]) -> int:
        """Post replies to comments. Returns number of successfully posted replies."""
        self.reply_count = 0

        for i, item in enumerate(comments_with_replies):
            if not item.get("ai_reply"):
                continue

            console.print(f"\n[blue]📤 [{i+1}/{len(comments_with_replies)}] 回复评论: {item.get('content', '')[:30]}...[/blue]")

            success = await self._post_single_reply(item)
            if success:
                self.reply_count += 1
                console.print(f"[green]  ✅ 已回复: {item['ai_reply']}[/green]")
            else:
                console.print(f"[red]  ❌ 回复失败[/red]")

            # Wait between replies to avoid detection
            if i < len(comments_with_replies) - 1:
                wait_time = config.reply_interval_seconds
                console.print(f"[dim]⏳ 等待 {wait_time} 秒后继续...[/dim]")
                await asyncio.sleep(wait_time)

        console.print(f"\n[bold green]📊 共成功回复 {self.reply_count}/{len(comments_with_replies)} 条评论[/bold green]")
        return self.reply_count

    async def _post_single_reply(self, item: dict) -> bool:
        """Post a single reply using browser interaction."""
        try:
            reply_text = item["ai_reply"]
            
            # Strategy 1: Try to find and click the reply button
            found = await self._try_click_reply_button(item)
            if not found:
                console.print("[yellow]  ⚠️ 未找到回复按钮，尝试直接JavaScript注入...[/yellow]")
                return await self._try_js_reply(item)

            # Type the reply
            await asyncio.sleep(1)
            
            # Find the reply input and type
            typed = await self._type_reply(reply_text)
            if not typed:
                console.print("[yellow]  ⚠️ 输入框定位失败[/yellow]")
                return False

            # Click send
            await asyncio.sleep(1)
            sent = await self._click_send()
            if not sent:
                console.print("[yellow]  ⚠️ 发送按钮定位失败[/yellow]")
                return False

            await asyncio.sleep(2)
            return True

        except Exception as e:
            console.print(f"[red]  ❌ 回复过程异常: {e}[/red]")
            return False

    async def _try_click_reply_button(self, item: dict) -> bool:
        """Try to find and click the reply/comment button for a specific comment."""
        comment_text = item.get("content", "")
        
        # Strategy: Scroll to find the comment text, then look for nearby reply button
        for attempt in range(3):
            try:
                # Find comment element by text content
                comment_elem = self.page.locator(f"text='{comment_text[:20]}'").first
                if await comment_elem.is_visible(timeout=3000):
                    # Get the comment container
                    comment_container = comment_elem.locator("xpath=ancestor::*[contains(@class, 'comment') or contains(@class, 'dy-comment')][1]")
                    
                    if await comment_container.is_visible(timeout=2000):
                        # Look for reply button inside the container
                        reply_btn = comment_container.locator(
                            '[class*="reply"], [class*="comment"], button:has-text("回复"), [class*="icon-reply"]'
                        ).first
                        
                        if await reply_btn.is_visible(timeout=2000):
                            await reply_btn.click()
                            await asyncio.sleep(1)
                            return True
                
                # Try scrolling down a bit to find it
                await self.page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)

        return False

    async def _type_reply(self, text: str) -> bool:
        """Type reply text into the input field."""
        try:
            # Look for reply input
            input_selectors = [
                '[class*="reply-input"] textarea',
                '[class*="reply-input"] input',
                'textarea[placeholder*="回复"]',
                'input[placeholder*="回复"]',
                '[class*="input"] textarea',
                '[contenteditable="true"]',
                '.reply-box textarea',
            ]
            
            for selector in input_selectors:
                try:
                    input_field = self.page.locator(selector).first
                    if await input_field.is_visible(timeout=2000):
                        await input_field.click()
                        await asyncio.sleep(0.5)
                        await input_field.fill(text)
                        return True
                except Exception:
                    continue

            # Fallback: try to find any visible textarea/input in the reply area
            try:
                active = self.page.locator("textarea, input[type='text'], [contenteditable='true']").last
                if await active.is_visible(timeout=2000):
                    await active.click()
                    await asyncio.sleep(0.5)
                    await active.fill(text)
                    return True
            except Exception:
                pass

            return False
        except Exception as e:
            console.print(f"[red]  ❌ 输入回复文本失败: {e}[/red]")
            return False

    async def _click_send(self) -> bool:
        """Click the send button to post the reply."""
        try:
            send_selectors = [
                'button:has-text("发送")',
                '[class*="send"]',
                '[class*="submit"]',
                'button[class*="btn-primary"]',
            ]
            
            for selector in send_selectors:
                try:
                    send_btn = self.page.locator(selector).first
                    if await send_btn.is_visible(timeout=2000) and await send_btn.is_enabled():
                        await send_btn.click()
                        return True
                except Exception:
                    continue

            # Try pressing Ctrl+Enter or Enter
            try:
                active = self.page.locator("textarea, [contenteditable='true']").last
                if await active.is_visible(timeout=1000):
                    await active.press("Control+Enter")
                    return True
            except Exception:
                pass

            return False
        except Exception as e:
            console.print(f"[red]  ❌ 点击发送失败: {e}[/red]")
            return False

    async def _try_js_reply(self, item: dict) -> bool:
        """Fallback: Use JavaScript injection to attempt reply."""
        reply_text = item["ai_reply"]
        try:
            result = await self.page.evaluate(f"""
                (() => {{
                    // Try to inject reply via any exposed API
                    if (window.__douyin && window.__douyin.reply) {{
                        window.__douyin.reply('{item.get("comment_id", "")}', '{reply_text}');
                        return true;
                    }}
                    return false;
                }})()
            """)
            return bool(result)
        except Exception:
            return False
