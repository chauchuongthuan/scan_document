import feedparser
import time
import json
from datetime import datetime, timedelta
from time import mktime
from colorama import Fore, Style, init
import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dateutil import parser as date_parser
from dotenv import load_dotenv
load_dotenv()
# ---> BỔ SUNG THƯ VIỆN NÀY ĐỂ XỬ LÝ URL
from urllib.parse import urlparse, urlunparse 
# <---
init(autoreset=True)

try:
    project_path = 'D:/PER_WORKSPACE/scan_document'
    sys.path.append(project_path) 
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee.settings')
    django.setup()
except Exception as e:
    # Bắt exception cụ thể để in ra lỗi chính xác hơn nếu Django thất bại
    print(f"{Fore.RED}LỖI CẤU HÌNH DJANGO: {e}. Vui lòng kiểm tra lại tên project/app và settings.")
    print(f"{Fore.RED}Script sẽ không thể tương tác với Database.")

from scan_news.models import DailyNewsFromVietNamSign, KeywordGroup, ScanRule
from django.db.models import F

gg_studio_key = os.getenv("GG_AI_STUDIO_KEY", "")
# --- CẤU HÌNH API ---
client = genai.Client(api_key=gg_studio_key)

class NewsScanner:
    def __init__(self, days_back=0):
        self.seen_links = set()
        self.seen_titles = set()
        self.sign_summary = 0 

        # Lấy mốc thời gian
        now = datetime.now()
        cutoff_today = now.replace(hour=0, minute=30, second=0, microsecond=0)
        if now < cutoff_today:
            self.current_accounting_date = (now - timedelta(days=1 + days_back)).date()
            self.start_time = cutoff_today - timedelta(days=1 + days_back)
        else:
            self.current_accounting_date = (now - timedelta(days=days_back)).date()
            self.start_time = cutoff_today - timedelta(days=days_back)
        
        print(f"{Fore.YELLOW}>>> QUÉT TIN TỪ: {self.start_time.strftime('%H:%M %d/%m/%Y')} ĐẾN NAY <<<\n")

        # --- CẬP NHẬT NGUỒN RSS ---
        self.rss_sources = {
            "Google News (Báo Daklak)": "https://news.google.com/rss/search?q=when:24h+site:baodaklak.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Gia Lai)": "https://news.google.com/rss/search?q=when:24h+site:baogialai.com.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Quãng Ngãi)": "https://news.google.com/rss/search?q=when:24h+site:baoquangngai.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Quảng Trị)": "https://news.google.com/rss/search?q=when:24h+site:baoquangtri.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Đồng Nai)": "https://news.google.com/rss/search?q=when:24h+site:baodongnai.com.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Sơn La)": "https://news.google.com/rss/search?q=when:24h+site:baosonla.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Google News (Báo Điện Biên)": "https://news.google.com/rss/search?q=when:24h+site:dienbientv.vn&hl=vi&gl=VN&ceid=VN:vi",

            "Nông nghiệp môi trường (Thời sự)": "https://nongnghiepmoitruong.vn/thoi-su.rss",
            "Nông nghiệp môi trường (Nông nghiệp)": "https://nongnghiepmoitruong.vn/nong-nghiep.rss",
            "Nông nghiệp môi trường (Nông nghiệp & Môi trường)": "https://nongnghiepmoitruong.vn/thoi-su-nong-nghiep-moi-truong.rss",

            "Báo Lâm Đồng (Thuế - Tài chính)": "https://baolamdong.vn/rss/kinh-te/thue-tai-chinh",
            "Báo Lâm Đồng (Kinh tế)": "https://baolamdong.vn/rss/kinh-te",
            "Báo Lâm Đồng (Đời sống)": "https://baolamdong.vn/rss/doi-song",
            "Báo Lâm Đồng (Tin tức Lâm Đồng)": "https://baolamdong.vn/rss/video/tin-tuc-lam-dong",
            "Báo Lâm Đồng (Thời sự)": "https://baolamdong.vn/rss/thoi-su",
            "Báo Lâm Đồng (Thời sự Lâm Đồng)": "https://baolamdong.vn/rss/thoi-su/thoi-su-lam-dong",

            "Báo Chính Phủ (Home)": "https://baochinhphu.vn/home.rss",
            "Báo Chính Phủ (Xã hội)": "https://baochinhphu.vn/xa-hoi.rss",
            "Báo Chính Phủ (Thời sự)": "https://baochinhphu.vn/thoi-su.rss",

            "VnExpress (Thời sự)": "https://vnexpress.net/rss/thoi-su.rss",
            "VnExpress (Tin mới nhất)": "https://vnexpress.net/rss/tin-moi-nhat.rss",    
        }

    def normalize_link(self, link):
        """
        Chuẩn hóa URL bằng cách loại bỏ query parameters và fragment.
        """
        try:
            parsed = urlparse(link)
            # Tạo lại URL chỉ với scheme, netloc (domain) và path
            normalized_link = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            # Loại bỏ dấu slash (/) cuối cùng nếu có
            if normalized_link.endswith('/'):
                normalized_link = normalized_link[:-1]
            return normalized_link
        except Exception:
            return link # Trả về link gốc nếu có lỗi

    def fetch_full_content(self, url):
        """
        Truy cập vào link bài viết để lấy toàn bộ nội dung văn bản.
        """
        try:
            # Fake User-Agent để không bị chặn
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # Tăng timeout một chút
            response = requests.get(url, headers=headers, timeout=15) 
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                full_text = ' '.join([p.get_text() for p in paragraphs])
                return full_text
            return ""
        except Exception as e:
            # print(f"Lỗi khi lấy nội dung {url}: {e}")
            return ""

    def get_accounting_date(self, pub_date):
        """
        Tính ngày ghi nhận dựa trên quy tắc 00:30 AM.
        """
        if not pub_date:
            pub_date = datetime.now()
            
        cutoff = pub_date.replace(hour=0, minute=30, second=0, microsecond=0)
        
        if pub_date < cutoff:
            return (pub_date - timedelta(days=1)).date()
        return pub_date.date()

    def update_db_sign(self, pub_date, sign):
        """
        Cập nhật hoặc tạo mới bản ghi trong Database theo ngày kế toán.
        """
        if sign not in ["+", "-"]:
            return 0, self.get_accounting_date(pub_date) # Neutral không thay đổi điểm
            
        acc_date = self.get_accounting_date(pub_date)
        
        try:
            record, created = DailyNewsFromVietNamSign.objects.get_or_create(
                date=acc_date,
                defaults={'sign_summary': 0}
            )
        
            if sign == "+":
                record.sign_summary = F('sign_summary') + 1
            elif sign == "-":
                record.sign_summary = F('sign_summary') - 1
                
            record.save()
            
            record.refresh_from_db()
            return record.sign_summary, acc_date
        except Exception as e:
            print(f"{Fore.RED}LỖI DB (Update): {e}")
            return 0, acc_date


    def check_relevance_and_content(self, title, summary, link):
        """
        Logic kết hợp giữa các group keyword dựa trên ScanRule từ Database.
        """
        raw_text = (title + " " + summary).lower()
        
        # 1. KIỂM TRA NHÓM TỪ KHÓA LOẠI BỎ (IGNORE)
        # Tìm group có tên là 'ignore' (không phân biệt hoa thường)
        ignore_group = KeywordGroup.objects.filter(name__icontains="ignore").first()
        if ignore_group:
            ignore_keywords = ignore_group.get_keyword_list()
            if any(k in raw_text for k in ignore_keywords):
                return False, None, ""

        # 2. TRUY VẤN TẤT CẢ CÁC QUY TẮC (SCAN RULE) ĐANG HOẠT ĐỘNG
        # prefetch_related để tối ưu truy vấn database
        active_rules = ScanRule.objects.filter(is_active=True).prefetch_related('keyword_groups')

        for rule in active_rules:
            groups = rule.keyword_groups.all()
            if not groups:
                continue

            # Kiểm tra sự xuất hiện của từng nhóm trong văn bản
            match_results = []
            for group in groups:
                keywords = group.get_keyword_list()
                has_match = any(k in raw_text for k in keywords)
                match_results.append(has_match)

            # ÁP DỤNG LOGIC KẾT HỢP (AND/OR) CỦA RULE
            if rule.logic_type == 'AND':
                # Phải thỏa mãn TẤT CẢ các nhóm được chọn trong Rule
                is_satisfied = all(match_results) if match_results else False
            else:
                # Chỉ cần thỏa mãn MỘT TRONG các nhóm được chọn trong Rule
                is_satisfied = any(match_results) if match_results else False

            # 3. XỬ LÝ KHI RULE THỎA MÃN
            if is_satisfied:
                # Lấy nội dung đầy đủ để phân tích sâu hơn
                full_content = self.fetch_full_content(link)
                
                # --- LOGIC ĐẶC BIỆT: Ràng buộc bổ sung cho tin Thiên Tai ---
                # Nếu Tag chứa chữ "THIÊN TAI", ta kiểm tra thêm xem Body có nhắc đến "Cà phê" không
                if "tin thiên tai vùng trồng" in rule.log_tag.upper():
                    priority_group = KeywordGroup.objects.filter(name__icontains="priority").first()
                    if priority_group:
                        priority_keywords = priority_group.get_keyword_list()
                        # Nếu trong body bài thiên tai không có từ khóa priority thì bỏ qua rule này
                        if not any(k in full_content.lower() for k in priority_keywords):
                            continue 
                
                # Trả về kết quả với Log Tag được cấu hình trong Rule
                return True, rule.log_tag, (title + "\n" + full_content[:3000])

        return False, None, ""

    def gemini_analyze(self, text_content): 
        """
        Phân tích nội dung bài viết bằng Gemini.
        """
        prompt = f"""
            You are a professional coffee market analyst. Analyze the news content below.
            
            CONTENT TO ANALYZE:
            "{text_content}"

            INSTRUCTIONS:
            1. **Relevance Check:** Does the content explicitly mention that weather/disaster is affecting coffee/agriculture production, harvest, or logistics?
               - IGNORE: Flooding in residential areas only, saving people, traffic jams without mentioning crops.
               - ACCEPT: "Coffee harvest delayed by rain", "Floods damaged crops", "Landslides blocked coffee transport", "Drought reduces yield".
            
            2. **Determine Sign:**
               - "+": Bullish (Price UP) -> Supply shortage, crop damage, harvest delay, logistics blocked.
               - "-": Bearish (Price DOWN) -> Good weather, bumper crop, supply unlock.
               - "neutral": Irrelevant or balanced.

            RETURN JSON ONLY:
            {{
                "sign": "+", 
                "explanation": "Brief reasoning (max 20 words)."
            }}
        """
        retries = 2
        for i in range(retries):
            try:
                # response = client.models.generate_content(
                #     model='gemini-2.5-flash', 
                #     contents=prompt
                # )
                # text = response.text.strip()
                
                response = ""
                text = response.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                analysis = json.loads(text)
                time.sleep(5) 
                
                # ---> FIX: Dùng keys 'sign' và 'explanation' từ JSON structure
                return analysis.get("sign", "neutral"), analysis.get("explanation", "No explanation")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 60 
                    print(f"{Fore.RED}!!! QUOTA EXCEEDED (429). Đang chờ {wait_time}s để hồi phục...{Style.RESET_ALL}")
                    time.sleep(wait_time)
                    continue 
                else:
                    print(f"{Fore.RED}Lỗi Gemini khác: {e}")
                    return "neutral", "API Error"
        
        return "neutral", "Failed after retries"

    def parse_rss(self, name, url):
        try:
            feed = feedparser.parse(url)
            count = 0
            valid_entries = []
            for entry in feed.entries:
                link = entry.link
                title = entry.title.strip()
                summary = getattr(entry, 'summary', '')

                # 1. KIỂM TRA TRÙNG LẶP (Link & Tiêu đề)
                normalized_link = self.normalize_link(link) 
                clean_title = title.lower() # Chuẩn hóa tiêu đề để so sánh
                
                if normalized_link in self.seen_links or clean_title in self.seen_titles:
                    continue
                
                # 2. ĐÁNH DẤU ĐÃ XEM
                self.seen_links.add(normalized_link)
                self.seen_titles.add(clean_title)

                pub_date = None
                
                # Cách 1: Thử lấy dữ liệu đã được parse sẵn bởi feedparser
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.published_parsed)) + timedelta(hours=7)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.updated_parsed)) + timedelta(hours=7)
                
                # Cách 2: Nếu thất bại, thử parse thủ công từ chuỗi raw string
                if pub_date is None:
                    raw_date = getattr(entry, 'published', getattr(entry, 'updated', None))
                    if raw_date:
                        try:
                            # Tuổi Trẻ thường dùng format: "Tue, 25 Nov 2025 09:11:00 GMT+7"
                            # date_parser rất mạnh, nó cân được hầu hết các định dạng
                            dt = date_parser.parse(raw_date)
                            
                            # Nếu kết quả có timezone, chuyển về naive datetime + 7 tiếng (giả lập logic cũ của bạn)
                            # Hoặc đơn giản là lấy giờ đó nếu parser đã nhận diện đúng +7
                            if dt.tzinfo:
                                # Chuyển về giờ địa phương (nếu server chạy giờ VN) hoặc bỏ tzinfo
                                pub_date = dt.replace(tzinfo=None) 
                            else:
                                pub_date = dt
                        except Exception as e:
                            # print(f"Lỗi parse ngày raw '{raw_date}': {e}")
                            pass

                # Kiểm tra ngày hợp lệ
                if pub_date is None or pub_date < (self.start_time - timedelta(minutes=30)):
                    continue 

                # Nếu thỏa mãn thời gian, đưa vào danh sách chờ xử lý
                valid_entries.append((entry, pub_date))
                
                # --- LOGIC KIỂM TRA NỘI DUNG VÀ RULE ---
                relevant, tag, content_to_analyze = self.check_relevance_and_content(title, summary, link)
                
                if relevant:
                    print(f"{Fore.CYAN}...Đang phân tích: {title[:30]}...")
                    
                    sign, explanation = self.gemini_analyze(content_to_analyze)
                    
                    # === UPDATE DATABASE ===
                    acc_date = self.get_accounting_date(pub_date)
                    obj = DailyNewsFromVietNamSign.objects.filter(date=acc_date).first()
                    # current_summary = 0 
                    current_summary = obj.sign_summary if obj else 0
                    
                    if sign in ["+", "-"]:
                        # current_summary, acc_date = self.update_db_sign(pub_date, sign)
                        if sign == "+":
                            self.sign_summary += 1
                        elif sign == "-":
                            self.sign_summary -= 1
                    
                    acc_date_str = acc_date.strftime('%d/%m/%Y')
                    self.print_news(name, title, link, tag, pub_date, sign, explanation, current_summary, acc_date_str)
                    count += 1
            for entry, pub_date in reversed(valid_entries):
                link = entry.link
                title = entry.title.strip()
                summary = getattr(entry, 'summary', '')

                # Kiểm tra trùng lặp
                normalized_link = self.normalize_link(link) 
                clean_title = title.lower()
                if normalized_link in self.seen_links or clean_title in self.seen_titles:
                    continue
                
                self.seen_links.add(normalized_link)
                self.seen_titles.add(clean_title)

                # Kiểm tra nội dung và phân tích
                relevant, tag, content_to_analyze = self.check_relevance_and_content(title, summary, link)
                if relevant:
                    print(f"{Fore.CYAN}...Đang phân tích: {title[:30]}...")
                    sign, explanation = self.gemini_analyze(content_to_analyze)
                    
                    acc_date = self.get_accounting_date(pub_date)
                    obj = DailyNewsFromVietNamSign.objects.filter(date=acc_date).first()
                    current_summary = obj.sign_summary if obj else 0
                    
                    if sign == "+": self.sign_summary += 1
                    elif sign == "-": self.sign_summary -= 1
                    
                    acc_date_str = acc_date.strftime('%d/%m/%Y')
                    self.print_news(name, title, link, tag, pub_date, sign, explanation, current_summary, acc_date_str)
                    count += 1

            return count
        except Exception as e:
            print(f"RSS Error ({name}): {e}")
            return 0
     
    def print_news(self, source, title, link, tag, pub_time, sign, explanation, current_summary, acc_date_str):
        tag_color = Fore.RED if "THIÊN TAI" in tag else Fore.GREEN
        
        if sign == "+": sign_color = Fore.MAGENTA 
        elif sign == "-": sign_color = Fore.BLUE
        else: sign_color = Fore.WHITE

        if current_summary > 0: sum_color = Fore.MAGENTA 
        elif current_summary < 0: sum_color = Fore.BLUE 
        else: sum_color = Fore.YELLOW

        time_str = pub_time.strftime('%H:%M %d/%m') if pub_time else "Mới cập nhật"
        
        print("-" * 60)
        print(f"{Style.BRIGHT}{tag_color}★ {tag} ★")
        print(f"{Fore.WHITE}Nguồn: {source} | {time_str}")
        print(f"{Fore.YELLOW}{title}")
        print(f"{Fore.CYAN}{link}")
        print(f"{Style.BRIGHT}{sign_color}Title Sign: [{sign}]")
        print(f"{Fore.WHITE}Explanation: {explanation}")
        print(f"{Style.BRIGHT}{sum_color}>>> TỔNG TÍN HIỆU THỊ TRƯỜNG NGÀY {acc_date_str}: {current_summary} <<<")
        print("-" * 60)

    def run(self):
        print(f"{Fore.CYAN}Đang quét RSS History...\n")
        total = 0
        for name, url in self.rss_sources.items():
            print(f"Checking {name}...", end="\r")
            total += self.parse_rss(name, url)
            
        print(f"\n{Fore.GREEN}>>> Đã quét xong lịch sử. Tìm thấy {total} tin.")
        print(f"{Fore.MAGENTA}>>> TỔNG KẾT ĐIỂM KHỞI ĐẦU: {self.sign_summary}")
        print(f"{Fore.CYAN}>>> Đang tiếp tục canh tin mới (Real-time)...")
        
        while True:
            time.sleep(60) 
            for name, url in self.rss_sources.items():
                self.parse_rss(name, url)
    
if __name__ == "__main__":
    scanner = NewsScanner(days_back=0)
    scanner.run()