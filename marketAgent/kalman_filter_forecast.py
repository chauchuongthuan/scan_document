import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

# ==========================================
# 1. KALMAN FILTER NÂNG CAO
# ==========================================
class SmartCoffeeKalman:
    def __init__(self, initial_value):
        self.x = initial_value
        self.p = 100 # Sai số ước tính ban đầu
        self.last_slope = 0

    def update(self, measurement, Q, R):
        old_x = self.x
        # Bước cập nhật với Q và R động từ dữ liệu
        kalman_gain = self.p / (self.p + R)
        self.x = self.x + kalman_gain * (measurement - self.x)
        self.p = (1 - kalman_gain) * self.p + Q
        
        self.last_slope = self.x - old_x
        return self.x

# ==========================================
# 2. XỬ LÝ DỮ LIỆU
# ==========================================
def load_and_merge_data():
    # Giữ nguyên các đường dẫn file của bạn
    # Đọc giá Daily
    df_price = pd.read_excel("C:/Users/COMPUTER/Desktop/KC_DAILY.xlsx")
    df_price['Date'] = pd.to_datetime(df_price['Date'])
    
    # Đọc IV
    df_iv = pd.read_excel("C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx")
    df_iv['Date'] = pd.to_datetime(df_iv['Date'])
    
    df_stock = pd.read_excel("C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx")
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])

    # Đọc CoT
    df_cot = pd.read_excel("C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx")
    df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])
    
    # Gộp dữ liệu
    df = pd.merge(df_price[['Date', 'Close']], df_iv[['Date', 'KCH26']], on='Date', how='left')
    df = pd.merge(df, df_stock[['Date', 'Bags']], left_on='Date', right_on='DATE', how='left')
    df = pd.merge(df, df_cot[['Date', 'NonComm_Positions_Long_All']], on='Date', how='left')
    
    return df.ffill().dropna().sort_values('Date')

# ==========================================
# 3. CHẠY DỰ BÁO TOÀN DIỆN
# ==========================================
def run_final_analysis():
    df = load_and_merge_data()
    
    # TÍNH TOÁN THAM SỐ TỪ DỮ LIỆU
    # R (Nhiễu đo lường) = Phương sai của giá trong 20 ngày
    df['Rolling_Var'] = df['Close'].rolling(window=20).var()
    
    kf = SmartCoffeeKalman(initial_value=df['Close'].iloc[0])
    
    kalman_results = []
    for i in range(len(df)):
        row = df.iloc[i]
        
        # R lấy từ phương sai thực tế, nếu chưa có (đầu mảng) thì lấy mặc định tạm thời
        R_dynamic = row['Rolling_Var'] if not np.isnan(row['Rolling_Var']) else 50
        
        # Q (Độ biến động hệ thống) tỷ lệ thuận với IV
        Q_dynamic = row['KCH26'] * 2 # IV càng cao, Q càng lớn
        
        kalman_val = kf.update(row['Close'], Q=Q_dynamic, R=R_dynamic)
        kalman_results.append(kalman_val)
        
    df['Kalman_Price'] = kalman_results

    # TÍNH LỰC ĐẨY TỪ COT (Dòng tiền)
    # Nếu phe Long tăng vị thế so với tuần trước -> Lực đẩy dương
    df['CoT_Momentum'] = df['NonComm_Positions_Long_All'].diff() / df['NonComm_Positions_Long_All'].shift()

    # DỰ BÁO 5 NGÀY
    last_slope = kf.last_slope
    last_cot_momentum = df['CoT_Momentum'].iloc[-1]
    last_price = df['Kalman_Price'].iloc[-1]
    
    forecast_days = 5
    # Dự báo = Giá cuối + (Độ dốc Kalman * ngày) + (Ảnh hưởng từ dòng tiền CoT)
    forecast_prices = [last_price + (last_slope * i) + (last_cot_momentum * 10 * i) for i in range(1, forecast_days + 1)]
    
    print("--- KẾT QUẢ DỰ BÁO DỰA TRÊN DATA THẬT ---")
    for i, p in enumerate(forecast_prices, 1):
        print(f"Ngày T+{i}: {p:.2f}")

    # Vẽ biểu đồ
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df['Date'], df['Close'], alpha=0.3, label='Giá thị trường')
    ax1.plot(df['Date'], df['Kalman_Price'], color='red', label='Xu hướng Kalman (R & Q động)')
    
    # Vẽ đoạn dự báo
    future_dates = [df['Date'].iloc[-1] + timedelta(days=i) for i in range(1, 6)]
    ax1.plot(future_dates, forecast_prices, 'ro--', label='Dự báo 5 ngày')
    
    ax1.legend()

    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df['Bags'], label='Tồn kho Lots (Stock)', color='tab:green', linestyle=':')
    ax2.tick_params(axis='y', labelcolor='tab:green')
    ax2.legend()
    plt.title("Mô hình Kalman")
    plt.show()

if __name__ == "__main__":
    run_final_analysis()