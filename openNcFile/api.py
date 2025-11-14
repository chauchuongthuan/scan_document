# views.py
import os
import re
import pandas as pd
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import RainPrecip
from django.conf import settings
from .download_file import download_chirps_pentad_split5
class RainPrecipView(APIView):
    def post(self, request):
        """
        Nhận input folder_path (chứa các file CSV filtered_...),
        đọc toàn bộ dữ liệu và ghi vào DB (model RainPrecip).
        """

        folder_path = request.data.get("folder_path")
        province = request.data.get("province")
        if not folder_path or not os.path.isdir(folder_path):
            return Response({
                "success": False,
                "message": "Thiếu hoặc sai đường dẫn folder_path."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Lấy danh sách file CSV
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(".csv")]
        if not files:
            return Response({
                "success": False,
                "message": "Không tìm thấy file CSV nào trong thư mục."
            }, status=status.HTTP_404_NOT_FOUND)

        # Hàm phụ: phát hiện cột
        def detect_cols(df):
            cols = [c.lower() for c in df.columns]
            time_col = next((c for c in cols if c in ("date", "time", "datetime")), None)
            lat_col = next((c for c in cols if c in ("lat", "latitude", "y")), None)
            lon_col = next((c for c in cols if c in ("lon", "longitude", "x")), None)
            precip_col = next((c for c in cols if c in ("precip", "precipitation", "value", "precip_mm")), None)
            return time_col, lat_col, lon_col, precip_col

        # Hàm sắp xếp theo ngày trong tên file
        def extract_start_date(fname):
            m = re.search(r"(\d{1,2})_(\d{1,2})_(\d{4})", fname)
            if not m:
                return datetime.max
            d, mth, y = map(int, m.groups())
            return datetime(y, mth, d)

        files.sort(key=extract_start_date)

        total_inserted = 0
        total_skipped = 0
        chunksize = 50000

        for fname in files:
            fpath = os.path.join(folder_path, fname)
            print(f"📂 Đang xử lý file: {fname}")

            try:
                reader = pd.read_csv(fpath, chunksize=chunksize, low_memory=False)
            except Exception as e:
                print(f"⚠️ Lỗi đọc {fname}: {e}")
                continue

            time_col = lat_col = lon_col = precip_col = None
            first = True

            for chunk in reader:
                if first:
                    time_col, lat_col, lon_col, precip_col = detect_cols(chunk)
                    if not all([time_col, lat_col, lon_col, precip_col]):
                        print(f"⚠️ File {fname} không đủ cột cần thiết.")
                        break
                    first = False

                # Chuẩn hoá dữ liệu
                chunk[time_col] = pd.to_datetime(chunk[time_col], errors="coerce").dt.date
                chunk[lat_col] = pd.to_numeric(chunk[lat_col], errors="coerce")
                chunk[lon_col] = pd.to_numeric(chunk[lon_col], errors="coerce")
                chunk[precip_col] = pd.to_numeric(chunk[precip_col], errors="coerce")

                chunk = chunk.dropna(subset=[time_col, lat_col, lon_col])

                # Ghi từng batch vào DB
                new_objs = []
                for _, row in chunk.iterrows():
                    new_objs.append(RainPrecip(
                        date=row[time_col],
                        latitude=row[lat_col],
                        longitude=row[lon_col],
                        precip=row[precip_col],
                        province=province,
                    ))

                # Ghi batch vào DB, tránh trùng (unique_together)
                try:
                    with transaction.atomic():
                        RainPrecip.objects.bulk_create(
                            new_objs, ignore_conflicts=True, batch_size=5000
                        )
                        total_inserted += len(new_objs)
                except Exception as e:
                    print(f"⚠️ Lỗi ghi batch {fname}: {e}")

            print(f"✅ Hoàn tất file: {fname}")

        return Response({
            "success": True,
            "message": "Đã gộp dữ liệu mưa thành công.",
            "stats": {
                "folder": folder_path,
                "total_files": len(files),
                "total_inserted": total_inserted,
            }
        }, status=status.HTTP_200_OK)

class ExportRainPrecipView(APIView):
    """
    API xuất dữ liệu mưa ra CSV (có thể lọc theo khoảng ngày).
    """

    def get(self, request):
        try:
            # Lấy tham số lọc (nếu có)
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")
            province = request.GET.get("province")

            # Query cơ bản
            qs = RainPrecip.objects.all().order_by("date", "latitude", "longitude").filter(province=province)

            if start_date and end_date:
                qs = qs.filter(date__range=[start_date, end_date])
            elif start_date:
                qs = qs.filter(date__gte=start_date)
            elif end_date:
                qs = qs.filter(date__lte=end_date)

            total = qs.count()
            if total == 0:
                return Response({
                    "success": False,
                    "message": "Không có dữ liệu để xuất."
                }, status=status.HTTP_404_NOT_FOUND)

            # Đảm bảo thư mục export tồn tại
            export_dir = os.path.join(settings.BASE_DIR, "media", "exports")
            os.makedirs(export_dir, exist_ok=True)

            # Tạo tên file
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"rain_precip_{province}_{now_str}.csv"
            file_path = os.path.join(export_dir, file_name)

            # Xuất từng batch để tránh ngốn RAM
            chunk_size = 100000
            with open(file_path, "w", encoding="utf-8") as fout:
                fout.write("date,latitude,longitude,precip,province\n")

            offset = 0
            while offset < total:
                batch = qs[offset:offset + chunk_size]
                df = pd.DataFrame(list(batch.values("date", "latitude", "longitude", "precip", "province")))
                df.to_csv(file_path, mode="a", index=False, header=False, encoding="utf-8")
                offset += chunk_size
                print(f"✅ Xuất {offset}/{total} hàng...")

            # Tạo URL trả về (giả định dùng MEDIA_URL)
            file_url = f"exports/{file_name}"

            return Response({
                "success": True,
                "message": f"Xuất thành công {total} bản ghi.",
                "file_name": file_name,
                "download_url": file_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Lỗi khi xuất dữ liệu: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DownLoadFileFromCoastwWatch(APIView):
    def post(self, request):
        try:
            save_dir = request.data.get("save_dir")
            lat_min = request.data.get("lat_min")
            lat_max = request.data.get("lat_max")
            lon_min = request.data.get("lon_min")
            lon_max = request.data.get("lon_max")
            start_year = request.data.get("start_year")
            end_year = request.data.get("end_year")

            final_message = download_chirps_pentad_split5(save_dir, lat_min, lat_max, lon_min, lon_max, start_year, end_year)

            if not lat_min or not lat_max or not lon_min or not lon_max or not start_year or not end_year or not save_dir:
                return Response({
                    "success": False,
                    "message": "Thiếu tham số."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response({
                "success": True,
                "message": final_message,
            }, status=status.HTTP_200_OK)
            
            
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Lỗi khi tải file từ CoastWatch: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)