"""
Playwright browser helper — used ONLY when a scraper declares needs_js = True.

Imported lazily so the application starts without Playwright installed.
Run `playwright install chromium` once to enable JS-rendered scrapers.

Usage:
    async with browser_page(url) as page:
        html = await page.content()
"""

import asyncio
import contextlib
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# Chromium launch args optimised for CI / container environments
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-setuid-sandbox",
    "--single-process",
]

# Block resource types that slow page load and aren't needed for scraping
BLOCKED_RESOURCE_TYPES = {"image", "font", "media", "stylesheet"}


@contextlib.asynccontextmanager
async def browser_page(
    url: str,
    *,
    wait_until: str = "networkidle",
    timeout_ms: int = 30_000,
    extra_headers: dict | None = None,
) -> AsyncIterator:
    """
    Context manager that opens a Playwright Chromium page, navigates to url,
    waits for the page to settle, then yields the page object.
    Always closes the browser context on exit.

    Args:
        url: Target URL.
        wait_until: Playwright navigation wait-until event.
        timeout_ms: Navigation timeout in milliseconds.
        extra_headers: Additional request headers.

    Yields:
        playwright.async_api.Page

    Raises:
        ImportError if playwright is not installed.
        playwright.async_api.Error on navigation failure.
    """
    try:
        from playwright.async_api import async_playwright  # lazy import
    except ImportError as exc:
        raise ImportError(
            "Playwright is not installed. Run: playwright install chromium"
        ) from exc

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=CHROMIUM_ARGS)
        context = await browser.new_context(
            user_agent="JobBridge/1.0 (+https://github.com/jobbridge)",
            extra_http_headers=extra_headers or {},
        )
        page = await context.new_page()

        # Block unnecessary resource types
        async def _block(route, request):
            if request.resource_type in BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", _block)

        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            yield page
        finally:
            await context.close()
            await browser.close()


async def get_page_html(
    url: str,
    *,
    wait_until: str = "networkidle",
    timeout_ms: int = 30_000,
) -> str:
    """Convenience wrapper: open page, return full HTML, close."""
    async with browser_page(url, wait_until=wait_until, timeout_ms=timeout_ms) as page:
        return await page.content()
