from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import os
from django.conf import settings
import json
from rest_framework.views import APIView

class SimpleMarketDataLoader:
    """
    Load dữ liệu thị trường đơn giản từ file Excel/CSV
    """
    
    @staticmethod
    def load_latest_data_from_file(uploaded_file):
        """
        Load dữ liệu thị trường mới nhất từ file
        """
        try:
            # Đọc file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Tìm cột ngày
            date_column = None
            for col in df.columns:
                if 'date' in col.lower() or 'ngày' in col.lower() or col == 'C':
                    date_column = col
                    break
            
            if date_column is None and len(df.columns) >= 3:
                date_column = df.columns[2]  # Cột C
            
            if date_column is None:
                date_column = df.columns[0]
            
            # Chuyển đổi ngày
            df['Date'] = pd.to_datetime(df[date_column], errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')
            
            if len(df) < 2:
                raise ValueError("Cần ít nhất 2 ngày dữ liệu")
            
            # Lấy dữ liệu 2 ngày gần nhất
            last_day = df.iloc[-1]
            prev_day = df.iloc[-2]
            
            result = {
                'date': last_day['Date'].strftime('%Y-%m-%d'),
                'open': float(last_day.get('Open', 0)),
                'high': float(last_day.get('High', 0)),
                'low': float(last_day.get('Low', 0)),
                'close': float(last_day.get('Close', 0)),
                'volume': float(last_day.get('Volume', 0)) if 'Volume' in df.columns else 0,
                'prev_close': float(prev_day.get('Close', 0)),
                'prev_date': prev_day['Date'].strftime('%Y-%m-%d'),
                'total_days': len(df)
            }
            
            return result
            
        except Exception as e:
            print(f"Lỗi load dữ liệu đơn giản: {str(e)}")
            raise

class MarketPredictorForToday:
    """
    Dự đoán biến động cho NGÀY HÔM NAY dựa trên:
    - Entropy của bản tin NGÀY HÔM NAY
    - Dữ liệu giá đến NGÀY HÔM QUA
    """
    
    @staticmethod
    def predict_today_move(entropy_score: float, historical_data: dict) -> dict:
        """
        Dự đoán biến động cho NGÀY HÔM NAY - LOGIC XÁC ĐỊNH (KHÔNG NGẪU NHIÊN)
        """
        try:
            last_day = historical_data['last_day_data']
            features = historical_data['historical_features']
            
            # Ngày dự đoán là HÔM NAY
            last_day_date = last_day['date']
            today_date = datetime.now().strftime('%Y-%m-%d')
            last_close = last_day['close']
            last_volume = last_day.get('volume', 0)
            
            # Lấy các chỉ số từ features
            avg_volume = features.get('avg_volume_20d', last_volume)
            volatility_5d = features.get('volatility_5d', 1.0)
            avg_daily_range_pct = features.get('avg_daily_range_pct', 1.5)
            trend_3d = features.get('trend_3d', 0)
            trend_5d = features.get('trend_5d', 0)
            trend_10d = features.get('trend_10d', 0)
            
            # TÍNH VOLUME RATIO
            volume_ratio = 1.0
            if avg_volume > 0:
                volume_ratio = last_volume / avg_volume
            
            # 1. XÁC ĐỊNH HƯỚNG (DIRECTION) - LOGIC XÁC ĐỊNH
            
            # Tính điểm cho BULLISH (tăng)
            bullish_score = 0
            bearish_score = 0
            
            # a. Xu hướng dài hạn (trend_10d) - trọng số cao
            if trend_10d > 2.0:
                bullish_score += 3
            elif trend_10d > 1.0:
                bullish_score += 2
            elif trend_10d > 0:
                bullish_score += 1
            elif trend_10d < -2.0:
                bearish_score += 3
            elif trend_10d < -1.0:
                bearish_score += 2
            elif trend_10d < 0:
                bearish_score += 1
            
            # b. Xu hướng ngắn hạn (trend_3d, trend_5d)
            if trend_5d > 1.5:
                bullish_score += 2
            elif trend_5d > 0.5:
                bullish_score += 1
            elif trend_5d < -1.5:
                bearish_score += 2
            elif trend_5d < -0.5:
                bearish_score += 1
                
            if trend_3d > 1.0:
                bullish_score += 1
            elif trend_3d < -1.0:
                bearish_score += 1
            
            # c. Volume xác nhận
            if volume_ratio > 1.3:  # Volume cao
                if trend_3d > 0:
                    bullish_score += 2  # Volume xác nhận uptrend
                elif trend_3d < 0:
                    bearish_score += 2  # Volume xác nhận downtrend
            
            # d. Vị trí so với support/resistance
            current_price = last_close
            support = features.get('support_level', current_price * 0.98)
            resistance = features.get('resistance_level', current_price * 1.02)
            
            distance_to_support_pct = ((current_price - support) / current_price) * 100
            distance_to_resistance_pct = ((resistance - current_price) / current_price) * 100
            
            # Nếu giá gần support -> tăng khả năng bounce lên
            if distance_to_support_pct < 1.0:
                bullish_score += 2
            
            # Nếu giá gần resistance -> tăng khả năng pullback xuống
            if distance_to_resistance_pct < 1.0:
                bearish_score += 2
            
            # e. RSI (nếu có)
            rsi = features.get('rsi_14', 50)
            if rsi > 70:  # Quá mua
                bearish_score += 1
            elif rsi < 30:  # Quá bán
                bullish_score += 1
            
            # 2. QUYẾT ĐỊNH HƯỚNG CUỐI CÙNG
            direction_multiplier = 0
            base_direction = "neutral"
            
            if bullish_score > bearish_score:
                direction_multiplier = 1  # LÊN
                base_direction = "bullish"
            elif bearish_score > bullish_score:
                direction_multiplier = -1  # XUỐNG
                base_direction = "bearish"
            else:
                # Bằng nhau, kiểm tra các yếu tố khác
                if trend_5d > 0:
                    direction_multiplier = 1
                    base_direction = "bullish"
                elif trend_5d < 0:
                    direction_multiplier = -1
                    base_direction = "bearish"
                else:
                    direction_multiplier = 0
                    base_direction = "neutral"
            
            # 3. TÍNH ĐỘ LỚN BIẾN ĐỘNG (MAGNITUDE)
            # Base volatility từ dữ liệu thực
            base_volatility = volatility_5d
            
            # Điều chỉnh theo entropy - LOGIC XÁC ĐỊNH
            # Entropy cao -> biến động cao hơn, nhưng không quá cực đoan
            if entropy_score > 0.8:
                entropy_multiplier = 1.8  # Cao nhưng hợp lý
            elif entropy_score > 0.6:
                entropy_multiplier = 1.4
            elif entropy_score > 0.4:
                entropy_multiplier = 1.0
            else:
                entropy_multiplier = 0.7
            
            # Base move dựa trên volatility thực tế và entropy
            base_move_percent = base_volatility * entropy_multiplier
            
            # Điều chỉnh theo strength of trend
            trend_strength = abs(trend_5d) / 100.0  # Chuyển % sang decimal
            if base_direction == "bullish" and trend_5d > 0:
                base_move_percent *= (1 + min(0.5, trend_strength))  # Tăng thêm nếu có trend mạnh
            elif base_direction == "bearish" and trend_5d < 0:
                base_move_percent *= (1 + min(0.5, abs(trend_strength)))
            
            # Giới hạn base_move_percent trong phạm vi hợp lý
            # Thị trường thường biến động 0.2-2.5% mỗi ngày
            base_move_percent = max(0.1, min(2.5, base_move_percent))
            
            # Tính điểm biến động
            predicted_move = last_close * (base_move_percent / 100) * direction_multiplier
            predicted_price = current_price + predicted_move
            predicted_change_percent = (predicted_move / current_price) * 100
            
            # 4. ĐIỀU CHỈNH CUỐI CÙNG THEO SUPPORT/RESISTANCE
            
            # Nếu gần support và đang dự đoán xuống -> giảm độ lớn
            if distance_to_support_pct < 1.0 and predicted_change_percent < 0:
                predicted_move *= 0.6  # Giảm 40%
                predicted_change_percent *= 0.6
            
            # Nếu gần resistance và đang dự đoán lên -> giảm độ lớn
            if distance_to_resistance_pct < 1.0 and predicted_change_percent > 0:
                predicted_move *= 0.6  # Giảm 40%
                predicted_change_percent *= 0.6
            
            # 5. GIỚI HẠN THEO RANGE TRUNG BÌNH
            # Không vượt quá 1.2 lần range trung bình
            max_move_pct = avg_daily_range_pct * 1.2
            if abs(predicted_change_percent) > max_move_pct:
                reduction_factor = max_move_pct / abs(predicted_change_percent)
                predicted_change_percent *= reduction_factor
                predicted_move *= reduction_factor
            
            # Tính lại giá dự đoán sau các điều chỉnh
            predicted_price = current_price + (current_price * (predicted_change_percent / 100))
            
            # 6. XÁC ĐỊNH DIRECTION VÀ ACTION CUỐI CÙNG
            if predicted_change_percent > 0.3:  # Ngưỡng thấp hơn cho thực tế
                direction = "bullish"
                action = "MUA"
            elif predicted_change_percent < -0.3:
                direction = "bearish"
                action = "BÁN"
            else:
                direction = "neutral"
                action = "QUAN SÁT"
            
            # Tính confidence với volume xác nhận
            confidence = MarketPredictorForToday._calculate_confidence(
                entropy_score, features, historical_data.get('num_days', 0),
                volume_ratio, abs(predicted_change_percent),
                abs(bullish_score - bearish_score)  # Thêm strength of signal
            )
            
            # Tính risk level với volatility thực tế
            risk_level = MarketPredictorForToday._calculate_risk_level(
                entropy_score, volatility_5d, abs(predicted_change_percent)
            )
            
            return {
                "prediction_date": today_date,
                "last_data_date": last_day_date,
                "predicted_move": float(round(predicted_move, 2)),
                "predicted_price": float(round(predicted_price, 2)),
                "last_close_price": float(round(current_price, 2)),
                "predicted_change_percent": float(round(predicted_change_percent, 2)),
                "direction": direction,
                "action": action,
                "confidence": float(round(confidence, 2)),
                "risk_level": risk_level,
                "entropy_impact": float(round(entropy_score * 100, 1)),
                "volume_ratio": float(round(volume_ratio, 2)),
                "signal_strength": abs(bullish_score - bearish_score),  # Độ mạnh của tín hiệu
                "market_context": {
                    "trend_3d": float(round(trend_3d, 2)),
                    "trend_5d": float(round(trend_5d, 2)),
                    "trend_10d": float(round(trend_10d, 2)),
                    "volatility_5d": float(round(volatility_5d, 2)),
                    "avg_daily_range_pct": float(round(avg_daily_range_pct, 2)),
                    "avg_gap_pct": float(round(features.get('avg_gap_pct', 0.5), 2)),
                    "support": float(round(support, 2)),
                    "resistance": float(round(resistance, 2)),
                    "avg_volume": float(round(avg_volume, 0)),
                    "last_volume": float(round(last_volume, 0)),
                    "rsi": float(round(features.get('rsi_14', 50), 1)),
                    "bullish_score": bullish_score,
                    "bearish_score": bearish_score,
                    "distance_to_support_pct": float(round(distance_to_support_pct, 2)),
                    "distance_to_resistance_pct": float(round(distance_to_resistance_pct, 2))
                }
            }
            
        except Exception as e:
            return {
                "prediction_date": datetime.now().strftime('%Y-%m-%d'),
                "predicted_move": 0.0,
                "predicted_price": 0.0,
                "direction": "neutral",
                "action": "KHÔNG THỂ DỰ ĐOÁN",
                "confidence": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    def _calculate_confidence(entropy_score, features, num_days, volume_ratio, move_percent, signal_strength):
        """Tính độ tin cậy của dự đoán với volume xác nhận và signal strength"""
        confidence = 0.5  # Base 50%
        
        # 1. Đánh giá entropy
        if 0.3 <= entropy_score <= 0.7:
            confidence += 0.15
        elif entropy_score > 0.8:
            confidence -= 0.1
        elif entropy_score < 0.3:
            confidence += 0.05
        
        # 2. Đánh giá volume - QUAN TRỌNG
        if volume_ratio > 1.3:
            confidence += 0.2
        elif volume_ratio > 1.1:
            confidence += 0.1
        elif volume_ratio < 0.7:
            confidence -= 0.15
        
        # 3. Đánh giá signal strength
        if signal_strength >= 4:
            confidence += 0.15
        elif signal_strength >= 2:
            confidence += 0.1
        elif signal_strength == 0:
            confidence -= 0.1  # Tín hiệu yếu
        
        # 4. Đánh giá số ngày dữ liệu
        if num_days >= 30:
            confidence += 0.15
        elif num_days >= 20:
            confidence += 0.1
        elif num_days < 10:
            confidence -= 0.1
        
        # 5. Đánh giá volatility
        volatility = features.get('volatility_5d', 0)
        if 0.5 <= volatility <= 2.0:
            confidence += 0.1
        elif volatility > 3.0:
            confidence -= 0.15
        elif volatility < 0.3:
            confidence -= 0.05
        
        # 6. Đánh giá move_percent hợp lý
        if move_percent > 3.0:
            confidence -= 0.15
        elif move_percent > 2.0:
            confidence -= 0.05
        
        # Giới hạn confidence trong khoảng 10-90%
        return max(0.1, min(0.9, confidence))
    
    @staticmethod
    def _calculate_risk_level(entropy_score, volatility, move_percent):
        """Tính mức rủi ro với volatility thực tế"""
        risk_score = (entropy_score * 0.4) + (volatility / 5 * 0.4) + (move_percent / 10 * 0.2)
        
        if risk_score > 0.5:
            return "CAO"
        elif risk_score > 0.35:
            return "TRUNG BÌNH CAO"
        elif risk_score > 0.25:
            return "TRUNG BÌNH"
        elif risk_score > 0.15:
            return "THẤP"
        else:
            return "RẤT THẤP"


class TodayMarketDataLoader:
    """
    Load dữ liệu để dự đoán cho NGÀY HÔM NAY
    """
    
    @staticmethod
    def load_data_for_today_prediction(uploaded_file) -> dict:
        """
        Load dữ liệu từ file Excel để dự đoán cho hôm nay
        
        Args:
            uploaded_file: File Excel chứa dữ liệu đến NGÀY HÔM QUA
        
        Returns:
            Dict chứa:
            - last_day_data: OHLC của ngày giao dịch cuối cùng (09/12)
            - historical_features: Các chỉ số từ lịch sử
            - num_days: Số ngày dữ liệu có sẵn
        """
        try:
            # Đọc file Excel
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Tìm cột ngày
            date_column = None
            for col in df.columns:
                if 'date' in col.lower() or 'ngày' in col.lower() or col == 'C':
                    date_column = col
                    break
            
            if date_column is None and len(df.columns) >= 3:
                date_column = df.columns[2]  # Cột C
            
            if date_column is None:
                date_column = df.columns[0]
            
            # Chuyển đổi ngày
            df['Date'] = pd.to_datetime(df[date_column], errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')
            
            if len(df) < 2:
                raise ValueError("Cần ít nhất 2 ngày dữ liệu để dự đoán")
            
            # Lấy dữ liệu NGÀY CUỐI CÙNG (09/12)
            last_day = df.iloc[-1]
            last_day_data = {
                'date': last_day['Date'].strftime('%Y-%m-%d'),
                'open': float(last_day.get('Open', 0)),
                'high': float(last_day.get('High', 0)),
                'low': float(last_day.get('Low', 0)),
                'close': float(last_day.get('Close', 0)),
                'volume': float(last_day.get('Volume', 0)) if 'Volume' in df.columns else 0
            }
            
            # Tính các chỉ số từ lịch sử (loại trừ ngày cuối cùng nếu cần)
            historical_df = df.iloc[:-1] if len(df) > 5 else df
            
            historical_features = {
                # Trend
                'trend_3d': TodayMarketDataLoader._calculate_trend(historical_df, 'Close', 3),
                'trend_5d': TodayMarketDataLoader._calculate_trend(historical_df, 'Close', 5),
                'trend_10d': TodayMarketDataLoader._calculate_trend(historical_df, 'Close', 10),
                
                # Volatility
                'volatility_5d': TodayMarketDataLoader._calculate_volatility(historical_df, 'Close', 5),
                
                # Support và Resistance (từ 20 ngày trước)
                'support_level': TodayMarketDataLoader._calculate_support(historical_df, lookback=20),
                'resistance_level': TodayMarketDataLoader._calculate_resistance(historical_df, lookback=20),
                
                # Average daily range
                'avg_daily_range': TodayMarketDataLoader._calculate_avg_range(historical_df),
                
                # Gap analysis
                'avg_gap': TodayMarketDataLoader._calculate_avg_gap(historical_df),
            }
            
            return {
                'last_day_data': last_day_data,
                'historical_features': historical_features,
                'num_days': len(df)
            }
            
        except Exception as e:
            print(f"Lỗi load dữ liệu: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_trend(df, column, days):
        """Tính xu hướng"""
        if len(df) < days:
            return 0
        
        recent = df.tail(days)[column].values
        if len(recent) < 2:
            return 0
        
        start_price = recent[0]
        end_price = recent[-1]
        
        return ((end_price - start_price) / start_price * 100) if start_price != 0 else 0
    
    @staticmethod
    def _calculate_volatility(df, column, days):
        """Tính độ biến động"""
        if len(df) < days:
            return 0
        
        recent = df.tail(days)[column].values
        print("_calculate_volatility recent", recent)
        returns = np.diff(recent) / recent[:-1] * 100
        print("_calculate_volatility returns", returns)
        print("np.std(returns) if len(returns) > 0 else 0", np.std(returns) if len(returns) > 0 else 0)
        return np.std(returns) if len(returns) > 0 else 0
    
    @staticmethod
    def _calculate_support(df, lookback=20):
        """Tính mức hỗ trợ"""
        if len(df) < lookback:
            return df['Low'].min() if 'Low' in df.columns else 0
        
        return df.tail(lookback)['Low'].min()
    
    @staticmethod
    def _calculate_resistance(df, lookback=20):
        """Tính mức kháng cự"""
        if len(df) < lookback:
            return df['High'].max() if 'High' in df.columns else 0
        
        return df.tail(lookback)['High'].max()
    
    @staticmethod
    def _calculate_avg_range(df):
        """Tính range trung bình"""
        if len(df) < 5:
            return 0
        
        if 'High' in df.columns and 'Low' in df.columns:
            ranges = (df['High'] - df['Low']).tail(20)
            return ranges.mean() if len(ranges) > 0 else 0
        
        return 0
    
    @staticmethod
    def _calculate_avg_gap(df):
        """Tính gap trung bình"""
        if len(df) < 3:
            return 0
        
        if 'Open' in df.columns and 'Close' in df.columns:
            gaps = []
            for i in range(1, len(df)):
                gap = abs(df.iloc[i]['Open'] - df.iloc[i-1]['Close'])
                gaps.append(gap)
            
            return np.mean(gaps) if gaps else 0
        
        return 0


class PredictTodayMarketMoveView(View):
    """
    API view để dự đoán biến động cho NGÀY HÔM NAY
    """
    
    @staticmethod
    @login_required(login_url="login_cms")
    def post(request):
        """
        API dự đoán biến động cho NGÀY HÔM NAY
        """
        if request.method == 'POST':
            try:
                # Lấy entropy_score của bản tin HÔM NAY
                entropy_score = request.POST.get('entropy_score', '')
                if not entropy_score:
                    return JsonResponse({
                        "status": "error",
                        "message": "Thiếu tham số entropy_score"
                    }, status=400)
                
                entropy_score = float(entropy_score)
                
                # Kiểm tra file upload
                if 'excel_file' not in request.FILES:
                    return JsonResponse({
                        "status": "error", 
                        "message": "Vui lòng upload file Excel"
                    }, status=400)
                
                excel_file = request.FILES['excel_file']
                
                # Load dữ liệu đến NGÀY HÔM QUA
                market_data = TodayMarketDataLoader.load_data_for_today_prediction(excel_file)
                
                # Dự đoán cho HÔM NAY
                prediction = MarketPredictorForToday.predict_today_move(entropy_score, market_data)
                
                # Trả về kết quả
                return JsonResponse({
                    "status": "success",
                    "message": "Dự đoán biến động cho hôm nay thành công!",
                    "result": {
                        "entropy_score": entropy_score,
                        "entropy_source": "Bản tin tóm tắt thị trường NGÀY HÔM NAY",
                        "prediction": prediction,
                        "data_context": {
                            "last_trading_day": market_data['last_day_data']['date'],
                            "prediction_day": prediction['prediction_date'],
                            "note": "Dự đoán biến động cho ngày hôm nay dựa trên entropy của bản tin hôm nay và dữ liệu giá đến hôm qua"
                        }
                    }
                })
                
            except ValueError as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Dữ liệu không hợp lệ: {str(e)}"
                }, status=400)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    "status": "error",
                    "message": f"Dự đoán thất bại: {str(e)}"
                }, status=400)

        return render(request, 'entropy/predict_market.html')
class GetMarketDataView(View):
    """
    API view để lấy dữ liệu thị trường từ file upload
    """
    
    @staticmethod
    @login_required(login_url="login_cms")
    def post(request):
        """
        API lấy dữ liệu thị trường từ file upload
        """
        if request.method == 'POST':
            try:
                # Kiểm tra file upload
                if 'excel_file' not in request.FILES:
                    return JsonResponse({
                        "status": "error", 
                        "message": "Vui lòng upload file Excel"
                    }, status=400)
                
                excel_file = request.FILES['excel_file']
                
                # Kiểm tra định dạng file
                if not excel_file.name.endswith(('.xlsx', '.xls', '.csv')):
                    return JsonResponse({
                        "status": "error",
                        "message": "File phải có định dạng .xlsx, .xls hoặc .csv"
                    }, status=400)
                
                # Load dữ liệu
                market_data = SimpleMarketDataLoader.load_latest_data_from_file(excel_file)
                
                # Tính các chỉ số
                change = market_data.get('close', 0) - market_data.get('prev_close', 0)
                change_pct = (change / market_data.get('prev_close', 1)) * 100 if market_data.get('prev_close', 0) != 0 else 0
                
                return JsonResponse({
                    "status": "success",
                    "message": "Lấy dữ liệu thành công!",
                    "result": {
                        "market_data": market_data,
                        "analysis": {
                            "daily_change": float(round(change, 2)),
                            "daily_change_pct": float(round(change_pct, 2)),
                            "is_up": change > 0,
                            "is_down": change < 0,
                            "range_percent": ((market_data.get('high', 0) - market_data.get('low', 0)) / market_data.get('open', 1)) * 100 
                                             if market_data.get('open', 0) != 0 else 0
                        }
                    }
                })
                
            except Exception as e:
                import traceback
                print(f"Error in get market data: {traceback.format_exc()}")
                
                return JsonResponse({
                    "status": "error",
                    "message": f"Lấy dữ liệu thất bại: {str(e)}"
                }, status=400)
        
        return JsonResponse({
            "status": "error",
            "message": "Method not allowed"
        }, status=405)