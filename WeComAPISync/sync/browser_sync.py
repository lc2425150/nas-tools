from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .config import AppConfig


LOGIN_URL = "https://work.weixin.qq.com/wework_admin/loginpage_wx"
ADMIN_URL = "https://work.weixin.qq.com/wework_admin/frame"
APP_DETAIL_URL = "https://work.weixin.qq.com/wework_admin/frame#apps/modApiApp/5629502692701710"


@dataclass
class BrowserResult:
    ok: bool
    verified: bool
    message: str
    screenshot: str = ""


def _is_login_page(page: Page) -> bool:
    url = page.url.lower()
    return "login" in url or "loginpage_wx" in url


def _wait_for_login(page: Page) -> None:
    if not _is_login_page(page):
        return
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_url(
        lambda url: "wework_admin/frame" in url or "wework_admin/manage" in url,
        timeout=180000,
    )


def trusted_ip_config_selector() -> str:
    return "li.app_card:has-text('企业可信IP') a:has-text('配置')"


def merge_ip_list(value: str, ip: str) -> str:
    items = [item.strip() for item in re.split(r"[;\n,，]+", value or "") if item.strip()]
    if ip not in items:
        items.append(ip)
    return ";".join(items)


def _goto_app_detail(page: Page) -> None:
    page.goto(APP_DETAIL_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_selector("text=Moviepilot", timeout=30000)


def _open_trusted_ip_dialog(page: Page) -> bool:
    if page.locator(".js_ipConfig_textarea").count() > 0:
        return True

    selectors = [
        trusted_ip_config_selector(),
        ".js_show_ipConfig_dialog a:has-text('配置')",
        "xpath=//span[contains(normalize-space(.),'企业可信IP')]/ancestor::li[contains(@class,'app_card')]//a[contains(normalize-space(.),'配置')]",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                locator.click(timeout=8000)
                page.wait_for_selector(".js_ipConfig_textarea", timeout=10000)
                return True
        except PlaywrightError:
            continue
    return False


def _fill_ip(page: Page, ip: str) -> bool:
    try:
        textarea = page.locator(".js_ipConfig_textarea").first
        if textarea.count() == 0:
            return False
        current = textarea.input_value(timeout=3000)
        textarea.fill(merge_ip_list(current, ip), timeout=5000)
        return True
    except PlaywrightError:
        return False
    return False


def _click_save(page: Page) -> bool:
    selectors = [
        ".js_ipConfig_confirmBtn",
        "button:has-text('确定')",
        "a:has-text('确定')",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                locator.click(timeout=5000)
                page.wait_for_timeout(1800)
                return True
        except PlaywrightError:
            continue
    return False


def _trusted_ip_dialog_contains_ip(page: Page, ip: str) -> bool:
    try:
        if not _open_trusted_ip_dialog(page):
            return False
        textarea = page.locator(".js_ipConfig_textarea").first
        return ip in [item.strip() for item in re.split(r"[;\n,，]+", textarea.input_value(timeout=3000)) if item.strip()]
    except PlaywrightError:
        return False


def _save_failure(page: Page, screenshot_path: Path) -> str:
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    except PlaywrightError:
        return ""


def sync_ip_with_browser(config: AppConfig, ip: str) -> BrowserResult:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=config.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context_kwargs = {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "viewport": {"width": 1280, "height": 860},
        }
        if config.storage_state_path.exists():
            context_kwargs["storage_state"] = str(config.storage_state_path)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        try:
            page.goto(ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
            _wait_for_login(page)
            context.storage_state(path=str(config.storage_state_path))
            _goto_app_detail(page)

            if _trusted_ip_dialog_contains_ip(page, ip):
                browser.close()
                return BrowserResult(True, True, f"IP {ip} already verified in trusted IP dialog")

            opened = _open_trusted_ip_dialog(page)
            filled = _fill_ip(page, ip)
            saved = _click_save(page)

            if not opened:
                screenshot = _save_failure(page, config.screenshot_path)
                browser.close()
                return BrowserResult(False, False, "trusted IP config dialog not found", screenshot)
            if not filled:
                screenshot = _save_failure(page, config.screenshot_path)
                browser.close()
                return BrowserResult(False, False, "IP input field not found", screenshot)
            if not saved:
                screenshot = _save_failure(page, config.screenshot_path)
                browser.close()
                return BrowserResult(False, False, "save button not found", screenshot)

            page.wait_for_timeout(1500)
            _goto_app_detail(page)
            verified = _trusted_ip_dialog_contains_ip(page, ip)
            context.storage_state(path=str(config.storage_state_path))
            screenshot = "" if verified else _save_failure(page, config.screenshot_path)
            browser.close()
            if verified:
                return BrowserResult(True, True, f"IP {ip} verified in trusted IP dialog")
            return BrowserResult(False, False, f"IP {ip} was submitted but not visible in trusted IP dialog", screenshot)
        except PlaywrightTimeoutError as exc:
            screenshot = _save_failure(page, config.screenshot_path)
            browser.close()
            return BrowserResult(False, False, f"browser timeout: {exc}", screenshot)
        except Exception as exc:
            screenshot = _save_failure(page, config.screenshot_path)
            browser.close()
            return BrowserResult(False, False, f"browser error: {exc}", screenshot)
