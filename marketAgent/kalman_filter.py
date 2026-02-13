import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. ĐỊNH NGHĨA LỚP KALMAN FILTER (Từ tài liệu)
# ==========================================
class CoffeeKalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimated_error, initial_value):
        """
        Q (process_variance): Độ biến động tự thân của thị trường.
        R (measurement_variance): Độ nhiễu của các quan sát (giá nhảy múa).
        """
        self.q = process_variance
        self.r = measurement_variance
        self.p = estimated_error
        self.x = initial_value

    def update(self, measurement):
        # Bước dự báo (Prediction)
        # Bước cập nhật (Update) - Công thức từ Chương 9 trong tài liệu
        kalman_gain = self.p / (self.p + self.r)
        self.x = self.x + kalman_gain * (measurement - self.x)
        self.p = (1 - kalman_gain) * self.p + self.q
        return self.x

# ==========================================
# 2. HÀM XỬ LÝ DỮ LIỆU (DATA PREPROCESSING)
# ==========================================
def load_and_merge_data():
    print("Đang đọc dữ liệu...")
    
    # Đọc giá Daily (Lấy Date và Close)
    df_price = pd.read_excel("C:/Users/COMPUTER/Desktop/KCK_DAILY.xlsx")
    df_price['Date'] = pd.to_datetime(df_price['Date'])
    
    # Đọc IV (Lấy Date và KCH26)
    df_iv = pd.read_excel("C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx")
    df_iv['Date'] = pd.to_datetime(df_iv['Date'])
    
    df_stock = pd.read_excel("C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx")
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])
    
    # Đọc CoT (Lấy Report_Date_as_MM_DD_YYYY và vị thế mua NonComm)
    df_cot = pd.read_excel("C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx")
    df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])
    
    # GỘP DỮ LIỆU (Merge)
    # Lấy bảng giá làm gốc
    final_df = df_price[['Date', 'Close']].sort_values('Date')
    
    final_df = pd.merge(final_df, df_iv[['Date', 'KCH26']], on='Date', how='left')
    final_df = pd.merge(final_df, df_stock[['Date', 'Bags']], left_on='Date', right_on='Date', how='left')
    final_df = pd.merge(final_df, df_cot[['Date', 'NonComm_Positions_Long_All']], on='Date', how='left')
    
    # Xử lý các ngày trống (Fill dữ liệu cũ cho ngày nghỉ/ngày chưa có báo cáo)
    final_df = final_df.ffill().dropna()
    
    return final_df

# ==========================================
# 3. HÀM CHẠY MÔ HÌNH VÀ PHÂN TÍCH
# ==========================================
def run_coffee_model():
    # 1. Nạp dữ liệu
    data = load_and_merge_data()
    
    # 2. Khởi tạo Kalman Filter 
    # Chúng ta dùng giá Close đầu tiên để làm điểm bắt đầu
    initial_price = data['Close'].iloc[0]
    kf = CoffeeKalmanFilter(process_variance=0.5, measurement_variance=50, estimated_error=100, initial_value=initial_price)
    
    # 3. Chạy lọc nhiễu cho giá
    data['Kalman_Price'] = data['Close'].apply(kf.update)
    
    # 4. Tính toán tương quan (Correlation)
    correlation = data['Close'].corr(data['Bags'])
    print(f"\nĐộ tương quan giữa Giá và Tồn kho: {correlation:.2f}")
    
    # 5. Vẽ biểu đồ
    fig, ax1 = plt.subplots(figsize=(14, 7))

    ax1.set_xlabel('Ngày')
    ax1.set_ylabel('Giá Cà phê (Close)', color='tab:blue')
    ax1.plot(data['Date'], data['Close'], label='Giá thực tế (Nhiễu)', color='lightblue', alpha=0.6)
    ax1.plot(data['Date'], data['Kalman_Price'], label='Xu hướng Kalman', color='red', linewidth=2)
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Vẽ thêm đường Tồn kho (Stock) ở trục bên phải để so sánh
    ax2 = ax1.twinx()
    ax2.set_ylabel('Tồn kho (Lots)', color='tab:green')
    ax2.plot(data['Date'], data['Bags'], label='Tồn kho (Stock)', color='tab:green', linestyle=':')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    plt.title('Phân tích Giá Cà phê kết hợp Tồn kho & Kalman Filter')
    fig.tight_layout()
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.show()

# ==========================================
# 4. CÁCH SỬ DỤNG
# ==========================================
if __name__ == "__main__":
    run_coffee_model()