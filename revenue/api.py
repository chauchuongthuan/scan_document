import requests
import pandas as pd
from datetime import datetime, time, timedelta
from django.db import transaction
from django.db.models import Q
from .models import Revenue, RevenueByHour
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pytz
from django.utils import timezone
import os
# Thiết lập múi giờ Việt Nam
tz = pytz.timezone('Asia/Ho_Chi_Minh')
REQUIRED_HOURS = [0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
class RevenueAPIView(APIView):
    def post(self, request):
        start_date_str = request.data.get('start_date') 
        end_date_str = request.data.get('end_date')
        token_str = request.data.get('token')
        fetch_and_sync_revenue(start_date_str, end_date_str, token_str)
        
        return Response({
            "success": True,
            "message": "Đã nhập dữ liệu doanh thu thành công.",
        }, status=status.HTTP_200_OK)

        

class GetSumTotalOf7DaysEveryHourAPIView(APIView):
    def post(self, request):
        current_time_str = request.data.get('current_time')
        hours = request.data.get('hours', 133)
        if not current_time_str:
            return Response({"error": "Thiếu current_time"}, status=400)
            
        try:
            total = calculate_total_revenue_last_n_hours(current_time_str, hours)
            return Response({
                "input_time": current_time_str,
                "hours_count": hours,
                "total_revenue": total
            }, status=200)
        except Exception as e:
            print("Error:", e)
            return Response({"error": str(e)}, status=500)

def fetch_and_sync_revenue(start_date_str, end_date_str, token_str = None):
    try:
        token = token_str or os.getenv("POS_API_TOKEN")
        # 2. Xử lý Start Date (00:00:00)
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        # Kết hợp ngày với 00:00:00 và gán múi giờ
        start_dt_local = tz.localize(datetime.combine(start_dt.date(), time.min))
        # Chuyển sang timestamp mili giây (nhân 1000)
        start_timestamp = str(int(start_dt_local.timestamp() * 1000))

        # 3. Xử lý End Date (23:59:59)
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        # Kết hợp ngày với 23:59:59 và gán múi giờ
        end_dt_local = tz.localize(datetime.combine(end_dt.date(), time.max))
        # Chuyển sang timestamp mili giây
        end_timestamp = str(int(end_dt_local.timestamp() * 1000))

    except ValueError:
        return Response({"error": "Định dạng ngày không đúng, vui lòng dùng YYYY-MM-DD"}, status=400)

    url = "https://posapi.ipos.vn/api/v1/accounting/report/sale-detail"
    print("start_timestamp", start_timestamp)
    print("end_timestamp", end_timestamp)
    params = {
        "company_uid": "5b03c7c5-3bfa-4a8a-8bb1-6210378753c3",
        "brand_uid": "ebe1cd4f-a394-428f-a986-f0975fa7015f",
        "list_store_uid": "c841f2eb-747e-47eb-a214-40f126545e98",
        "start_date": start_timestamp,
        "end_date": end_timestamp,
        "skip_limit": "1",
        "results_per_page": "200000"
    }
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": token,
        "access_token": "5c885b2ef8c34fb7b1d1fad11eef7bec",
        "fabi_type": "pos-cms",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    }

    try:
        # 1. Gọi API lấy dữ liệu
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        res_data = response.json()
        # 2. Đưa vào Pandas DataFrame (Lấy từ key 'data')
        df = pd.DataFrame(res_data['data'])
        
        if df.empty:
            return Response({
                "success": False,
                "message": "Không có dữ liệu"
            }, status=status.HTTP_404_NOT_FOUND)
        print("df::", df)
        # 3. Xử lý dữ liệu
        # Chuyển tran_date (timestamp ms) thành định dạng ngày
        df['date_dt'] = pd.to_datetime(df['tran_date'], unit='ms').dt.date
        
        # 4. Groupby (Pivot Table)
        # Group theo Ngày và Giờ, tính tổng total_amount_without_vat
        pivot_df = df.groupby(['date_dt', 'end_hour'])['total_amount_without_vat'].sum().reset_index()
        print("pivot_df::", pivot_df)
        # 5. Lưu vào PostgreSQL
        unique_dates = pivot_df['date_dt'].unique()
        with transaction.atomic():
            for d in unique_dates:
                # Lọc dữ liệu của riêng ngày d
                day_data = pivot_df[pivot_df['date_dt'] == d]
                
                # Tạo dictionary để tra cứu nhanh {giờ: tổng tiền}
                hour_lookup = dict(zip(day_data['end_hour'], day_data['total_amount_without_vat']))
                
                # Xây dựng cấu trúc JSON đầy đủ 19 mốc và đúng thứ tự
                full_revenue_list = []
                for h in REQUIRED_HOURS:
                    full_revenue_list.append({
                        "time": h,
                        "total": float(hour_lookup.get(h, 0)) # Nếu không có giờ đó thì lấy 0
                    })
                
                timezone_dt = timezone.make_aware(
                    datetime.combine(d, time.min)
                )
                # Lưu/Cập nhật bản ghi duy nhất cho ngày d với toàn bộ list 19 mốc
                Revenue.objects.update_or_create(
                    timestamp=timezone_dt,
                    defaults={
                        "revenue_data": full_revenue_list
                    }
                )
        
        return Response({
            "success": True,
            "message": "Đã nhập dữ liệu doanh thu thành công.",
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "message": f"Lỗi: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def calculate_total_revenue_last_n_hours(current_dt_str, hours):
    """
    current_dt_str: "YYYY-MM-DD HH:MM"
    hours: số slot giờ hợp lệ cần truy ngược
    """
    target_dt = tz.localize(datetime.strptime(current_dt_str, "%Y-%m-%d %H:%M"))

    required_slots = []
    cursor_dt = target_dt

    # 1️⃣ Thu thập đủ `hours` slot hợp lệ
    while len(required_slots) < hours:
        hour = cursor_dt.hour

        if hour in REQUIRED_HOURS:
            required_slots.append(
                (cursor_dt.strftime("%Y-%m-%d"), hour)
            )

        cursor_dt -= timedelta(hours=1)

    # 2️⃣ Xác định khoảng datetime để query DB
    start_dt = cursor_dt
    start_date_dt = timezone.make_aware(
        datetime.combine(start_dt.date(), time.min)
    )
    end_date_dt = timezone.make_aware(
        datetime.combine(target_dt.date(), time.max)
    )

    # 3️⃣ Query DB
    revenues = Revenue.objects.filter(
        timestamp__range=[start_date_dt, end_date_dt]
    )

    # 4️⃣ Build revenue_map (theo ngày LOCAL)
    revenue_map = {
        r.timestamp.strftime("%Y-%m-%d"): r.revenue_data
        for r in revenues
    }

    print("revenue_map keys:", revenue_map.keys())

    # 5️⃣ Cộng tổng
    total_sum = 0.0

    for day_str, hour in required_slots:
        print(f"[CHECK SLOT] day={day_str}, hour={hour}")

        day_data = revenue_map.get(day_str)
        if not day_data:
            print("  -> No data for this day")
            continue

        hour_record = next(
            (item for item in day_data if item["time"] == hour),
            None
        )

        if hour_record:
            print(
                f"  -> MATCHED | day={day_str} | hour={hour} | record={hour_record}"
            )
            total_sum += float(hour_record.get("total", 0))
        else:
            print(
                f"  -> NO HOUR RECORD (not in REQUIRED_HOURS)"
            )
    
    # 6️⃣ Lưu vào RevenueByHour
    RevenueByHour.objects.update_or_create(
        date=target_dt.date(),
        hour=int(target_dt.time().hour),
        defaults={
            "total": total_sum
        }
    )
    return total_sum
