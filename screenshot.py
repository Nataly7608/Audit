import asyncio
from playwright.async_api import async_playwright

URL = "https://www.garshinka.ru"
OUTPUT = r"C:\Users\user\Documents\pa-finance.2\tmp\garshinka-main.png"

async def screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=OUTPUT, full_page=False)
        await browser.close()
        print(f"Screenshot saved to {OUTPUT}")

asyncio.run(screenshot())
