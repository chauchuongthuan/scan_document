import re
import joblib
import pandas as pd
import numpy as np

# Đường dẫn đến file mô hình đã huấn luyện (sẽ tạo ở bước sau)
MODEL_PATH = 'ml_models/coffee_price_model.pkl'

def parse_weather_text_to_score(text_input):
    """
    Chuyển đổi văn bản thời tiết thành điểm số (Rain Index).
    Input: Đoạn văn bản thời tiết.
    Output: Điểm số trung bình (float).
    """
    text_input = text_input.lower()
    
    # Định nghĩa trọng số khu vực (Đắk Lắk quan trọng nhất)
    regions = {
        'dak lak': 0.5,
        'lam dong': 0.3,
        'gia lai': 0.2
    }
    
    # Từ khóa để chấm điểm mưa
    keywords = {
        'clear': 0, 'sunny': 0,
        'overcast': 3, 'cloudy': 3,
        'light rain': 5, 'moderate rain': 6,
        'heavy rain': 9, 'storm': 10
    }
    
    total_score = 0
    
    # Logic đơn giản: Tìm từ khóa trong đoạn văn và nhân với trọng số vùng
    # (Đây là xử lý chuỗi cơ bản, thực tế có thể cần Regex phức tạp hơn)
    for region, weight in regions.items():
        region_score = 5 # Mặc định là trung bình nếu không thấy tên vùng
        
        # Tách dòng có chứa tên vùng để phân tích
        for line in text_input.split('\n'):
            if region in line:
                # Tìm từ khóa thời tiết trong dòng đó
                found_scores = [score for word, score in keywords.items() if word in line]
                if found_scores:
                    region_score = max(found_scores) # Lấy tình trạng tệ nhất (mưa to nhất)
                else:
                    region_score = 0 # Không thấy từ khóa mưa -> coi là tạnh ráo
                break
        
        total_score += region_score * weight
        
    return round(total_score, 2)

def predict_coffee_price(prev_price, inventory, weather_text):
    """
    Hàm chính để dự đoán.
    """
    # 1. Xử lý thời tiết
    weather_score = parse_weather_text_to_score(weather_text)
    
    # 2. Chuẩn bị dữ liệu đầu vào cho mô hình
    # Thứ tự phải khớp với lúc huấn luyện mô hình (Excel)
    input_data = pd.DataFrame({
        'Prev_Close': [prev_price],
        'Inventory_Level': [inventory],
        'Weather_Score': [weather_score]
    })
    
    # 3. Load mô hình và dự báo
    try:
        model = joblib.load(MODEL_PATH)
        prediction = model.predict(input_data)[0]
        return prediction, weather_score
    except FileNotFoundError:
        return None, weather_score