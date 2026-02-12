from django.core.management.base import BaseCommand
from django.utils import timezone # Import thư viện timezone của Django
import pytz # Thư viện xử lý múi giờ
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
import os
import sys
import django
import time
from dotenv import load_dotenv
load_dotenv()
try:
    project_path = 'D:/PER_WORKSPACE/scan_document'
    sys.path.append(project_path) 
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee.settings')
    django.setup()
except Exception as e:
    # Bắt exception cụ thể để in ra lỗi chính xác hơn nếu Django thất bại
    print(f"LỖI CẤU HÌNH DJANGO: {e}. Vui lòng kiểm tra lại tên project/app và settings.")
    print(f"Script sẽ không thể tương tác với Database.")

from chartOHLC.models import OHLCDataKC, OHLCDataRC
from django.db.models import F

class GetDataEvery15Minutes(BaseCommand):
    def getDataKC(self):
        df = tv.get_hist(
            symbol="KCH2026",
            exchange="ICEUS",
            interval=Interval.in_1_minute,
            n_bars=30
        )
        if df is not None:
            df = df.reset_index()
            for _, row in df.iterrows():
                naive_dt = row['datetime']
                timezone_dt = timezone.make_aware(naive_dt, pytz.timezone('Asia/Ho_Chi_Minh'))
                OHLCDataKC.objects.update_or_create(
                        symbol="KCH2026",
                        timestamp=timezone_dt,
                        defaults={
                            'open': row['open'], 'high': row['high'],
                            'low': row['low'], 'close': row['close'],
                            'volume': row['volume']
                        }
                    )
    
    def getDataRC(self):
        df = tv.get_hist(
            symbol="RCH2026",
            exchange="ICEEUR",
            interval=Interval.in_1_minute,
            n_bars=30
        )
        if df is not None:
            df = df.reset_index()
            for _, row in df.iterrows():
                naive_dt = row['datetime']
                timezone_dt = timezone.make_aware(naive_dt, pytz.timezone('Asia/Ho_Chi_Minh'))
                OHLCDataRC.objects.update_or_create(
                        symbol="RCH2026",
                        timestamp=timezone_dt,
                        defaults={
                            'open': row['open'], 'high': row['high'],
                            'low': row['low'], 'close': row['close'],
                            'volume': row['volume']
                        }
                    )
    
if __name__ == "__main__":
    # Khởi tạo đối tượng một lần duy nhất bên ngoài vòng lặp để tối ưu hiệu suất
    worker = GetDataEvery15Minutes()
    
    while True:
        try:
            # flush=True giúp in log ra màn hình ngay lập tức, không đợi buffer
            print(f"START RUNNING...", flush=True)
            
            print("Fetching KC data...", flush=True)
            worker.getDataKC()
            
            print("Fetching RC data...", flush=True)
            worker.getDataRC()
            
            print(f"RUNNING END - Sleeping 15 minutes", flush=True)
            time.sleep(900)
            
        except Exception as e:
            # Bắt mọi lỗi phát sinh để script không bị dừng đột ngột
            print(f"LỖI PHÁT SINH TRONG VÒNG LẶP: {e}", flush=True)
            # Nếu lỗi do mạng, đợi 10s rồi thử lại vòng lặp mới
            time.sleep(10)