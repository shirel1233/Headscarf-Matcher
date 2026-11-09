"""
הרצה:
    python run_scrapers.py                      # סורק את כל האתרים הפעילים ושומר ל-DB
    python run_scrapers.py --dry-run            # סורק ושומר רק לקבצי JSON בתיקיית output (בלי DB)
    python run_scrapers.py --site הדרא          # רק אתר אחד
    python run_scrapers.py --check https://...  # בודק אם האתר הוא Shopify
כל אתר רץ בנפרד: תקלה באחד לא עוצרת את האחרים. אם היתה תקלה, הקוד היציאה הוא 1
(כך ש-GitHub Actions יתריע).
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

from config import TARGET_SITES


def check_site(url):
    base = url.rstrip("/")
    try:
        r = requests.get(
            base + "/products.json",
            params={"limit": 1},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        data = r.json()
        if r.ok and "products" in data:
            print(f"✔ {base} is a Shopify store. Use platform='shopify'.")
            if data["products"]:
                print("  Sample product:", data["products"][0].get("title"))
            return
    except Exception as e:  # noqa: BLE001
        print(f"  (products.json failed: {e})")
    print(f"✘ {base} did not return /products.json. Use platform='html' (send me the HTML).")


def get_scraper(site):
    if site["platform"] == "shopify":
        from shopify_scraper import scrape
    elif site["platform"] == "html":
        from html_scraper import scrape  # מייבא Playwright רק אם צריך
    else:
        raise ValueError(f"Unknown platform: {site['platform']}")
    return scrape


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", help="designer_name של אתר בודד")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", metavar="URL")
    args = parser.parse_args()

    if args.check:
        check_site(args.check)
        return 0

    sites = [s for s in TARGET_SITES if s.get("enabled", True)]
    if args.site:
        sites = [s for s in sites if s["designer_name"] == args.site]
        if not sites:
            print(f"No enabled site named {args.site!r}")
            return 1

    conn = None
    if not args.dry_run:
        from db import get_conn

        conn = get_conn()

    failures = []
    for site in sites:
        name = site["designer_name"]
        print(f"\n=== {name} ===")
        run_started = datetime.now(timezone.utc)
        try:
            scarves = get_scraper(site)(site)
            if not scarves:
                raise RuntimeError("Scraper returned 0 products")
            if args.dry_run:
                os.makedirs("output", exist_ok=True)
                path = os.path.join("output", f"{name}.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(scarves, f, ensure_ascii=False, indent=2)
                print(f"  saved {len(scarves)} products to {path}")
            else:
                from db import save_scarves

                stats = save_scarves(conn, scarves, name, run_started)
                print(f"  DB: {stats}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR in {name}: {e}")
            if conn:
                conn.rollback()
            failures.append(name)

    if conn:
        conn.close()
    if failures:
        print(f"\nFailed sites: {', '.join(failures)}")
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
