from playwright.sync_api import sync_playwright
import re

def check_gap_kcc1():
    """
    Scrapes US Coffee C futures data from Investing.com and returns
    today's open price, yesterday's close price, and the gap between them.
    """
    url = "https://vn.investing.com/commodities/us-coffee-c-advanced-chart?cid=1186960"
    
    with sync_playwright() as pw:
        # Launch browser in headless mode
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to the page
            page.goto(url, timeout=30000)
            
            # Wait for the bottomText section to load
            page.wait_for_selector("div.bottomText ul.bold", timeout=3000)
            
            # Extract all list items from the bottomText section
            list_items = page.query_selector_all("div.bottomText ul.bold li")
            
            prev_close = None
            open_today = None
            
            # Iterate through list items to find the specific data
            for item in list_items:
                text_content = item.inner_text()
                
                # Check for previous close (Giá đ.cửa hôm trước)
                if "Giá đ.cửa hôm trước" in text_content:
                    # Extract the number using regex
                    match = re.search(r'(\d+\.\d+)', text_content)
                    if match:
                        prev_close = float(match.group(1))
                
                # Check for opening price (Giá mở cửa)
                elif "Giá mở cửa" in text_content:
                    # Extract the number using regex
                    match = re.search(r'(\d+\.\d+)', text_content)
                    if match:
                        open_today = float(match.group(1))
            
            # Alternative method using more specific CSS selectors
            if not prev_close or not open_today:
                # Try to get previous close using more specific selector
                prev_close_element = page.query_selector("div.bottomText ul.bold li:has-text('Giá đ.cửa hôm trước') span[dir='ltr']")
                if prev_close_element:
                    prev_close_text = prev_close_element.inner_text()
                    prev_close = float(re.search(r'(\d+\.\d+)', prev_close_text).group(1))
                
                # Try to get open price using more specific selector
                open_price_element = page.query_selector("div.bottomText ul.bold li:has-text('Giá mở cửa') span[dir='ltr']")
                if open_price_element:
                    open_price_text = open_price_element.inner_text()
                    open_today = float(re.search(r'(\d+\.\d+)', open_price_text).group(1))
            
            # Calculate the gap
            open_gap = round(open_today - prev_close, 2) if (open_today and prev_close) else None
            
            # Return the results in requested format
            return {
                "open_today": open_today,
                "close_yesterday": prev_close,
                "open_gap": open_gap
            }
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return {
                "open_today": None,
                "close_yesterday": None, 
                "open_gap": None
            }
        finally:
            # Close browser
            browser.close()

# Execute the function and print results
if __name__ == "__main__":
    results = check_gap_kcc1()
    print("Scraping Results:")
    print(results)