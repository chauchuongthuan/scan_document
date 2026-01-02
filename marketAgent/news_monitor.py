import feedparser
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from colorama import Fore, Style, init
import re

# Khởi tạo màu sắc
init(autoreset=True)

class CoffeeNewsMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.seen_links = set()

        # --- CẤU HÌNH TỪ KHÓA (QUAN TRỌNG) ---
        # Nhóm 1: Luôn lấy nếu xuất hiện (trực tiếp về cà phê)
        self.keywords_priority = [
            "cà phê", "cafe", "coffee", "giá nông sản", "hồ tiêu", "tiêu điều", "xuất khẩu nông sản"
        ]

        # Nhóm 2: Từ khóa Thiên tai/Thời tiết (Phải đi kèm với địa danh ở Nhóm 3)
        self.keywords_disaster = [
            "thiên tai", "bão", "lũ", "lụt", "sạt lở", "mưa lớn", "hạn hán", 
            "nắng nóng", "thời tiết", "áp thấp", "thủy điện xả lũ", "ngập úng",
            "vụ mùa", "mất mùa", "thu hoạch"
        ]

        # Nhóm 3: Địa danh Tây Nguyên (Bao gồm cả không dấu và có dấu)
        self.keywords_region = [
            "tây nguyên", "tay nguyen",
            "gia lai", 
            "đắk lắk", "dak lak", "daklak", 
            "đắk nông", "dak nong", "daknong", 
            "kon tum", "lam dong", "lâm đồng", "đà lạt"
        ]

        # --- CẤU HÌNH NGUỒN TIN ---
        self.rss_sources = {
            "Báo Chính Phủ": "https://baochinhphu.vn/Rss/thoi-su.rss", # Mới thêm
            "VnExpress": "https://vnexpress.net/rss/thoi-su.rss",
            "VnExpress (Kinh doanh)": "https://vnexpress.net/rss/kinh-doanh.rss",
            "Tuổi Trẻ": "https://tuoitre.vn/rss/thoi-su.rss",
            "Thanh Niên": "https://thanhnien.vn/rss/thoi-su.rss",
            "VietnamNet": "https://vietnamnet.vn/rss/thoi-su.rss",
            "Báo Mới": "https://baomoi.com/rss.xml",
            # Thêm CafeF để bắt tin giá cả thị trường nhanh hơn
            "CafeF (Thị trường)": "https://cafef.vn/rss/thi-truong.rss" 
        }

        self.html_sources = [
            {
                "name": "Zing News",
                "url": "https://znews.vn/xa-hoi.html", # Chỉ quét mục Xã hội để tìm thiên tai
                "selector": "p.article-title a",
                "domain_prefix": ""
            }
            # Đã bỏ NDH vì hiện tại không ổn định, CafeF (RSS) thay thế tốt hơn
        ]

    def get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S %d/%m")

    def is_relevant(self, title, summary=""):
        """
        Hàm lọc tin tức:
        1. Nếu tiêu đề/tóm tắt chứa từ khóa Cà phê -> LẤY NGAY
        2. Nếu tiêu đề/tóm tắt chứa (Thiên tai/Thời tiết) VÀ (Địa danh Tây Nguyên) -> LẤY NGAY
        """
        content = (title + " " + summary).lower()
        
        # Check 1: Tin về cà phê
        for k in self.keywords_priority:
            if k in content:
                return True, "TIN CÀ PHÊ/NÔNG SẢN"

        # Check 2: Tin thiên tai + Địa điểm
        has_disaster = any(k in content for k in self.keywords_disaster)
        has_region = any(k in content for k in self.keywords_region)

        if has_disaster and has_region:
            return True, "CẢNH BÁO THIÊN TAI TÂY NGUYÊN"
            
        return False, None

    def parse_rss(self, name, url):
        try:
            feed = feedparser.parse(url)
            found_articles = []
            
            for entry in feed.entries[:10]: # Quét sâu hơn (10 tin) để không bỏ sót
                link = entry.link
                title = entry.title
                summary = getattr(entry, 'summary', '') # Lấy tóm tắt nếu có
                
                if link not in self.seen_links:
                    self.seen_links.add(link)
                    
                    # KIỂM TRA TỪ KHÓA
                    relevant, tag = self.is_relevant(title, summary)
                    if relevant:
                        found_articles.append((title, link, tag))
                        
            return found_articles
        except Exception as e:
            print(f"{Fore.RED}[Error] {name}: {e}")
            return []

    def parse_html(self, source_config):
        name = source_config['name']
        url = source_config['url']
        selector = source_config['selector']
        prefix = source_config.get('domain_prefix', '')
        
        found_articles = []
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.select(selector)
                
                for item in links[:10]:
                    title = item.get_text().strip()
                    href = item.get('href')
                    if not href: continue
                    full_link = href if href.startswith('http') else f"{prefix}{href}"
                    
                    if full_link not in self.seen_links:
                        self.seen_links.add(full_link)
                        
                        # HTML thường không lấy được summary dễ dàng, chỉ check title
                        relevant, tag = self.is_relevant(title)
                        if relevant:
                            found_articles.append((title, full_link, tag))
        except Exception as e:
            print(f"{Fore.RED}[Error] {name}: {e}")
            
        return found_articles

    def run(self, refresh_rate=120): # Tăng thời gian nghỉ lên 2 phút vì quét nhiều nguồn
        print(f"{Fore.CYAN}=== MONITOR TÂY NGUYÊN & CÀ PHÊ ({self.get_timestamp()}) ===")
        print(f"Đang theo dõi các từ khóa: {self.keywords_region[0]}..., {self.keywords_disaster[0]}..., {self.keywords_priority[0]}...")
        print("Đang khởi tạo dữ liệu nền (bỏ qua tin cũ)...")
        
        # Lần đầu chạy để nạp cache, không in
        self.scan_all(initial=True)
        print(f"{Fore.GREEN}Hệ thống đã sẵn sàng. Đang canh tin mới...\n")

        while True:
            try:
                self.scan_all(initial=False)
                time.sleep(refresh_rate)
            except KeyboardInterrupt:
                break

    def scan_all(self, initial=False):
        for name, url in self.rss_sources.items():
            articles = self.parse_rss(name, url)
            if not initial and articles:
                self.print_news(name, articles)

        for source in self.html_sources:
            articles = self.parse_html(source)
            if not initial and articles:
                self.print_news(source['name'], articles)

    def print_news(self, source_name, articles):
        for title, link, tag in articles:
            # Màu đỏ cho cảnh báo thiên tai, Màu xanh cho tin cà phê
            tag_color = Fore.RED if "THIÊN TAI" in tag else Fore.GREEN
            
            print(f"\n{Style.BRIGHT}[{self.get_timestamp()}] {tag_color}★ {tag} ★")
            print(f"{Fore.WHITE}Nguồn: {source_name}")
            print(f"{Fore.YELLOW}Tiêu đề: {title}")
            print(f"{Fore.CYAN}Link: {link}")
            print("-" * 50)
            
            # Âm thanh beep cảnh báo (trên Windows/Mac) khi có tin quan trọng
            print('\a') 

if __name__ == "__main__":
    monitor = CoffeeNewsMonitor()
    # Khuyên dùng 120s (2 phút) để đảm bảo không bị block IP khi quét nhiều nguồn
    monitor.run(refresh_rate=120)