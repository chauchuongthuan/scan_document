import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar
import warnings

# Tắt cảnh báo định dạng
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN FILE
# ==========================================
PATH_CONFIG = {
    'price': "C:/Users/COMPUTER/Desktop/KCU_DAILY.xlsx",
    'iv': "C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx",
    'stock': "C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx",
    'cot': "C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx",
    'sd': "C:/Users/COMPUTER/Desktop/Global S&D.xlsx"
}

us_cal = USFederalHolidayCalendar()
trading_days = CustomBusinessDay(calendar=us_cal)

# ==========================================
# 2. HÀM XỬ LÝ DỮ LIỆU AN TOÀN
# ==========================================
def get_clean_sd_value(df, keyword):
    """Trích xuất giá trị S&D và đảm bảo không trả về 0 nếu có dữ liệu"""
    try:
        # Tìm hàng chứa từ khóa (không phân biệt hoa thường, bỏ khoảng trắng)
        mask = df.iloc[:, 0].astype(str).str.contains(keyword, na=False, case=False)
        row = df[mask]
        
        if row.empty:
            print(f"⚠️ Cảnh báo: Không tìm thấy từ khóa '{keyword}'")
            return 0
        
        # Lấy tất cả giá trị từ cột thứ 2 trở đi, chuyển sang số
        values = pd.to_numeric(row.iloc[0, 2:], errors='coerce').dropna()
        
        if values.empty:
            return 0
        return float(values.iloc[-1])
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc giá trị '{keyword}': {e}")
        return 0

def apply_kalman_filter(data):
    if len(data) == 0: return data
    n_iter = len(data)
    sz = (n_iter,)
    xhat = np.zeros(sz); P = np.zeros(sz)
    xhatminus = np.zeros(sz); Pminus = np.zeros(sz); K = np.zeros(sz)
    Q = 1e-4; R = 0.01
    xhat[0] = data[0]; P[0] = 1.0
    for k in range(1, n_iter):
        xhatminus[k] = xhat[k-1]
        Pminus[k] = P[k-1] + Q
        K[k] = Pminus[k] / (Pminus[k] + R)
        xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
        P[k] = (1 - K[k]) * Pminus[k]
    return xhat

# ==========================================
# 3. HỆ THỐNG DỰ BÁO CHÍNH (V7)
# ==========================================
def run_market_forecast_system(entropy_today, vn_data={'R': 28, 'A': 1.6}, br_data={'R': 46.75, 'A': 24.95}, lookback=60):
    try:
        # --- LOAD DATA ---
        df_price = pd.read_excel(PATH_CONFIG['price'])
        df_iv = pd.read_excel(PATH_CONFIG['iv'])
        df_stock = pd.read_excel(PATH_CONFIG['stock'])
        df_cot = pd.read_excel(PATH_CONFIG['cot'])
        
        # --- XỬ LÝ S&D (Fix lỗi Division by Zero) ---
        df_prod = pd.read_excel(PATH_CONFIG['sd'], sheet_name='Production')
        df_cons = pd.read_excel(PATH_CONFIG['sd'], sheet_name='Consumption')
        
        # Sử dụng từ khóa rộng hơn để khớp với file của bạn
        world_prod = get_clean_sd_value(df_prod, "Total")
        world_cons = get_clean_sd_value(df_cons, "Total")
        
        vn_old = get_clean_sd_value(df_prod, "Viet Nam")
        br_old = get_clean_sd_value(df_prod, "Brazil")
        print("world_prod:::", world_prod)
        print("world_cons:::", world_cons)
        # Kiểm tra an toàn trước khi chia
        if world_cons == 0:
            print("❌ LỖI NGHIÊM TRỌNG: world_cons = 0. Kiểm tra lại sheet Consumption trong file S&D.")
            return

        adjusted_prod = world_prod - vn_old - br_old + (vn_data['R'] + vn_data['A']) + (br_data['R'] + br_data['A'])
        sd_ratio = adjusted_prod / world_cons

        # --- MERGE & CLEAN DATA ---
        df_price['Date'] = pd.to_datetime(df_price['Date'], dayfirst=True)
        df_iv['Date'] = pd.to_datetime(df_iv['Date'], dayfirst=True)
        df_stock['Date'] = pd.to_datetime(df_stock['Date'])
        df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

        df = df_price[['Date', 'Close']].copy()
        # Merge các file phụ vào file giá
        df = pd.merge_asof(df.sort_values('Date'), df_iv.sort_values('Date'), on='Date', direction='backward')
        df = pd.merge_asof(df, df_stock.sort_values('Date'), on='Date', direction='backward')
        df = pd.merge_asof(df, df_cot.sort_values('Date'), on='Date', direction='backward')

        # Điền dữ liệu và cắt lát theo lookback
        df = df.ffill().bfill().dropna()
        if len(df) > lookback:
            df = df.tail(lookback).reset_index(drop=True)

        # --- TÍNH TOÁN BIẾN SỐ ---
        df['COT_Signal'] = df['NonComm_Positions_Long_All'] - df['NonComm_Positions_Short_All']
        df['SD_Vector'] = sd_ratio
        df['Entropy'] = 0.5 

        # Kiểm tra tên cột IV trong file của bạn (KCH26 hoặc RMH26)
        iv_col = 'KCH26' if 'KCH26' in df.columns else df_iv.columns[1]
        stock_col = 'Bags' if 'Bags' in df.columns else df_stock.columns[1]

        features = ['Close', iv_col, stock_col, 'COT_Signal', 'SD_Vector', 'Entropy']
        
        # PCA & Kalman
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(df[features])
        pca = PCA(n_components=1)
        df['Internal_Vector'] = pca.fit_transform(scaled_features)
        df['Kalman_Signal'] = apply_kalman_filter(df['Internal_Vector'].values)

        # --- DỰ BÁO ---
        last_date = df['Date'].iloc[-1]
        forecast_date = last_date + trading_days
        
        y = df['Kalman_Signal'].tail(5).values
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        
        entropy_amplifier = 1 + (entropy_today - 0.5) * 2 
        adjusted_slope = slope * entropy_amplifier
        kalman_forecast = df['Kalman_Signal'].iloc[-1] + adjusted_slope

        # --- BIỂU ĐỒ ---
        fig, ax1 = plt.subplots(figsize=(14, 8))
        ax1.plot(df['Date'], df['Close'], color='#2c3e50', alpha=0.3, label='Giá Coffee (Thực tế)')
        ax1.set_ylabel('Price (Cent/lb)', fontweight='bold')
        
        ax2 = ax1.twinx()
        ax2.plot(df['Date'], df['Kalman_Signal'], color='#2980b9', linewidth=2, label='Nội tại (Quá khứ)')
        ax2.scatter(forecast_date, kalman_forecast, color='red', s=100, zorder=5)
        ax2.plot([last_date, forecast_date], [df['Kalman_Signal'].iloc[-1], kalman_forecast], 'r--')

        plt.title(f"DỰ BÁO PHIÊN {forecast_date.strftime('%d/%m/%Y')}\nS&D Ratio: {sd_ratio:.4f}")
        plt.show()

        print(f"✅ Hoàn tất! S&D Ratio: {sd_ratio:.4f}")
        print(f"Dự báo: {'LÊN' if adjusted_slope > 0 else 'XUỐNG'}")

    except Exception as e:
        print(f"❌ Lỗi hệ thống: {e}")
        import traceback
        traceback.print_exc()

# --- CHẠY ---
run_market_forecast_system(entropy_today=0.48)