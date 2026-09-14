import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime
from .weather_forecast_service import (
    evaluate_severity, 
    save_weather_problems_to_db, 
    sync_regions_from_dataframe
)

# Cấu hình API Client
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def process_weather_forecast(input_file, daily_output_file):
    try:
        # 1. Đọc và làm sạch dữ liệu từ Excel
        df = pd.read_excel(input_file)
        original_count = len(df)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        cleaned_count = len(df)
        
        if original_count > cleaned_count:
            print(f"⚠️ Đã loại bỏ {original_count - cleaned_count} dòng do thiếu tọa độ (NaN).")

        if df.empty:
            print("❌ Không có dữ liệu tọa độ hợp lệ để xử lý.")
            return

        # 2. Đồng bộ danh sách vị trí vào PostgreSQL
        sync_regions_from_dataframe(df)

    except Exception as e:
        print(f"❌ Lỗi khi đọc file Excel: {e}")
        return

    results = []
    url = "https://api.open-meteo.com/v1/forecast"
    
    lats = df['Latitude'].tolist()
    longs = df['Longitude'].tolist()

    params = {
        "latitude": lats,
        "longitude": longs,
        "hourly": ["temperature_2m", "rain", "precipitation", "precipitation_probability"],
        "daily": [
            "temperature_2m_min", "temperature_2m_max", "rain_sum", 
            "precipitation_probability_max", "showers_sum", "snowfall_sum", 
            "precipitation_sum", "et0_fao_evapotranspiration"
        ],
        "timezone": "auto",
        "forecast_days": 1,
    }

    print(f"🚀 Đang lấy dữ liệu thời tiết cho {len(df)} vị trí hợp lệ...")
    
    try:
        responses = openmeteo.weather_api(url, params=params)
    except Exception as e:
        print(f"❌ Lỗi khi gọi API: {e}")
        return

    # 3. Xử lý phản hồi thời tiết
    for i, response in enumerate(responses):
        hourly = response.Hourly()
        daily = response.Daily()
        utc_offset = response.UtcOffsetSeconds()

        forecast_date = pd.to_datetime(hourly.Time() + utc_offset, unit="s").strftime('%Y-%m-%d')
        
        row_info = df.iloc[i].to_dict()
        row_info.update({
            "Date": forecast_date,
			"Temperature_2m Min (°C)": round(float(daily.Variables(0).ValuesAsNumpy().min()), 2),
			"Temperature_2m Max (°C)": round(float(daily.Variables(1).ValuesAsNumpy().max()), 2),
            # "Temperature_2m Avg Hourly (°C)": round(float(avg_temp), 2),
			"Rain Sum (mm)": round(float(daily.Variables(2).ValuesAsNumpy().sum()), 2),
            # "Rain Avg Hourly (mm)": round(float(avg_rain), 2),
            "Showers Sum (mm)": round(float(daily.Variables(4).ValuesAsNumpy().sum()), 2),
            "Snowfall Sum (mm)": round(float(daily.Variables(5).ValuesAsNumpy().sum()), 2),
            # "Precipitation Avg Hourly (mm)": round(float(avg_precip), 2),
            "Precipitation Sum (mm)": round(float(daily.Variables(6).ValuesAsNumpy().sum()), 2),
            "Precipitation Probability Max (%)": round(float(daily.Variables(3).ValuesAsNumpy().max()), 2),
            "Reference Evapotranspiration (ET₀)": round(float(daily.Variables(7).ValuesAsNumpy().sum()), 2),
            # "Precipitation Probability Avg Hourly (%)": round(float(avg_prob), 2)
            "Frost & Drought Index": round(float(daily.Variables(7).ValuesAsNumpy().sum()), 2) * round(float(daily.Variables(0).ValuesAsNumpy().min()), 2),
        })
        results.append(row_info)

    # 4. In thông báo console đối với các khu vực gặp vấn đề
    print("\n🔍 KHU VỰC CÓ CẢNH BÁO THỜI TIẾT:")
    for result in results:
        idx = result["Frost & Drought Index"]
        severity = evaluate_severity(idx)
        if severity:
            print(f"Country: {result['Country']}, Region: {result['Region']}: {idx} -> {severity}")

    # 5. Lưu các vị trí gặp vấn đề vào PostgreSQL Database
    saved_db_count = save_weather_problems_to_db(results)
    print(f"💾 Đã lưu/cập nhật {saved_db_count} bản ghi sự cố vào PostgreSQL Database.")

    # 6. Xuất file Excel hàng ngày đầy đủ thông tin
    output_df = pd.DataFrame(results)
    cols = [
        'Country', 'Type', 'Region', 'Latitude', 'Longitude', 'Date', 
        'Temperature_2m Min (°C)', 'Temperature_2m Max (°C)', 
        'Rain Sum (mm)', 'Showers Sum (mm)', 'Snowfall Sum (mm)',
        'Precipitation Sum (mm)', 'Precipitation Probability Max (%)', 
        'Reference Evapotranspiration (ET₀)', 'Frost & Drought Index'
    ]
    output_df = output_df[[c for c in cols if c in output_df.columns]]
    output_df.to_excel(daily_output_file, index=False)
    print(f"✅ Xong dữ liệu hàng ngày! Lưu tại: {daily_output_file}")
