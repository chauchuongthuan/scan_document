from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from datetime import datetime
import json

from .models import QuantumEngine
from .quantum_engine import QuantumPredictor
# Import hàm utils nếu bạn để file utils.py cùng cấp
from .utils import import_historical_data 

def quantum_dashboard(request):
    """
    View chính xử lý hiển thị Dashboard và Logic tính toán
    """
    if request.method == "GET":
        # Lấy dữ liệu lịch sử để hiển thị bảng (10 ngày gần nhất)
        history_data = QuantumEngine.objects.all().order_by('-date')[:20]
        return render(request, 'quantum/dashboard.html', {'history': history_data})

    if request.method == "POST":
        try:
            # 1. Nhận dữ liệu từ Ajax gửi lên
            # Lưu ý: Nếu dùng FormData thì dùng request.POST, nếu JSON body thì dùng json.loads
            # Ở đây giả định dùng Form Submit bình thường hoặc FormData qua fetch
            
            data_date = request.POST.get('date')
            news_content = request.POST.get('news_content', '')
            farm_price = float(request.POST.get('farm_price', 0))
            midstream_price = float(request.POST.get('midstream_price', 0))
            
            if not data_date:
                return JsonResponse({"status": "error", "message": "Vui lòng chọn ngày!"}, status=400)

            # Chuyển đổi ngày
            target_date = datetime.strptime(data_date, '%Y-%m-%d').date()

            # 2. Lấy dữ liệu ngày hôm trước (để so sánh Trend)
            prev_data = QuantumEngine.objects.filter(date__lt=target_date).order_by('-date').first()
            
            # Khởi tạo giá trị mặc định nếu không có dữ liệu cũ
            prev_rc_close = prev_data.rc_close if (prev_data and prev_data.rc_close) else 0
            
            # --- LOGIC TÍNH TOÁN (Z-AXIS & VOLATILITY) ---
            # Volatility: Tính dựa trên 5 ngày gần nhất
            recent_days = QuantumEngine.objects.filter(date__lte=target_date).order_by('-date')[:5]
            closes = [d.rc_close for d in recent_days if d.rc_close]
            
            volatility = 0.05 # Mặc định
            if len(closes) > 1:
                volatility = np.std(closes) / np.mean(closes)

            # Trend Z: Logic so sánh Giá Nhập Tay (VND) vs Giá Futures Quy đổi (hoặc Giá hôm qua)
            # Ở đây ta so sánh: Giá Farm hôm nay vs Giá Farm hôm qua (nếu có)
            # Hoặc đơn giản: Giá Farm nhập vào phản ánh xu hướng gì so với kỳ vọng?
            
            trend_z = 0
            if prev_data and prev_data.manual_farm_gate_price > 0:
                # So sánh giá Farm hôm nay vs hôm qua
                delta = farm_price - prev_data.manual_farm_gate_price
                trend_z = delta / prev_data.manual_farm_gate_price * 100 # % thay đổi làm lực đẩy Z
            else:
                # Fallback: Dùng sentiment để đoán trend nếu không có giá cũ
                trend_z = 0 

            # 3. Chạy Quantum Engine
            engine = QuantumPredictor()
            sentiment_score = engine.analyze_sentiment(news_content)
            
            # Tổng hợp Trend Z từ cả Giá và Sentiment
            final_z = (trend_z * 0.7) + (sentiment_score * 0.3)

            results = engine.calculate_quantum_state(sentiment_score, final_z, volatility)

            # 4. Lưu vào Database
            obj, created = QuantumEngine.objects.update_or_create(
                date=target_date,
                defaults={
                    'manual_farm_gate_price': farm_price,
                    'manual_midstream_price': midstream_price,
                    'news_content': news_content,
                    'sentiment_score': results['sentiment'],
                    'market_trend_z': results['trend_z'],
                    'volatility_y': volatility,
                    'purity': results['purity'],
                    'bullish_prob': results['bullish_prob']
                }
            )

            return JsonResponse({
                "status": "success",
                "message": "Dự báo thành công!",
                "result": {
                    "purity": results['purity'],
                    "bullish_prob": results['bullish_prob'],
                    "sentiment": results['sentiment'],
                    "trend_z": results['trend_z'],
                    "date": str(target_date)
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

def import_data_historical(request):
    if request.method == "POST":
        try:
            rc_stock_file = request.FILES['rc_stock_file']
            kc_stock_file = request.FILES['kc_stock_file']
            rc_daily_file = request.FILES['rc_daily_file']
            kc_daily_file = request.FILES['kc_daily_file']

            import_historical_data(rc_stock_file, kc_stock_file, rc_daily_file, kc_daily_file)
            return JsonResponse({"status": "success", "message": "Import thành công!"}, status=200) 
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return render(request, 'quantum/import-history.html')