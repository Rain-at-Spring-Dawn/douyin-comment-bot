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
            except Exception as e:
                console.print(f"[yellow]恢复登录状态失败: {e}，将重新登录[/yellow]")

        # Verify login status with a single page
        page = await context.new_page()
        try:
            await page.goto(config.dy_index_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(4)

            # If we had saved state, also restore local storage now
            if self.state_file.exists():
                try:
                    with open(self.state_file) as f:
                        state = json.load(f)
                    if "local_storage" in state and state["local_storage"]:
                        await page.evaluate(
                            "items => items.forEach(([k, v]) => localStorage.setItem(k, v))",
                            list(state["local_storage"].items()),
                        )
                        # Reload to let the site pick up the restored state
                        await page.reload(wait_until="domcontentloaded")
                        await asyncio.sleep(3)
                except Exception:
                    pass

            is_logged_in = await self._check_login(page)
            if is_logged_in:
                console.print("[green]✅ 登录状态有效[/green]")
                await page.close()
                return True

        except Exception as e:
            console.print(f"[yellow]登录状态检查出错: {e}[/yellow]")

        # Not logged in, do QR login
        console.print("[yellow]📱 需要登录抖音[/yellow]")
        return await self._qr_login(page)

    async def _check_login(self, page: Page) -> bool:
        """Check if logged in by examining cookies and page state."""
        try:
            # Method 1: Check cookies for sessionid
            cookies = await page.context.cookies()
            has_session = any("sessionid" in c.get("name", "") for c in cookies)
            if has_session:
                return True

            # Method 2: Check if we can find user avatar / logged-in indicator
            has_user = await page.evaluate("""
                () => {
                    try {
                        const avatar = document.querySelector(
                            '.user-info-avatar, [class*="avatar-wrapper"], ' +
                            '[class*="userAvatar"], [class*="user-avatar"]'
                        );
                        const noLoginBtn = !document.querySelector(
                            '.login-button, [class*="login-btn"], ' +
                            'button:has-text("登录")'
                        );
                        return avatar !== null || noLoginBtn;
                    } catch(e) {
                        return false;
                    }
                }
            """)
            return has_user
        except Exception:
            return False

    async def _qr_login(self, page: Page) -> bool:
        """Perform QR code login using the given page."""
        try:
            # Open login dialog
            await page.goto(config.dy_index_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)

            login_clicked = False
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
                        login_clicked = True
                        console.print("[dim]已点击登录按钮[/dim]")
                        await asyncio.sleep(2)
                        break
                except Exception:
                    continue

            if not login_clicked:
                console.print("[yellow]未找到登录按钮，可能已经登录或页面结构有变[/yellow]")

            console.print("[bold yellow]⏳ 请用抖音扫描二维码登录...[/bold yellow]")
            console.print("[dim]请在打开的浏览器窗口中扫码，等待自动检测[/dim]")

            await page.screenshot(path=str(self.state_dir / "qrcode.png"))

            # Wait for login - check cookies periodically
            for _ in range(120):
                await asyncio.sleep(1)
                try:
                    if await self._check_login(page):
                        console.print("[green]✅ 登录成功![/green]")
                        await self._save_state(page)
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

    async def _save_state(self, page: Page):
        """Save browser state using Playwright's built-in storage_state."""
        try:
            context = page.context
            cookies = await context.cookies()
            local_storage = {}
            try:
                local_storage = await page.evaluate("() => ({...localStorage})")
            except Exception:
                pass

            state = {"cookies": cookies, "local_storage": local_storage}
            with open(self.state_file, "w") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            console.print(f"[green]💾 登录状态已保存 ({len(cookies)} cookies, {len(local_storage)} items)[/green]")
        except Exception as e:
            console.print(f"[yellow]保存登录状态失败: {e}[/yellow]")
