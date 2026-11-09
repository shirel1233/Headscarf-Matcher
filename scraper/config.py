"""
הגדרות האתרים לסריקה.

platform:
  "shopify" - אתר Shopify (מומלץ, לא צריך HTML). בדקי עם:  python run_scrapers.py --check https://האתר
  "html"    - אתר אחר, דורש selectors (ראי דוגמה למטה)

scarf_filter:
  "keywords" - שומר רק מוצרים שבשם/תגיות/סוג שלהם יש "מטפחת/צעיף/..." (ראי common.py)
  "all"      - שומר את כל המוצרים בחנות/באוסף (מתאים לאוסף שכולו מטפחות)

collections (Shopify בלבד, אופציונלי):
  רשימת "handle" של אוספים, למשל ["headscarves"] מתוך הכתובת /collections/headscarves
  ריק = כל החנות.
"""

TARGET_SITES = [
    {
        "key": "hadara",
        "display_name": "הדרא",
        "base_url": "https://www.hadara.biz",
        "platform": "shopify",
        "collections": [],
        "scarf_filter": "keywords",
        "currency": "ILS",
        "enabled": True,
    },
    {
        "key": "etcasia",
        "display_name": "אתכסיא",
        "base_url": "https://etcasiart.com",
        "platform": "html",
        "listing_urls": ["https://etcasiart.com/product-category/%D7%9E%D7%98%D7%A4%D7%97%D7%95%D7%AA/"],
        "page_param": "page",
        "scroll": False,
        "selectors": {
            "card": "li.product",
            "name": ".woocommerce-loop-product__title, h2",
            "link": "a",
            "image": "img",
            "price": ".price",
            "sold_out": ".out-of-stock",
        },
        "scarf_filter": "all",
        "currency": "ILS",
        "enabled": True,
    },
    {
        "key": "avia_sason",
        "display_name": "אביה ששון",
        "base_url": "https://aviasason.com",
        "platform": "html",
        "listing_urls": ["https://aviasason.com/product-category/%D7%9E%D7%98%D7%A4%D7%97%D7%95%D7%AA/"],
        "page_param": "paged",
        "scroll": False,
        "selectors": {
            "card": "li.product",
            "name": ".woocommerce-loop-product__title, h2",
            "link": "a",
            "image": "img",
            "price": ".price",
            "sold_out": ".out-of-stock",
        },
        "scarf_filter": "all",
        "currency": "ILS",
        "enabled": True,
    },
    # דוגמה לאתר שאינו Shopify (selectors לדוגמה בלבד, יש להתאים ל-HTML האמיתי):
    # {
    #     "key": "example",            # מזהה טכני באנגלית: משמש ב-DB ובפקודת --site
    #     "display_name": "דוגמה",     # שם לתצוגה בעברית
    #     "base_url": "https://example.co.il",
    #     "platform": "html",
    #     "listing_urls": ["https://example.co.il/category/scarves"],
    #     "page_param": "page",   # שם פרמטר העימוד ב-URL
    #     "scroll": False,        # True אם המוצרים נטענים בגלילה אינסופית
    #     "selectors": {
    #         "card": "li.product",
    #         "name": "h2.title",
    #         "link": "a",
    #         "image": "img",
    #         "price": ".price",
    #         "sold_out": ".sold-out",
    #     },
    #     "scarf_filter": "all",
    #     "enabled": False,
    # },
]
