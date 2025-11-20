from playwright.sync_api import sync_playwright
import re

def search_ft(keyword):
    url = "https://www.ft.com"
    
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

            accept_ft_cookies(page)
            keywords = ["coffee", "tariff", "Trump"]
            page.click("a[title='Open search bar']")
            page.fill("#o-header-search-term-primary", keyword)
            # search
            page.locator("form.o-header__search-form >> button.o-header__search-submit").first.click()
        

            # SORT BY DATE
            page.locator(".search-sort__link").nth(1).click()
            page.wait_for_selector("ul.search-results__list")

            # LẤY 5 BÀI
            items = page.locator("ul.search-results__list > li.search-results__list-item").all()[:5]
            results = []
            for item in items:
                title = item.locator(".o-teaser__heading a").inner_text().strip()
                desc = item.locator(".o-teaser__standfirst a").inner_text().strip()
                link = item.locator(".o-teaser__heading a").get_attribute("href")
                time = item.locator(".o-teaser__timestamp").inner_text().strip()
                if link.startswith("/"):
                    link = "https://www.ft.com" + link

                results.append({
                    "title": title,
                    "description": desc,
                    "url": link,
                    "time": time
                })
            browser.close()
            return {
                "articles": results
            }
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"articles": []}
        
        finally:
            browser.close()

def accept_ft_cookies(page):
    print("Đang chờ popup cookies...")

    # Cách 2: Kiểm tra iframe
    print("Đang kiểm tra iframe...")
    for frame in page.frames:
        if frame != page.main_frame:
            try:
                accept_btn = frame.locator("button:has-text('Accept Cookies')")
                if accept_btn.count() > 0:
                    accept_btn.click()
                    print(f"Đã click Accept Cookies trong iframe: {frame.url}")
                    return True
            except:
                continue

    print("Không tìm thấy popup cookies, có thể tiếp tục...")
    return False