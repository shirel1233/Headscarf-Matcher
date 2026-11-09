"""
סורק גנרי מבוסס Playwright לאתרים שאינם Shopify.
כל אתר מוגדר ב-config.py דרך "selectors" (איך מזהים כרטיס מוצר, שם, תמונה, קישור).
הסורק עובר על כל עמודי הרשימה עד שלא נמצאים מוצרים חדשים.
"""
import re
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from common import UNKNOWN_COLOR, find_first_color, find_pattern, looks_like_scarf


def _scroll_to_bottom(page, rounds=15):
    last_height = 0
    for _ in range(rounds):
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(1200)
        height = page.evaluate("document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height


def _image_src(img, base_url):
    if not img:
        return None
    for attr in ("data-src", "data-original", "src"):
        val = img.get_attribute(attr)
        if val and not val.startswith("data:"):
            return urljoin(base_url, val)
    srcset = img.get_attribute("srcset") or img.get_attribute("data-srcset")
    if srcset:
        return urljoin(base_url, srcset.split(",")[0].strip().split(" ")[0])
    return None


def _parse_price(text):
    m = re.search(r"(\d[\d,]*\.?\d*)", (text or "").replace("\u200f", ""))
    return float(m.group(1).replace(",", "")) if m else None


def _extract(card, sel, site):
    base_url = site["base_url"]
    link_el = card.query_selector(sel.get("link", "a"))
    href = link_el.get_attribute("href") if link_el else None
    if not href:
        return None
    img = card.query_selector(sel.get("image", "img"))

    name = None
    if sel.get("name"):
        name_el = card.query_selector(sel["name"])
        name = name_el.inner_text().strip() if name_el else None
    if not name and img:
        name = (img.get_attribute("alt") or "").strip()
    if not name:
        return None

    price_el = card.query_selector(sel["price"]) if sel.get("price") else None
    price = _parse_price(price_el.inner_text()) if price_el else None
    sold_out = bool(sel.get("sold_out") and card.query_selector(sel["sold_out"]))

    return {
        "externalId": None,
        "name": name,
        "color": find_first_color(name) or UNKNOWN_COLOR,
        "pattern": find_pattern(name),
        "imageUrl": _image_src(img, base_url),
        "purchaseUrl": urljoin(base_url, href).split("#")[0],
        "designer": site["key"],
        "price": price,
        "currency": site.get("currency", "ILS"),
        "inStock": not sold_out,
    }


def scrape(site):
    sel = site["selectors"]
    items = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="he-IL")
        for listing in site["listing_urls"]:
            for page_no in range(1, site.get("max_pages", 50) + 1):
                sep = "&" if "?" in listing else "?"
                url = listing if page_no == 1 else f"{listing}{sep}{site.get('page_param', 'page')}={page_no}"
                print(f"  {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_selector(sel["card"], timeout=10000)
                except PWTimeout:
                    break
                if site.get("scroll"):
                    _scroll_to_bottom(page)

                new = 0
                for card in page.query_selector_all(sel["card"]):
                    data = _extract(card, sel, site)
                    if data and data["purchaseUrl"] not in items:
                        items[data["purchaseUrl"]] = data
                        new += 1
                print(f"    found {new} new products")
                if new == 0 or site.get("single_page"):
                    break
        browser.close()

    mode = site.get("scarf_filter", "keywords")
    result = [d for d in items.values() if mode == "all" or looks_like_scarf(d["name"])]
    print(f"  total: {len(items)} | kept as scarves: {len(result)}")
    return result
