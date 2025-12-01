import feedparser
import time
import json
from datetime import datetime, timedelta
from time import mktime
from colorama import Fore, Style, init
import os
import sys
import django
from google import genai
from google.genai import types
init(autoreset=True)
try:
    project_path = 'D:/PER_WORKSPACE/scan_document'
    sys.path.append(project_path) 
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee.settings')
    django.setup()
except:
    print(f"{Fore.RED}LỖI CẤU HÌNH DJANGO: {e}. Vui lòng kiểm tra lại tên project/app và settings.")
    print(f"{Fore.RED}Script sẽ không thể tương tác với Database.")

from marketAgent.models import DailyNewsFromVietNamSign # Thay your_app_name
from django.db.models import F

# --- CẤU HÌNH API ---
# Thay API Key của bạn vào đây
client = genai.Client(api_key="AIzaSyA46hJwJsxpkB-a78FG2j9ryeB4OZ4RbjE")

class NewsScanner:
    def __init__(self):
        self.seen_links = set()
        self.sign_summary = 0 # Biến lưu tổng tín hiệu

        # Lấy mốc thời gian: 1h30 sáng hôm nay
        now = datetime.now()
        cutoff_today = now.replace(hour=1, minute=30, second=0, microsecond=0)
        if now < cutoff_today:
            self.current_accounting_date = (now - timedelta(days=1)).date()
            self.start_time = cutoff_today - timedelta(days=1)
        else:
            self.current_accounting_date = now.date()
            self.start_time = cutoff_today
        
        print(f"{Fore.YELLOW}>>> QUÉT TIN TỪ: {self.start_time.strftime('%H:%M %d/%m/%Y')} ĐẾN NAY <<<\n")

        # --- 1. CẬP NHẬT TỪ KHÓA ---
        self.keywords_priority = [
            "cà phê", "cafe", "coffee", "giá nông sản", "giá cà phê", "nông sản"
        ]
        self.keywords_disaster = [
            "thiên tai", "bão", "lũ", "lụt", "sạt lở", "mưa lớn", "hạn hán", 
            "nắng nóng", "thời tiết", "áp thấp", "ngập úng", "thiệt hại"
        ]
        # Đã bỏ keywords_agriculture theo yêu cầu, dùng Prompt để lọc kỹ hơn
        self.keywords_region = [
            "tây nguyên", "tay nguyen",
            "gia lai", "đắk lắk", "dak lak", "daklak",
            "đắk nông", "dak nong", "daknong",
        ]

        # --- 2. CẬP NHẬT NGUỒN RSS ---
        self.rss_sources = {
            "Nông nghiệp môi trường (Thời sự)": "https://nongnghiepmoitruong.vn/thoi-su.rss",
            "Nông nghiệp môi trường (Nông nghiệp)": "https://nongnghiepmoitruong.vn/nong-nghiep.rss",
            "Nông nghiệp môi trường (Trồng trọt)": "https://nongnghiepmoitruong.vn/trong-trot.rss",
            "Báo Chính Phủ (Home)": "https://baochinhphu.vn/home.rss",
            "Báo Chính Phủ (Xã hội)": "https://baochinhphu.vn/xa-hoi.rss",
            "Báo Chính Phủ (Thời sự)": "https://baochinhphu.vn/thoi-su.rss",
            "VnExpress (Thời sự)": "https://vnexpress.net/rss/thoi-su.rss",
            "VnExpress (Tin mới nhất)": "https://vnexpress.net/rss/tin-moi-nhat.rss",
            "Tuổi Trẻ": "https://tuoitre.vn/rss/thoi-su.rss",
            "Thanh Niên": "https://thanhnien.vn/rss/thoi-su.rss",
            "VietnamNet": "https://vietnamnet.vn/rss/thoi-su.rss",
        }

    def get_accounting_date(self, pub_date):
        """
        Tính ngày ghi nhận dựa trên quy tắc 01:30 AM.
        - Nếu tin ra lúc 01:29 ngày 23/11 -> Tính vào ngày 22/11.
        - Nếu tin ra lúc 01:31 ngày 23/11 -> Tính vào ngày 23/11.
        """
        if not pub_date:
            pub_date = datetime.now()
            
        cutoff = pub_date.replace(hour=1, minute=30, second=0, microsecond=0)
        
        if pub_date < cutoff:
            return (pub_date - timedelta(days=1)).date()
        return pub_date.date()

    def update_db_sign(self, pub_date, sign):
        """
        Cập nhật hoặc tạo mới bản ghi trong Database theo ngày kế toán.
        """
        if sign not in ["+", "-"]:
            return 0 # Neutral không thay đổi điểm
            
        # 1. Xác định ngày kế toán của bài viết đó
        acc_date = self.get_accounting_date(pub_date)
        
        # 2. Get or Create bản ghi cho ngày đó
        # Dùng get_or_create để tránh lỗi nếu chưa có record ngày đó
        record, created = DailyNewsFromVietNamSign.objects.get_or_create(
            date=acc_date,
            defaults={'sign_summary': 0}
        )
        
        # 3. Cập nhật điểm (Atomic update để an toàn hơn)
        if sign == "+":
            record.sign_summary = F('sign_summary') + 1
        elif sign == "-":
            record.sign_summary = F('sign_summary') - 1
            
        record.save()
        
        # 4. Refresh để lấy giá trị số nguyên mới nhất ra hiển thị
        record.refresh_from_db()
        return record.sign_summary, acc_date

    def is_relevant(self, title, summary=""):
        content = (title + " " + summary).lower()
        
        # Check 1: Tin Cà phê (Ưu tiên cao nhất)
        for k in self.keywords_priority:
            if k in content: return True, "TIN CÀ PHÊ/NÔNG SẢN"

        # Check 2: Thiên tai + Vùng (Bỏ qua check nông nghiệp ở bước này, để Gemini check kỹ)
        has_disaster = any(k in content for k in self.keywords_disaster)
        has_region = any(k in content for k in self.keywords_region)
        
        if has_disaster and has_region:
            return True, "CẢNH BÁO THIÊN TAI VÙNG TRỒNG"
            
        return False, None

    def gemini_analyze(self, title):
        """
        Phân tích tiêu đề bằng Gemini với cơ chế Retry khi bị 429 và Prompt lọc nhiễu.
        """
        # Prompt mới: Yêu cầu Gemini đóng vai trò "Gatekeeper" (Người gác cổng)
        # Chỉ đánh dấu +/- nếu tin tức thực sự ảnh hưởng đến sản xuất/logistics
        prompt = f"""
            You are a strict financial analyst for the coffee commodity market. Analyze this news title from Vietnam.
            
            INPUT TITLE: "{title}"

            INSTRUCTIONS:
            1.  **Relevance Check:** Does this news DIRECTLY affect coffee production, farming, harvest, or supply chain logistics?
                * IGNORE: Residential flooding, humanitarian aid (rescuing people), traffic jams, political visits, or weather that doesn't affect crops. -> Return "neutral".
                * ACCEPT: Crop damage, harvest delays, landslides blocking transport routes, widespread drought/frost affecting farms.
            
            2.  **Determine Sign:**
                * "+": Bullish (Price UP) -> Bad weather damaging crops, supply blocked, scarcity.
                * "-": Bearish (Price DOWN) -> Good weather, bumper crop, supply unlock.
                * "neutral": Irrelevant news (even if about disaster) OR balanced news.

            RETURN ONLY JSON:
            {{
                "title_sign": "+", 
                "sign_explanation": "Brief explanation in English (max 20 words). Why relevant or why ignored."
            }}
        """
        
        retries = 3
        for i in range(retries):
            try:
                # Gọi API
                response = client.models.generate_content(
                    model='gemini-2.0-flash', # Nên dùng flash cho nhanh và rẻ/free
                    contents=prompt
                )
                
                # Parse JSON
                text = response.text.strip()
                # Xử lý trường hợp trả về có markdown ```json
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                analysis = json.loads(text)
                
                # --- QUAN TRỌNG: Delay để tránh lỗi 429 (Rate Limit) ---
                # Free tier giới hạn số request/phút. Ngủ 4s giữa các lần gọi.
                time.sleep(4) 
                
                return analysis.get("title_sign", "neutral"), analysis.get("sign_explanation", "No explanation")

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 60 # Nếu bị lỗi 429, chờ hẳn 60 giây
                    print(f"{Fore.RED}!!! QUOTA EXCEEDED (429). Đang chờ {wait_time}s để hồi phục...{Style.RESET_ALL}")
                    time.sleep(wait_time)
                    continue # Thử lại vòng lặp
                else:
                    print(f"{Fore.RED}Lỗi Gemini khác: {e}")
                    return "neutral", "API Error"
        
        return "neutral", "Failed after retries"

    def parse_rss(self, name, url):
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                link = entry.link
                title = entry.title
                summary = getattr(entry, 'summary', '')
                
                # --- SỬA LOGIC LẤY NGÀY ---
                pub_date = None
                
                # 1. Ưu tiên lấy ngày xuất bản (published)
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.published_parsed)) + timedelta(hours=7)
                # 2. Nếu không có, thử lấy ngày cập nhật (updated)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.updated_parsed)) + timedelta(hours=7)
                elif hasattr(entry, 'created_parsed') and entry.created_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.created_parsed)) + timedelta(hours=7)
                
                # 3. Nếu vẫn không tìm thấy ngày -> BỎ QUA (Không tính toán, không lưu DB)
                if pub_date is None:
                    print(f"{Fore.RED}Bỏ qua bài viết (Không tìm thấy ngày): {title} | {link}") 
                    continue

                # 4. Kiểm tra thời gian lọc (start_time)
                if pub_date < (self.start_time - timedelta(minutes=30)):
                     continue 
                
                # --- HẾT PHẦN SỬA LOGIC NGÀY ---

                if link not in self.seen_links:
                    relevant, tag = self.is_relevant(title, summary)
                    if relevant:
                        self.seen_links.add(link)
                        print(f"{Fore.CYAN}...Đang phân tích: {title[:30]}...")
                        
                        # sign, explanation = self.gemini_analyze(title)
                        
                        sign = "+"
                        explanation = "test" 
                        
                        # === UPDATE DATABASE ===
                        # Mặc định lấy giá trị hiện tại của ngày kế toán để hiển thị
                        acc_date = self.get_accounting_date(pub_date)
                        
                        # Lấy giá trị cũ từ DB để hiển thị (nếu sign là neutral)
                        obj = DailyNewsFromVietNamSign.objects.filter(date=acc_date).first()
                        current_summary = obj.sign_summary if obj else 0
                        
                        if sign in ["+", "-"]:
                            # Nếu có dấu, update DB và lấy giá trị mới nhất
                            current_summary, acc_date = self.update_db_sign(pub_date, sign)
                            # Lưu ý: self.sign_summary ở đây chỉ là biến tạm trên RAM để bạn debug
                            if sign == "+":
                                self.sign_summary += 1
                            elif sign == "-":
                                self.sign_summary -= 1
                        
                        acc_date_str = acc_date.strftime('%d/%m/%Y')
                        self.print_news(name, title, link, tag, pub_date, sign, explanation, current_summary, acc_date_str)
                        count += 1
            return count
        except Exception as e:
            print(f"RSS Error ({name}): {e}")
            return 0

    def print_news(self, source, title, link, tag, pub_time, sign, explanation, current_summary, acc_date_str):
        tag_color = Fore.RED if "THIÊN TAI" in tag else Fore.GREEN
        
        # Màu cho Sign
        if sign == "+": sign_color = Fore.MAGENTA 
        elif sign == "-": sign_color = Fore.BLUE
        else: sign_color = Fore.WHITE # Neutral

        # Màu cho Summary
        if current_summary > 0: sum_color = Fore.MAGENTA # Bullish trend
        elif current_summary < 0: sum_color = Fore.BLUE  # Bearish trend
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
            time.sleep(60) # Chờ 1 phút giữa các lần quét RSS
            for name, url in self.rss_sources.items():
                self.parse_rss(name, url)
    
if __name__ == "__main__":
    scanner = NewsScanner()
    scanner.run()