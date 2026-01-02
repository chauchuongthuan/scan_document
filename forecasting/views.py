import os
import joblib
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# --- Helper Function: Xử lý thời tiết ---
def parse_weather_text_to_score(text_input):
    if not text_input:
        return 5 # Mặc định nếu không có text
    
    text_input = text_input.lower()
    regions = {'dak lak': 0.5, 'lam dong': 0.3, 'gia lai': 0.2}
    keywords = {
        'clear': 0, 'sunny': 0,
        'overcast': 3, 'cloudy': 3,
        'light rain': 5, 'moderate rain': 6,
        'heavy rain': 9, 'storm': 10
    }
    
    total_score = 0
    # Logic đơn giản hóa để demo, bạn có thể thay thế bằng logic regex phức tạp hơn
    for region, weight in regions.items():
        region_score = 0 # Mặc định trời đẹp nếu không nhắc tới
        if region in text_input:
            # Tìm từ khóa thời tiết xuất hiện cùng tên vùng (hoặc trong text)
            # Ở đây lấy max score tìm thấy trong toàn văn bản cho đơn giản
            found_scores = [score for word, score in keywords.items() if word in text_input]
            if found_scores:
                region_score = max(found_scores)
        total_score += region_score * weight
        
    return round(total_score, 2)

# --- Main View ---
class CoffeeForecastView(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                def get_float_or_nan(key):
                    val = request.POST.get(key)
                    if val and val.strip():
                        return float(val)
                    return np.nan
                    
                prev_open = get_float_or_nan('prev_open')
                prev_high = get_float_or_nan('prev_high')
                prev_low  = get_float_or_nan('prev_low')
                prev_close = get_float_or_nan('prev_close')
                inventory = get_float_or_nan('inventory')
                entropy = get_float_or_nan('entropy')
                weather_text = request.POST.get('weather', '')
                weather_score = parse_weather_text_to_score(weather_text)

                # 2. Tạo DataFrame (Đúng thứ tự cột như lúc train)
                features = ['Prev_Open', 'Prev_High', 'Prev_Low', 'Prev_Close', 
                            'Inventory_Level', 'Weather_Score', 'Entropy_Score']
                
                input_data = pd.DataFrame([[
                    prev_open, prev_high, prev_low, prev_close, 
                    inventory, weather_score, entropy
                ]], columns=features)

                # 3. Load Model và Imputer
                model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'coffee_price_model.pkl')
                imputer_path = os.path.join(settings.BASE_DIR, 'ml_models', 'coffee_imputer.pkl')

                if not os.path.exists(model_path) or not os.path.exists(imputer_path):
                     return JsonResponse({"status": "error", "message": "Chưa train model hoặc thiếu file imputer!"}, status=500)

                model = joblib.load(model_path)
                imputer = joblib.load(imputer_path)

                # 4. Xử lý dữ liệu thiếu bằng Imputer đã train
                input_data_processed = imputer.transform(input_data)

                # 5. Dự báo
                prediction = model.predict(input_data_processed)[0]

                return JsonResponse({
                    "status": "success",
                    "message": "Dự báo thành công!",
                    "data": {
                        "price": f"{prediction:,.2f}",
                        "weather_score": weather_score
                    }
                }, status=200)

            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Lỗi xử lý: {str(e)}"
                }, status=500)
        
        return render(request, 'forecasting/predict_price.html')