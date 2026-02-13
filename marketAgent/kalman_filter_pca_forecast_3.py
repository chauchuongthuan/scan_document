import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from datetime import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

# ==========================================
# 1. THIẾT LẬP LỊCH GIAO DỊCH (TRADING CALENDAR)
# ==========================================
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
        if np.isnan(measurement): return self.x 
        self.p = self.p + self.q
        kalman_gain = self.p / (self.p + self.r)
        self.x = self.x + kalman_gain * (measurement - self.x)
        self.p = (1 - kalman_gain) * self.p
        return self.x

# ==========================================
# 3. LOAD VÀ XỬ LÝ DỮ LIỆU
# ==========================================
def prepare_data():
    # --- ĐƯỜNG DẪN FILE (Vui lòng kiểm tra lại đường dẫn này) ---
    path_price = "C:/Users/COMPUTER/Desktop/KCK_DAILY.xlsx"
    path_iv = "C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx"
    path_stock = "C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx"
    path_cot = "C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx"

    # Load dữ liệu
    df_price = pd.read_excel(path_price).assign(Date=lambda x: pd.to_datetime(x['Date']))
    df_iv = pd.read_excel(path_iv).assign(Date=lambda x: pd.to_datetime(x['Date']))
    
    # File stock cần skip 2 dòng đầu
    df_stock = pd.read_excel(path_stock)
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])
    
    df_cot = pd.read_excel(path_cot)
    df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

    # 1. Hợp nhất dữ liệu (Outer join để không mất ngày nào)
    df = pd.merge(df_price[['Date', 'Close']], df_iv[['Date', 'KCH26']], on='Date', how='outer')
    df = pd.merge(df, df_stock[['Date', 'Bags']], on='Date', how='outer')
    df = pd.merge(df, df_cot[['Date', 'NonComm_Positions_Long_All']], on='Date', how='outer')
    
    # 2. Sửa lỗi ngày tương lai: Chỉ lấy dữ liệu từ quá khứ đến hiện tại (9/2/2026)
    today = pd.Timestamp(datetime.now().date())
    df = df[df['Date'] <= today].sort_values('Date')

    # 3. Tạo khung lịch giao dịch chuẩn (Chỉ gồm các ngày đi làm của sàn)
    # Lấy từ ngày có giá đầu tiên đến ngày hôm nay (hoặc ngày cuối cùng có giá)
    start_date = df['Date'].min()
    end_date = df[df['Close'].notna()]['Date'].max()
    
    # Nếu ngày cuối có giá là thứ 6 (6/2), lịch chuẩn sẽ bao gồm cả thứ 2 (9/2)
    full_business_range = pd.date_range(start=start_date, end=today, freq=trading_days)
    
    # Reindex theo lịch chuẩn: Các ngày thiếu (giao dịch nhưng ko có data) sẽ để NaN
    df = df.set_index('Date').reindex(full_business_range)
    
    # 4. Xử lý lấp đầy dữ liệu để tính toán (Chỉ ffill sau khi đã định hình khung ngày chuẩn)
    # Điều này đảm bảo PCA và Kalman có đủ số liệu liên tục
    df = df.ffill().bfill()
    
    df.index.name = 'Date'
    return df.reset_index()

# ==========================================
# 4. PHÂN TÍCH VÀ DỰ BÁO
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

    # --- TÍNH TOÁN DỰ BÁO ---
    forecast_steps = 5
    last_date = df['Date'].max()
    
    # Tạo danh sách các ngày giao dịch tiếp theo (bắt đầu từ sau ngày cuối trong data)
    future_dates = []
    curr = last_date
    for _ in range(forecast_steps):
        curr = curr + trading_days
        future_dates.append(curr)
    
    # Dự báo nội tại (Slope 10 phiên)
    lookback = 10
    y = df['Coffee_Index_Smooth'].tail(lookback).values
    x = np.arange(lookback)
    slope, intercept = np.polyfit(x, y, 1)
    future_values = [slope * (lookback + i) + intercept for i in range(1, forecast_steps + 1)]
    
    # Độ dốc giá thực tế
    price_slope, _ = np.polyfit(x, df['Close'].tail(lookback).values, 1)

    # --- HIỂN THỊ ---
    print("\n" + "="*50)
    print(f"NGÀY HIỆN TẠI: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"DỰ BÁO PHIÊN TIẾP THEO: {future_dates[0].strftime('%Y-%m-%d')}")
    print("="*50)
    
    status = "TĂNG" if slope > 0 else "GIẢM"
    if price_slope < 0 and slope > 0:
        msg = "PHÂN KỲ DƯƠNG (BULLISH): Giá giảm nhưng nội tại đang âm thầm mạnh lên."
    elif price_slope > 0 and slope < 0:
        msg = "PHÂN KỲ ÂM (BEARISH): Giá tăng nhưng nội tại đang suy yếu."
    else:
        msg = "XU HƯỚNG ĐỒNG THUẬN: Nội tại và giá đang đi cùng hướng."

    print(f"Tín hiệu: {msg}")
    print(f"Xu hướng nội tại 5 ngày tới: {status}")
    
    # Biểu đồ
    plt.figure(figsize=(15, 7))
    plt.plot(df['Date'], df['Coffee_Index_Smooth'], label='Nội tại (PCA + Kalman)', color='blue', linewidth=2)
    
    # Đường dự báo nét đứt
    f_dates = [df['Date'].iloc[-1]] + future_dates
    f_vals = [df['Coffee_Index_Smooth'].iloc[-1]] + future_values
    plt.plot(f_dates, f_vals, 'r--', label=f'Dự báo {forecast_steps} ngày tới')
    
    plt.title('Coffee Market Intrinsic Index Forecast')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    run_enhanced_analysis()