from playwright.sync_api import sync_playwright
import re

def search_afr(keyword):
    url = "https://www.afr.com"
    print("keyword", keyword)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url)
            page.locator("button[data-testid='Header-searchButton']").first.click()
            page.fill("input[data-testid='SearchInput-input']", keyword)
            # search
            page.locator("button[data-testid='SearchInput-submit-button']").first.click()
            # page.locator("label[for='sortByLatest']").click()
            # print(4.5) # Add a print statement to track the new step
            # page.locator("button[data-testid='Search-ApplyFilter']").click()
            # LẤY 5 BÀI
            page.wait_for_selector('div[data-testid="StoryTileBase"]', timeout=15000)
            items = page.locator('div[data-testid="StoryTileBase"]').all()[:10]
            results = []
            for item in items:
                link_locator = item.locator('a[href]').last
                title = item.locator('a._73414cb90844eda9-headlineLink').inner_text()
                link = link_locator.get_attribute("href")

                if link.startswith("/"):
                    link = "https://www.afr.com" + link
                
                results.append({
                    "title": title,
                    "link": link,
                })
            
            browser.close()
            print("results", results)
            return {
                "articles": results
            }
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"articles": []}
        
        finally:
            print("finally")
            browser.close()

if __name__ == "__main__":
    articles = search_afr("coffee")
    for a in articles:
        print(a)