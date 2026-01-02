from django.shortcuts import render
from django.http import JsonResponse
from .utils import fetch_historical_data
from .models import CoffeeQuantumModel
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import numpy as np
from datetime import datetime

def quantum_dashboard(request):
    # Hiển thị trang dashboard
    history = CoffeeQuantumModel.objects.all().order_by('-date')[:10]
    return render(request, 'quantum/dashboard_v2.html', {'history': history})

# --- Component 1: Dự báo dựa trên Số liệu (Numerical) ---
def analyze_numerical(request):
    if request.method == "POST":
        date_str = request.POST.get('date')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        farm_price = float(request.POST.get('farm_price', 0))

        # Lấy dữ liệu T-1
        hist = fetch_historical_data(target_date)
        if not hist:
            return JsonResponse({"status": "error", "message": "Không tìm thấy dữ liệu CSV ngày hôm trước"})

        # Logic Quantum cho Robusta (RC)
        # Q0: Price Momentum, Q1: IV, Q2: Stock
        qc_rc = QuantumCircuit(3)
        
        # Chuẩn hóa (Normalize)
        # Giả sử giá Farm hôm nay tăng so với sàn hôm qua là tín hiệu Bull
        price_ratio = min(max(farm_price / (hist['RC']['close'] * 25), 0), 1) # Ví dụ quy đổi
        
        qc_rc.ry(price_ratio * np.pi, 0)
        qc_rc.ry(hist['RC']['iv'] * np.pi, 1)
        qc_rc.ry(0.5 * np.pi, 2) # Stock normalize
        
        qc_rc.cx(0, 1)
        state_rc = Statevector.from_instruction(qc_rc)
        prob_rc = sum(state_rc.probabilities([0, 1])) / 2 # Lấy xác suất trung bình

        # Lưu vào database
        record, _ = CoffeeQuantumModel.objects.update_or_create(
            date=target_date,
            defaults={'farm_gate_price': farm_price, 'rc_bullish_prob': prob_rc}
        )

        return JsonResponse({
            "status": "success",
            "rc_prob": round(prob_rc, 4),
            "rc_status": "Tăng" if prob_rc > 0.5 else "Giảm"
        })

# --- Component 2: Dự báo dựa trên Text Synopsis (Qualitative) ---
def analyze_text_input(request):
    if request.method == "POST":
        date_str = request.POST.get('date')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Lấy các field nhập tay
        vol = float(request.POST.get('volume_tons', 0))
        diff = float(request.POST.get('diff_value', 0))
        weather = float(request.POST.get('weather_score', 0.5))

        # Mạch lượng tử 3 Qubit
        qc = QuantumCircuit(3)
        
        # Encoding
        theta_vol = min(vol / 5000, 1) * np.pi
        theta_diff = min(abs(diff) / 250, 1) * np.pi
        theta_weather = weather * np.pi # 0: nắng, 1: mưa

        qc.ry(theta_vol, 0)
        qc.ry(theta_diff, 1)
        qc.rz(theta_weather, 2)
        
        qc.h(1)
        qc.cx(0, 1)
        qc.cx(1, 2)

        state = Statevector.from_instruction(qc)
        prob = sum(state.probabilities()[4:]) # Trạng thái 1xx

        sentiment = "Trung tính"
        if prob > 0.6: sentiment = "Tích cực (Bullish)"
        elif prob < 0.4: sentiment = "Tiêu cực (Bearish)"

        CoffeeQuantumModel.objects.update_or_create(
            date=target_date,
            defaults={
                'trade_volume': vol,
                'diff_value': diff,
                'weather_score': weather,
                'text_sentiment': sentiment
            }
        )

        return JsonResponse({
            "status": "success",
            "sentiment": sentiment,
            "quantum_score": round(prob, 4)
        })