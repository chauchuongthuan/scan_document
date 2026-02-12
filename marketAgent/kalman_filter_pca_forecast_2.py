import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from datetime import timedelta
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

# ==========================================
# 1. THIẾT LẬP LỊCH GIAO DỊCH (TRADING CALENDAR)
# ==========================================
# Định nghĩa ngày nghỉ lễ của sàn (ICE US thường nghỉ theo lịch lễ Liên bang Mỹ)
us_cal = USFederalHolidayCalendar()
trading_days = CustomBusinessDay(calendar=us_cal)
# ==========================================
# 2. LỚP KALMAN FILTER
# ==========================================
class SimpleKalman:
    def __init__(self, q=0.05, r=5, initial_value=0):
        self.q = q
        self.r = r
        self.p = 1.0
        self.x = initial_value

    def update(self, measurement):
        if np.isnan(measurement): return self.x # Bỏ qua nếu là NaN
        self.p = self.p + self.q
        kalman_gain = self.p / (self.p + self.r)
        self.x = self.x + kalman_gain * (measurement - self.x)
        self.p = (1 - kalman_gain) * self.p
        return self.x

# ==========================================
# 3. LOAD VÀ XỬ LÝ DỮ LIỆU (XỬ LÝ GAPS)
# ==========================================
def prepare_data():
    # Giả định các file CSV đã được load (Thay đổi đường dẫn nếu cần)
    df_price = pd.read_excel("C:/Users/COMPUTER/Desktop/KC_DAILY.xlsx").assign(Date=lambda x: pd.to_datetime(x['Date']))
    df_price = df_price.dropna(subset=['Close'])
    df_iv = pd.read_excel("C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx").assign(Date=lambda x: pd.to_datetime(x['Date']))
    df_stock = pd.read_excel("C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx")
    df_stock['Date'] = pd.to_datetime(df_stock['Date'], dayfirst=True)
    df_cot = pd.read_excel("C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx")
    df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

    # Merge dữ liệu ban đầu
    df = pd.merge(df_price[['Date', 'Close']], df_iv[['Date', 'KCH26']], on='Date', how='outer')
    df = pd.merge(df, df_stock[['Date', 'Bags']], on='Date', how='outer')
    df = pd.merge(df, df_cot[['Date', 'NonComm_Positions_Long_All']], on='Date', how='outer')
    
    df = df.sort_values('Date').reset_index(drop=True)

    # --- XỬ LÝ NGÀY TRỐNG ---
    # Tạo một khung thời gian liên tục từ ngày bắt đầu đến ngày kết thúc
    full_range = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
    df = df.set_index('Date').reindex(full_range)
    
    # Lọc bỏ Thứ 7 và Chủ Nhật (Thị trường chắc chắn đóng cửa)
    df = df[df.index.dayofweek < 5]
    
    # Với các ngày trong tuần mà thiếu dữ liệu (Gaps/Holidays), dùng ffill để bù đắp
    # Điều này giúp Kalman Filter không bị "gãy" đường trend
    df = df.ffill().bfill()
    df.index.name = 'Date'
    return df.reset_index()

# ==========================================
# 4. PHÂN TÍCH VÀ DỰ BÁO TƯƠNG LAI
# ==========================================
def run_enhanced_analysis():
    df = prepare_data()
    features = ['Close', 'KCH26', 'Bags', 'NonComm_Positions_Long_All']
    
    # PCA
    x_scaled = StandardScaler().fit_transform(df[features].values)
    pca = PCA(n_components=1)
    df['Coffee_Index'] = pca.fit_transform(x_scaled)
    
    # Kalman
    kf = SimpleKalman(initial_value=df['Coffee_Index'].iloc[0])
    df['Coffee_Index_Smooth'] = df['Coffee_Index'].apply(kf.update)

    # --- PHẦN DỰ BÁO TƯƠNG LAI (CHỈ TÍNH NGÀY GIAO DỊCH) ---
    forecast_steps = 5
    last_date = df['Date'].max()
    
    # Tạo 5 ngày giao dịch tiếp theo (Bỏ qua T7, CN và Lễ Mỹ)
    future_dates = []
    current_date = last_date
    for _ in range(forecast_steps):
        current_date = current_date + trading_days
        future_dates.append(current_date)
    
    # Dự báo dựa trên độ dốc 10 phiên gần nhất
    lookback = 10
    y = df['Coffee_Index_Smooth'].tail(lookback).values
    x = np.arange(lookback)
    slope, intercept = np.polyfit(x, y, 1)
    future_values = [slope * (lookback + i) + intercept for i in range(1, forecast_steps + 1)]
    
    # Tính độ dốc giá
    price_slope, _ = np.polyfit(x, df['Close'].tail(lookback).values, 1)

    # ==========================================
    # 5. HIỂN THỊ KẾT QUẢ
    # ==========================================
    print("\n" + "="*50)
    print(f"DỰ BÁO PHIÊN GIAO DỊCH TIẾP THEO ({future_dates[0].strftime('%Y-%m-%d')})")
    print("="*50)
    
    if price_slope < 0 and slope > 0:
        msg = "BULLISH DIVERGENCE: Giá giảm nhưng nội tại đang tích cực."
    elif price_slope > 0 and slope < 0:
        msg = "BEARISH DIVERGENCE: Giá tăng nhưng nội tại đang suy yếu."
    else:
        msg = "TREND CONTINUATION: Nội tại và giá đang đồng thuận."

    print(f"Tín hiệu: {msg}")
    print(f"Xu hướng nội tại 5 ngày tới: {'TĂNG' if slope > 0 else 'GIẢM'}")
    
    # Vẽ biểu đồ
    plt.figure(figsize=(15, 7))
    plt.plot(df['Date'], df['Coffee_Index_Smooth'], label='PCA Index (Smooth)', color='red', linewidth=2)
    
    # Vẽ đoạn dự báo (đường nét đứt)
    forecast_series_dates = [df['Date'].iloc[-1]] + future_dates
    forecast_series_values = [df['Coffee_Index_Smooth'].iloc[-1]] + future_values
    plt.plot(forecast_series_dates, forecast_series_values, 'r--', label='Dự báo (Trading Days only)')
    
    plt.title('PCA Coffee Index - Future Trading Days Projection')
    plt.axvspan(df['Date'].iloc[-1], future_dates[-1], color='gray', alpha=0.1)
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.show()

if __name__ == "__main__":
    run_enhanced_analysis()