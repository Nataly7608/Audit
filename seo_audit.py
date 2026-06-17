import asyncio, json, os, re, time
from playwright.async_api import async_playwright

URL = "https://www.garshinka.ru"
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "seo-audit-result.json")

async def audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        start = time.time()
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        load_time = time.time() - start

        title = await page.title()
        meta_desc = await page.evaluate("document.querySelector('meta[name=\"description\"]')?.getAttribute('content') || ''")
        meta_keys = await page.evaluate("document.querySelector('meta[name=\"keywords\"]')?.getAttribute('content') || ''")
        h1 = await page.evaluate("document.querySelector('h1')?.textContent?.trim() || ''")
        h_tags = await page.evaluate('''() => {
            const tags = {};
            for (let i = 1; i <= 6; i++) {
                const els = document.querySelectorAll('h' + i);
                if (els.length) tags['h' + i] = Array.from(els).map(e => e.textContent.trim()).slice(0, 10);
            }
            return tags;
        }''')
        canon = await page.evaluate("document.querySelector('link[rel=\"canonical\"]')?.getAttribute('href') || ''")
        lang = await page.evaluate("document.documentElement.getAttribute('lang') || ''")
        og_title = await page.evaluate("document.querySelector('meta[property=\"og:title\"]')?.getAttribute('content') || ''")
        og_desc = await page.evaluate("document.querySelector('meta[property=\"og:description\"]')?.getAttribute('content') || ''")
        og_image = await page.evaluate("document.querySelector('meta[property=\"og:image\"]')?.getAttribute('content') || ''")
        robots = await page.evaluate("document.querySelector('meta[name=\"robots\"]')?.getAttribute('content') || ''")
        viewport_tag = await page.evaluate("document.querySelector('meta[name=\"viewport\"]')?.getAttribute('content') || ''")
        charset = await page.evaluate("document.querySelector('meta[charset]')?.getAttribute('charset') || document.querySelector('meta[http-equiv=\"Content-Type\"]')?.getAttribute('content') || ''")

        # Images alt check
        imgs = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.getAttribute('src')?.slice(0, 100),
                alt: img.getAttribute('alt') || '',
                has_alt: !!img.getAttribute('alt')
            })).slice(0, 50);
        }''')
        imgs_no_alt = [i for i in imgs if not i['has_alt']]

        # Internal links count
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.getAttribute('href'),
                text: a.textContent.trim().slice(0, 50)
            })).slice(0, 100);
        }''')
        internal_links = [l for l in links if l['href'].startswith('/') or 'garshinka.ru' in l['href']]
        external_links = [l for l in links if l['href'].startswith('http') and 'garshinka.ru' not in l['href']]

        # Structure
        has_favicon = bool(await page.evaluate("document.querySelector('link[rel*=\"icon\"]')"))
        has_schema = bool(await page.evaluate("document.querySelector('script[type=\"application/ld+json\"]')"))

        # HTTP status via navigation
        resp_status = None
        resp_headers = None
        async def capture_resp(response):
            nonlocal resp_status, resp_headers
            if response.url == URL or response.url == URL + "/":
                resp_status = response.status
                resp_headers = response.headers
        page.on("response", capture_resp)

        # Content type & size
        content_type = resp_headers.get('content-type', '') if resp_headers else ''

        await browser.close()

        # Robots & sitemap check
        robots_content = ""
        sitemap_urls = []
        try:
            async with async_playwright() as p2:
                b2 = await p2.chromium.launch(headless=True)
                p2_page = await b2.new_page()
                try:
                    resp = await p2_page.goto(URL + "/robots.txt", timeout=10000)
                    if resp and resp.status == 200:
                        robots_content = await p2_page.text_content("pre") or await p2_page.content()
                except: pass
                try:
                    resp = await p2_page.goto(URL + "/sitemap.xml", timeout=10000)
                    if resp and resp.status == 200:
                        content = await p2_page.content()
                        sitemap_urls = re.findall(r'<loc>(.*?)</loc>', content)[:10]
                except: pass
                await b2.close()
        except: pass

        result = {
            "url": URL,
            "load_time_sec": round(load_time, 2),
            "http_status": resp_status,
            "content_type": content_type,
            "title": title,
            "title_length": len(title),
            "meta_description": meta_desc,
            "meta_description_length": len(meta_desc),
            "meta_keywords": meta_keys,
            "h1": h1,
            "headings": h_tags,
            "canonical": canon,
            "lang": lang,
            "charset": charset,
            "viewport": viewport_tag,
            "robots_meta": robots,
            "og_title": og_title,
            "og_description": og_desc,
            "og_image": og_image,
            "has_favicon": has_favicon,
            "has_schema_org": has_schema,
            "images_total": len(imgs),
            "images_without_alt": len(imgs_no_alt),
            "images_sample_no_alt": imgs_no_alt[:5],
            "internal_links_count": len(internal_links),
            "external_links_count": len(external_links),
            "robots_txt_found": bool(robots_content),
            "sitemap_found": bool(sitemap_urls),
            "sitemap_urls_sample": sitemap_urls[:5]
        }

        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Audit saved to {OUTPUT}")
        return result

res = asyncio.run(audit())
for k, v in res.items():
    if not isinstance(v, (list, dict)):
        print(f"{k}: {v}")
