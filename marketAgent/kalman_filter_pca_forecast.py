import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ==========================================
# 1. LỚP KALMAN FILTER (Để làm mượt chỉ số PCA)
# ==========================================
class SimpleKalman:
    def __init__(self, q=0.1, r=10, initial_value=0):
        self.q = q
        self.r = r
        self.p = 1.0
        self.x = initial_value

    def update(self, measurement):
        self.p = self.p + self.q
        kalman_gain = self.p / (self.p + self.r)
        self.x = self.x + kalman_gain * (measurement - self.x)
        self.p = (1 - kalman_gain) * self.p
        return self.x

# ==========================================
# 2. LOAD VÀ CLEAN DỮ LIỆU
# ==========================================
def prepare_data():
    # Load các file (Giữ nguyên logic của bạn)
    # Đọc giá Daily
    df_price = pd.read_excel("C:/Users/COMPUTER/Desktop/KCK_DAILY.xlsx")
    df_price['Date'] = pd.to_datetime(df_price['Date'])
    
    # Đọc IV
    df_iv = pd.read_excel("C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx")
    df_iv['Date'] = pd.to_datetime(df_iv['Date'])
    
    df_stock = pd.read_excel("C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx")
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])
    
    # Đọc CoT
    df_cot = pd.read_excel("C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx")
    df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

    # Gộp dữ liệu thành một bảng master
    df = pd.merge(df_price[['Date', 'Close']], df_iv[['Date', 'KCH26']], on='Date', how='left')
    df = pd.merge(df, df_stock[['Date', 'Bags']], left_on='Date', right_on='Date', how='left')
    df = pd.merge(df, df_cot[['Date', 'NonComm_Positions_Long_All']], on='Date', how='left')
    
    # Xử lý dữ liệu thiếu và sắp xếp
    df = df.ffill().bfill().sort_values('Date')
    return df

# ==========================================
# 3. THỰC THI PCA & KALMAN
# ==========================================
def run_pca_analysis():
    df = prepare_data()
    
    # Chọn các cột để đưa vào PCA (Càng nhiều dữ liệu đầu vào, PCA càng mạnh)
    # Chúng ta dùng: Giá, Biến động (IV), Tồn kho (Stock), Vị thế cá mập (CoT)
    features = ['Close', 'KCH26', 'Bags', 'NonComm_Positions_Long_All']
    x = df[features].values
    
    # BẮT BUỘC: Chuẩn hóa dữ liệu về cùng một thang đo (Z-score)
    # Vì Stock là hàng nghìn, IV là 0.x, nếu không chuẩn hóa PCA sẽ chạy sai.
    x_scaled = StandardScaler().fit_transform(x)
    
    # CHẠY PCA: Gom tất cả thành 1 thành phần chính (PC1)
    pca = PCA(n_components=1)
    df['Coffee_Index'] = pca.fit_transform(x_scaled)
    
    # DÙNG KALMAN: Làm mượt chỉ số PCA vừa tạo
    kf = SimpleKalman(q=0.05, r=5, initial_value=df['Coffee_Index'].iloc[0])
    df['Coffee_Index_Smooth'] = df['Coffee_Index'].apply(kf.update)

    # Giải thích tỷ trọng: PCA cho bạn biết biến nào quan trọng nhất
    weights = pd.Series(pca.components_[0], index=features)
    print("--- TỶ TRỌNG CẤU THÀNH CHỈ SỐ (PCA LOADINGS) ---")
    print(weights)
    print("-" * 40)

    # ==========================================
    # 4. VẼ BIỂU ĐỒ SO SÁNH
    # ==========================================
    fig, ax1 = plt.subplots(figsize=(15, 8))

    # Trục 1: Giá Cà phê
    color = 'tab:blue'
    ax1.set_xlabel('Ngày')
    ax1.set_ylabel('Giá Cà phê (Close)', color=color)
    ax1.plot(df['Date'], df['Close'], color=color, alpha=0.5, label='Giá thực tế')
    ax1.tick_params(axis='y', labelcolor=color)

    # Trục 2: Chỉ số tổng hợp (PCA Index)
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Chỉ số Sức khỏe Thị trường (PCA + Kalman)', color=color)
    ax2.plot(df['Date'], df['Coffee_Index_Smooth'], color=color, linewidth=2, label='Chỉ số PCA (Leading)')
    
    # Vẽ thêm vùng 0 để thấy sự phân kỳ
    ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    plt.title('Hệ thống Phân tích Đa biến: Giá vs. PCA Leading Indicator')
    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_pca_analysis()