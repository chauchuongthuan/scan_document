import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime

# Cấu hình API Client
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def process_weather_forecast(input_file, output_file):
    try:
        # 1. Đọc dữ liệu từ file Excel
        df = pd.read_excel(input_file)
        
        # 2. LÀM SẠCH DỮ LIỆU: Loại bỏ các dòng có lat hoặc long là rỗng (NaN)
        # Bước này cực kỳ quan trọng để tránh lỗi API
        original_count = len(df)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        cleaned_count = len(df)
        
        if original_count > cleaned_count:
            print(f"⚠️ Đã loại bỏ {original_count - cleaned_count} dòng do thiếu tọa độ (NaN).")

        if df.empty:
            print("❌ Không có dữ liệu tọa độ hợp lệ để xử lý.")
            return

    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")
        return

    results = []
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Chuyển thành list sau khi đã xóa bỏ NaN
    lats = df['Latitude'].tolist()
    longs = df['Longitude'].tolist()

    params = {
        "latitude": lats,
        "longitude": longs,
        "hourly": ["temperature_2m", "rain", "precipitation", "precipitation_probability"],
		"daily": ["temperature_2m_min", "temperature_2m_max", "rain_sum", "precipitation_probability_max", "showers_sum", "snowfall_sum", "precipitation_sum", "et0_fao_evapotranspiration"],
        "timezone": "auto",
        "forecast_days": 1,
    }

    print(f"🚀 Đang lấy dữ liệu thời tiết cho {len(df)} vị trí hợp lệ...")
    
    try:
        responses = openmeteo.weather_api(url, params=params)
    except Exception as e:
        print(f"❌ Lỗi khi gọi API: {e}")
        return

    # 4. Lặp qua từng phản hồi và tính toán trung bình
    for i, response in enumerate(responses):
        hourly = response.Hourly()
        daily = response.Daily()
        utc_offset = response.UtcOffsetSeconds()

        # Tính giá trị trung bình
        avg_temp = hourly.Variables(0).ValuesAsNumpy().mean()
        avg_rain = hourly.Variables(1).ValuesAsNumpy().mean()
        avg_precip = hourly.Variables(2).ValuesAsNumpy().mean()
        avg_prob = hourly.Variables(3).ValuesAsNumpy().mean()

        forecast_date = pd.to_datetime(hourly.Time() + utc_offset, unit="s").strftime('%Y-%m-%d')

        # Map lại thông tin từ DataFrame đã làm sạch
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
    # Print các khu vực có Frost & Drought Index có vấn đề gồm Country, Region, Frost & Drought Index của từng khu vực
    # >= 150 có vấn đề
    # >= 160 tệ
    # >= 180 đỏ
    # <= 20 có vấn đề
    # <= 10 tệ
    # <= 0 đỏ
    for result in results:
        idx = result["Frost & Drought Index"]
        base_msg = f"Country: {result['Country']}, Region: {result['Region']}: {idx}"

        # Kiểm tra các mức độ nghiêm trọng từ cao xuống thấp
        if idx <= 0 or idx >= 180:
            print(f"{base_msg}: Đỏ")
        elif idx <= 10 or idx >= 160:
            print(f"{base_msg}: Tệ")
        elif idx <= 20 or idx >= 150:
            print(f"{base_msg}: Vấn đề")
    # 5. Xuất file
    output_df = pd.DataFrame(results)
    cols = [
                'Country', 'Type', 'Region', 'Latitude', 'Longitude', 'Date', 
                'Temperature_2m Min (°C)', 'Temperature_2m Max (°C)', 
                # 'Temperature_2m Avg Hourly (°C)', 
                'Rain Sum (mm)',
                'Showers Sum (mm)',
                'Snowfall Sum (mm)',
                # 'Rain Avg Hourly (mm)',
                'Precipitation Sum (mm)',
                # 'Precipitation Avg Hourly (mm)', 
                'Precipitation Probability Max (%)', 
                # 'Precipitation Probability Avg Hourly (%)',
                'Reference Evapotranspiration (ET₀)',
                'Frost & Drought Index'
            ]
    output_df = output_df[[c for c in cols if c in output_df.columns]]
    
    output_df.to_excel(output_file, index=False)
    print(f"✅ Xong! Dữ liệu đã lưu tại: {output_file}")

if __name__ == "__main__":
    INPUT_FILENAME = "C:/Users/COMPUTER/Desktop/Coffee Regions.xlsx" # Đảm bảo tên file chính xác
    OUTPUT_FILENAME = f"D:/PER_WORKSPACE/scan_document/media/coffee_regions_weather/coffee_regions_weather_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
    process_weather_forecast(INPUT_FILENAME, OUTPUT_FILENAME)