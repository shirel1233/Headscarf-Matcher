"""
סורק לחנויות Shopify.

במקום לקרוא HTML, כל חנות Shopify חושפת את כל המוצרים כ-JSON בכתובת:
    https://<האתר>/products.json?limit=250&page=N
זה יציב יותר, מהיר יותר, ומחזיר את *כל* המוצרים עם עימוד (pagination) מסודר.
"""
import time

import requests

from common import UNKNOWN_COLOR, find_first_color, find_pattern, looks_like_scarf

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SmartScarfMatcher/1.0)",
    "Accept": "application/json",
}
COLOR_OPTION_NAMES = {"צבע", "גוון", "color", "colour"}
PAGE_SIZE = 250  # המקסימום ש-Shopify מאפשר


def _get_json(url, params, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 429:  # האתר מבקש להאט
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Rate limited too many times: {url}")


def fetch_all_products(base_url, collection=None, delay=1.0, max_pages=100):
    """מושך את כל המוצרים (כל העמודים) ומסיר כפילויות לפי id."""
    base_url = base_url.rstrip("/")
    path = f"/collections/{collection}/products.json" if collection else "/products.json"
    products = {}
    for page in range(1, max_pages + 1):
        data = _get_json(base_url + path, {"limit": PAGE_SIZE, "page": page})
        batch = data.get("products", [])
        if not batch:
            break
        new = 0
        for p in batch:
            if p["id"] not in products:
                products[p["id"]] = p
                new += 1
        print(f"  page {page}: {len(batch)} products ({new} new)")
        if new == 0:  # הגנה מפני אתר שמחזיר את אותו עמוד שוב ושוב
            break
        time.sleep(delay)
    return list(products.values())


def _tags(p):
    tags = p.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return tags


def _text_blob(p):
    return " ".join([p.get("title", ""), p.get("product_type", ""), " ".join(_tags(p))])


def _color(p, blob):
    for opt in p.get("options", []):
        if opt.get("name", "").strip().lower() in COLOR_OPTION_NAMES:
            values = [v for v in opt.get("values", []) if v]
            if values:
                return ", ".join(values)
    return find_first_color(blob) or UNKNOWN_COLOR


def normalize(p, site):
    """ממיר מוצר Shopify לשורה בטבלת Scarf שלנו."""
    base_url = site["base_url"].rstrip("/")
    blob = _text_blob(p)
    variants = p.get("variants", [])

    prices = []
    for v in variants:
        try:
            prices.append(float(v["price"]))
        except (KeyError, TypeError, ValueError):
            pass

    images = p.get("images") or []
    image_url = images[0]["src"] if images else (p.get("image") or {}).get("src")

    return {
        "externalId": str(p["id"]),
        "name": p.get("title", "").strip(),
        "color": _color(p, blob),
        "pattern": find_pattern(blob),
        "imageUrl": image_url,
        "purchaseUrl": f"{base_url}/products/{p['handle']}",
        "designer": site["designer_name"],
        "price": min(prices) if prices else None,
        "currency": site.get("currency", "ILS"),
        "inStock": any(v.get("available", True) for v in variants) if variants else False,
    }


def scrape(site):
    collections = site.get("collections") or [None]  # None = כל החנות
    raw = {}
    for collection in collections:
        print(f"Fetching {site['designer_name']} ({collection or 'all products'})...")
        for p in fetch_all_products(site["base_url"], collection):
            raw[p["id"]] = p

    mode = site.get("scarf_filter", "keywords")
    kept, skipped = [], []
    for p in raw.values():
        if mode == "all" or looks_like_scarf(_text_blob(p)):
            kept.append(normalize(p, site))
        else:
            skipped.append(p.get("title", ""))

    print(f"  total fetched: {len(raw)} | kept as scarves: {len(kept)} | skipped: {len(skipped)}")
    if skipped:
        print("  examples of skipped products (check none are real scarves):")
        for title in skipped[:10]:
            print(f"    - {title}")
    return kept
