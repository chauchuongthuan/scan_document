import os
import django
from datetime import datetime
import pytz
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coffee.settings")
django.setup()

tz = pytz.timezone("Asia/Ho_Chi_Minh")

REVENUE_API_URL = "http://localhost:8000/revenue/api/fetch-and-sync-revenue"
SUMMARY_API_URL = "http://localhost:8000/revenue/api/get-sum-total-of-7-days-every-hour"

# Thay Token mỗi tuần
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVlMDJjYjE4LTk1YTYtNGIzMi04OWM2LWI1NTc3ODVlNTZmOSIsInV0IjoiZmZlOGFkYzMtMzdjOC00YjBiLTgzMWUtMGUzMWRjNDBhMTFlIiwiZW1haWwiOiJpbmZvQGhvdGJlYW5zLmNvZmZlZSIsImlhdCI6MTc3MDQ0NzA1NSwiZXhwIjoxNzcxMDUxODU1fQ.inpoXBiXgGHWEMnEycWL33IoQVf-76fuEPJxZvnJ2V0"

def run_hourly_jobs():
    """
    Chạy đúng mỗi giờ: 08:00, 09:00, 10:00, ...
    """
    now = datetime.now(tz)

    # 👉 Làm tròn về đầu giờ (cron đã đảm bảo phút = 00)
    current_time_str = now.strftime("%Y-%m-%d %H:00")
    today_str = now.strftime("%Y-%m-%d")

    print("[CRON] Running at:", current_time_str)

    # 1️⃣ GỌI RevenueAPIView (chỉ ngày hôm đó)
    revenue_payload = {
        "token": TOKEN,
        "start_date": today_str,
        "end_date": today_str
    }

    try:
        r1 = requests.post(REVENUE_API_URL, json=revenue_payload, timeout=60)
        print("[CRON] RevenueAPIView:", r1.status_code)
    except Exception as e:
        print("[CRON] RevenueAPIView ERROR:", e)

    # 2️⃣ GỌI GetSumTotalOf7DaysEveryHourAPIView
    summary_payload = {
        "current_time": current_time_str,
        "hours": 3   # hoặc 133 cho 7 ngày
    }

    try:
        r2 = requests.post(SUMMARY_API_URL, json=summary_payload, timeout=60)
        print("[CRON] GetSumTotal:", r2.status_code, r2.text)
    except Exception as e:
        print("[CRON] GetSumTotal ERROR:", e)

if __name__ == "__main__":
    run_hourly_jobs()