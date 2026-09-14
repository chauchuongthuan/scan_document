import os
import pandas as pd
from datetime import datetime
from django.utils import timezone
from weatherForecast.models import CoffeeRegionWeatherForecast, WeatherProblemHistory, WeatherForecastHistory


def evaluate_severity(idx: float) -> str | None:
    """Đánh giá chỉ số Frost & Drought Index theo thứ tự ưu tiên."""
    if idx <= 0 or idx >= 180:
        return "Đỏ"
    elif idx <= 10 or idx >= 160:
        return "Tệ"
    elif idx <= 20 or idx >= 150:
        return "Vấn đề"
    return None


def sync_regions_from_dataframe(df: pd.DataFrame):
    """Cập nhật hoặc thêm mới các khu vực vào database từ DataFrame."""
    for _, row in df.iterrows():
        CoffeeRegionWeatherForecast.objects.update_or_create(
            country=str(row['Country']).strip(),
            region=str(row['Region']).strip(),
            defaults={
                'is_active': True
            }
        )

def save_weather_problems_to_db(results: list[dict]) -> int:
    """Lọc các khu vực gặp vấn đề và lưu/cập nhật vào Postgres DB."""
    saved_count = 0
    
    for result in results:
        idx = result.get("Frost & Drought Index")
        if idx is None:
            continue

        severity = evaluate_severity(idx)
        if not severity:
            continue

        country = str(result["Country"]).strip()
        region_name = str(result["Region"]).strip()

        # Tìm hoặc tạo Region record
        region_obj, _ = CoffeeRegionWeatherForecast.objects.get_or_create(
            country=country,
            region=region_name,
            defaults={
                'is_active': True
            }
        )

        # Lưu hoặc cập nhật bản ghi lịch sử sự cố theo ngày
        WeatherProblemHistory.objects.update_or_create(
            coffee_region=region_obj,
            date=result["Date"],
            defaults={
                'country': country,
                'region': region_name,
                'frost_drought_index': idx,
                'note': severity
            }
        )
        saved_count += 1

    return saved_count


def export_history_weather_forecast_service(output_directory: str, file_name_str: str, filters: dict = None) -> str:
    """
    Xuất lịch sử các khu vực gặp vấn đề thời tiết ra file Excel theo đúng định dạng mẫu.
    Sắp xếp theo Country -> Region -> Date và chỉ hiển thị tên Country, Region ở dòng đầu của nhóm.
    """
    try:
        os.makedirs(output_directory, exist_ok=True)
        
        # 1. Khởi tạo QuerySet
        if file_name_str.startswith("history_weather_forecast_problem"):
            queryset = WeatherProblemHistory.objects.select_related('coffee_region').all()
        else:
            queryset = WeatherForecastHistory.objects.select_related('coffee_region').all()
        
        # 2. Áp dụng bộ lọc (loại bỏ các giá trị None/chuỗi rỗng)
        if filters:
            region = filters.get('region', '').strip() if filters.get('region') else ''
            start_date = filters.get('start_date', '').strip() if filters.get('start_date') else ''
            end_date = filters.get('end_date', '').strip() if filters.get('end_date') else ''

            if region:
                queryset = queryset.filter(region__icontains=region)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
        
        # Kiểm tra nếu không có dữ liệu
        if not queryset.exists():
            print(f"⚠️ [EXPORT LOG] Không tìm thấy dữ liệu phù hợp với bộ lọc: {filters}")
            return ""

        # 3. Chuyển QuerySet sang DataFrame
        data_list = list(queryset.values('country', 'region', 'date', 'frost_drought_index', 'note'))
        df = pd.DataFrame(data_list)
        
        # 4. Sắp xếp thứ tự ưu tiên: Country -> Region -> Date
        df.sort_values(by=['country', 'region', 'date'], ascending=[True, True, True], inplace=True)

        # 5. Đổi tên cột khớp với file mẫu
        df.rename(columns={
            'country': 'Country',
            'region': 'Region',
            'date': 'Date',
            'frost_drought_index': 'Frost & Drought Index',
            'note': 'Note'
        }, inplace=True)

        # 6. Gom nhóm visual: Xóa tên Country và Region lặp lại ở các dòng phía sau
        duplicate_mask = df.duplicated(subset=['Country', 'Region'])
        df.loc[duplicate_mask, ['Country', 'Region']] = ''

        # 7. Sắp xếp đúng thứ tự cột
        df = df[['Country', 'Region', 'Date', 'Frost & Drought Index', 'Note']]

        # 8. Tạo tên file và xuất Excel
        file_name = file_name_str
        full_path = os.path.join(output_directory, file_name)

        df.to_excel(full_path, index=False)
        print(f"✅ [EXPORT LOG] Đã tạo thành công file Excel: {full_path}")
        return full_path

    except Exception as e:
        print(f"❌ [EXPORT ERROR] Lỗi trong quá trình export Excel: {str(e)}")
        return ""