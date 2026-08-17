# 作者：孙文龙
# 用途：Playwright 批量截取 ifrit Web UI 主要页面，输出到 docs/screenshots
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5001"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("dashboard", "/"),
    ("import", "/import"),
    ("ai", "/ai"),
    ("settings", "/settings"),
    ("reports", "/reports"),
    ("agent", "/agent"),
    ("knowledge", "/knowledge"),
    ("console", "/console"),
]


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5,
        )
        for name, path in PAGES:
            try:
                await page.goto(BASE + path, wait_until="networkidle", timeout=20000)
                await page.wait_for_timeout(1200)
                await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
                print(f"OK  {name}  {path}")
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {name} {path}: {e}", file=sys.stderr)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())