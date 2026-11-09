import asyncio
from playwright.async_api import async_playwright
from config import TARGET_SITES

async def scrape_hadara(page):
    """לוגיקת חילוץ ספציפית לאתר הדרא"""
    print("Starting to extract products from Hadara...")
    
    # המתנה להופעת כרטיסי המוצרים בעמוד
    await page.wait_for_selector("product-item", timeout=10000)
    
    # שליפת כל כרטיסי המוצרים בעמוד
    product_items = await page.query_selector_all("product-item")
    print(f"found {len(product_items)} products on Hadara page.")

    for item in product_items:
        try:
            # שליפת תמונת המוצר והשם מתוך ה-alt
            img_element = await item.query_selector("img")
            if img_element:
                name = await img_element.get_attribute("alt")
                image_url = await img_element.get_attribute("src")
            else:
                name = "Unknown"
                image_url = ""

            # שליפת הקישור למוצר
            link_element = await item.query_selector("a")
            product_url = await link_element.get_attribute("href") if link_element else ""
            if product_url and product_url.startswith("/"):
                product_url = "https://www.hadara.biz" + product_url

            print(f"שם: {name}")
            print(f"תמונה: {image_url}")
            print(f"קישור: {product_url}")
            print("-" * 30)

        except Exception as e:
            print(f"Error extracting product item: {e}")

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        for site in TARGET_SITES:
            print(f"\nMoving to: {site['designer_name']} - {site['url']}")
            try:
                await page.goto(site["url"], timeout=60000)
                await page.wait_for_timeout(3000)

                # כרגע נפעיל את הלוגיקה הייעודית אם זו הדרא
                if site['designer_name'] == "הדרא":
                    await scrape_hadara(page)
                else:
                    print(f"Scraping logic for {site['designer_name']} will be added soon!")

            except Exception as e:
                print(f"Error scraping {site['designer_name']}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())