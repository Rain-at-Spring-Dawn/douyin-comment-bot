"""Douyin QR code login module using Playwright."""
import asyncio
import json
from pathlib import Path

from playwright.async_api import BrowserContext, Page
from rich.console import Console

from config import config

console = Console()


class DouyinLogin:
    """Handles Douyin login via QR code with persistent browser state."""

    def __init__(self):
        self.state_dir = Path(config.browser_data_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "login_state.json"

    async def ensure_login(self, context: BrowserContext) -> bool:
        """Check if already logged in, otherwise prompt QR login."""
        # Try to restore saved state
        if self.state_file.exists():
            console.print("[dim]发现已保存的登录状态，正在恢复...[/dim]")
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                await context.add_cookies(state.get("cookies", []))
                if "local_storage" in state:
                    page = await context.new_page()
                    await page.goto(config.dy_index_url, wait_until="domcontentloaded", timeout=15000)
                    await page.evaluate(
                        "items => items.forEach(([k, v]) => localStorage.setItem(k, v))",
                        list(state["local_storage"].items()),
                    )
                    await page.close()
            except Exception as e:
                console.print(f"[yellow]恢复登录状态失败: {e}，将重新登录[/yellow]")

        # Verify login status
        page = await context.new_page()
        try:
            await page.goto(config.dy_index_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            is_logged_in = await self._check_login(page)
            if is_logged_in:
                console.print("[green]✅ 登录状态有效[/green]")
                await page.close()
                return True
        except Exception as e:
            console.print(f"[yellow]检查登录状态时出错: {e}[/yellow]")

        await page.close()
        return await self._qr_login(context)

    async def _check_login(self, page: Page) -> bool:
        """Check if current session is logged in to Douyin."""
        try:
            result = await page.evaluate("""
                () => {
                    try {
                        const hasSession = document.cookie.includes('sessionid');
                        return { hasSession: hasSession };
                    } catch(e) {
                        return { error: e.message };
                    }
                }
            """)
            if isinstance(result, dict):
                return result.get("hasSession", False)
            return False
        except Exception:
            return False

    async def _qr_login(self, context: BrowserContext) -> bool:
        """Perform QR code login."""
        console.print("[yellow]📱 需要登录抖音[/yellow]")
        page = await context.new_page()
        await page.goto(config.dy_index_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)

        try:
            # Try to open login dialog
            login_selectors = [
                ".login-button",
                ".login-btn",
                "[class*='login']",
                "button:has-text('登录')",
                ".user-info-avatar",
            ]
            for sel in login_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        console.print("[dim]已点击登录按钮[/dim]")
                        await asyncio.sleep(2)
                        break
                except Exception:
                    continue

            console.print("[bold yellow]⏳ 请用抖音扫描二维码登录...[/bold yellow]")
            console.print("[dim]二维码可能出现在页面中央或弹窗中，请查看浏览器窗口[/dim]")

            await page.screenshot(path=str(self.state_dir / "qrcode.png"))

            # Wait for login (check cookies periodically)
            for _ in range(120):
                await asyncio.sleep(1)
                try:
                    cookies = await context.cookies()
                    has_session = any("sessionid" in c.get("name", "") for c in cookies)
                    if has_session:
                        console.print("[green]✅ 登录成功![/green]")
                        await self._save_state(context)
                        await page.close()
                        return True
                except Exception:
                    continue

            console.print("[red]❌ 登录超时（2分钟），请重试[/red]")
            await page.close()
            return False

        except Exception as e:
            console.print(f"[red]登录过程出错: {e}[/red]")
            await page.close()
            return False

    async def _save_state(self, context: BrowserContext):
        """Save browser state for future logins."""
        try:
            cookies = await context.cookies()
            pages = context.pages
            local_storage = {}
            if pages:
                try:
                    local_storage = await pages[0].evaluate("() => ({...localStorage})")
                except Exception:
                    pass

            state = {"cookies": cookies, "local_storage": local_storage}
            with open(self.state_file, "w") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            console.print("[green]💾 登录状态已保存[/green]")
        except Exception as e:
            console.print(f"[yellow]保存登录状态失败: {e}[/yellow]")
