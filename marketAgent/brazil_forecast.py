import json
import pandas as pd
import os
import datetime
def export_weather_to_excel(json_files, output_filename="weather_report.xlsx"):
    """
    Đọc các file JSON dự báo thời tiết và tạo file Excel với nhiều sheet.
    
    Args:
        json_files (list): Danh sách đường dẫn tới các file .json
        output_filename (str): Tên file Excel đầu ra.
    """
    # Sử dụng ExcelWriter để ghi nhiều sheet vào cùng 1 file
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        for file_path in json_files:
            # 1. Đọc dữ liệu từ file JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 2. Trích xuất các trường thông tin cần thiết
            extracted_data = []
            for entry in data:
                extracted_data.append({
                    "ngày": entry['start'][:10], # Lấy 10 ký tự đầu (YYYY-MM-DD)
                    "temperature_min": entry['temperature']['min'],
                    "temperature_max": entry['temperature']['max'],
                    "precipitation": entry['precipitation']['value'],
                    "twelve_hour_symbols": entry['twelveHourSymbols'],
                    "six_hour_symbols": entry['sixHourSymbols']
                })
            print("extracted_data::", extracted_data)
            # 3. Chuyển đổi sang DataFrame của Pandas
            df = pd.DataFrame(extracted_data)
            
            # 4. Lấy tên vùng từ tên file (ví dụ: 'minas_gerais.json' -> 'minas_gerais')
            sheet_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 5. Ghi DataFrame vào sheet tương ứng
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Đã tạo file thành công: {output_filename}")

# --- Cách sử dụng ---
files = [
    "D:/PER_WORKSPACE/scan_document/media/brazil_forecast/espirito_santo.json",
    "D:/PER_WORKSPACE/scan_document/media/brazil_forecast/minas_gerais.json",
    "D:/PER_WORKSPACE/scan_document/media/brazil_forecast/parana.json",
    "D:/PER_WORKSPACE/scan_document/media/brazil_forecast/rondonia.json",
    "D:/PER_WORKSPACE/scan_document/media/brazil_forecast/sao_paulo.json",
]

export_weather_to_excel(files, f"D:/PER_WORKSPACE/scan_document/media/brazil_forecast/brazil_forecast_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx")