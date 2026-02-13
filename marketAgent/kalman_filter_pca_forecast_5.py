import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar
import warnings

# Tắt các cảnh báo định dạng từ openpyxl
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN FILE (Sửa lại nếu cần)
# ==========================================
PATH_CONFIG = {
    'price': "C:/Users/COMPUTER/Desktop/KCK_DAILY.xlsx",
    'iv': "C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx",
    'stock': "C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx",
    'cot': "C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx",
    'sd': "C:/Users/COMPUTER/Desktop/Global S&D.xlsx"
}

us_cal = USFederalHolidayCalendar()
trading_days = CustomBusinessDay(calendar=us_cal)

# ==========================================
# 2. HÀM TRÍCH XUẤT DỮ LIỆU S&D
# ==========================================
def get_clean_sd_value(df, keyword):
    """
    Tìm kiếm hàng chứa từ khóa và lấy giá trị số mới nhất (năm 2024/25).
    Xử lý được việc file có nhiều bảng phụ nằm bên phải.
    """
    # Tìm các hàng mà cột đầu tiên khớp với keyword
    if keyword.lower() == "total":
        # Khớp chính xác chữ "Total" để tránh dòng "Total production..."
        mask = df.iloc[:, 0].astype(str).str.strip().str.fullmatch("Total", case=False)
    else:
        mask = df.iloc[:, 0].astype(str).str.contains(keyword, na=False, case=False)
    
    if not mask.any():
        return 0
    
    # Duyệt qua các hàng khớp (lấy hàng đầu tiên có dữ liệu số)
    matched_rows = df[mask]
    for i in range(len(matched_rows)):
        row_data = matched_rows.iloc[i]
        # Dữ liệu năm thường nằm từ cột index 2 đến 37 (1990 - 2025)
        # Chuyển sang số, bỏ qua NaN
        vals = pd.to_numeric(row_data.iloc[2:38], errors='coerce').dropna()
        if not vals.empty:
            return vals.iloc[-1] # Trả về năm gần nhất có dữ liệu
    return 0

# ==========================================
# 3. HỆ THỐNG DỰ BÁO CHÍNH
# ==========================================
def run_market_forecast_system(entropy_today, vn_data={'R': 28, 'A': 1.6}, br_data={'R': 46.75, 'A': 24.95}, lookback=60):
    try:
        print("--- ĐANG XỬ LÝ DỮ LIỆU ---")
        
        # A. LOAD DỮ LIỆU CƠ BẢN
        df_price = pd.read_excel(PATH_CONFIG['price'])
        df_iv = pd.read_excel(PATH_CONFIG['iv'])
        df_stock = pd.read_excel(PATH_CONFIG['stock'])
        df_cot = pd.read_excel(PATH_CONFIG['cot'])
        
        # Load S&D (Đọc raw để tìm hàng/cột thủ công)
        df_prod_raw = pd.read_excel(PATH_CONFIG['sd'], sheet_name='Production', header=None)
        df_cons_raw = pd.read_excel(PATH_CONFIG['sd'], sheet_name='Consumption', header=None)

        # B. TÍNH TOÁN VECTOR S&D (Supply & Demand)
        # Lấy số liệu từ file (đơn vị nghìn bao)
        world_prod_file = get_clean_sd_value(df_prod_raw, "Total")
        vn_prod_file = get_clean_sd_value(df_prod_raw, "Viet Nam")
        br_prod_file = get_clean_sd_value(df_prod_raw, "Brazil")
        world_cons_file = get_clean_sd_value(df_cons_raw, "Total")

        # Tính toán sản lượng thực tế dựa trên số liệu bạn cung cấp (Triệu bao -> Nghìn bao)
        user_vn_total = (vn_data['R'] + vn_data['A']) * 1000
        user_br_total = (br_data['R'] + br_data['A']) * 1000
        
        # Điều chỉnh: Thế giới - (VN_cũ + BR_cũ) + (VN_mới + BR_mới)
        adj_production = world_prod_file - vn_prod_file - br_prod_file + user_vn_total + user_br_total
        sd_ratio = adj_production / (world_cons_file if world_cons_file != 0 else 1)

        # C. MERGE VÀ XỬ LÝ CHUỖI THỜI GIAN
        df_price['Date'] = pd.to_datetime(df_price['Date'], dayfirst=True)
        df_iv['Date'] = pd.to_datetime(df_iv['Date'], dayfirst=True)
        df_stock['Date'] = pd.to_datetime(df_stock['Date'])
        df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

        df = pd.merge(df_price[['Date', 'Close', 'Volatility Close']], df_iv[['Date', 'KCH26']], on='Date', how='left')
        df = pd.merge(df, df_stock[['Date', 'Bags']], on='Date', how='left')
        df_cot['Net_NonComm'] = df_cot['NonComm_Positions_Long_All'] - df_cot['NonComm_Positions_Short_All']
        df = pd.merge(df, df_cot[['Date', 'Net_NonComm']], on='Date', how='left')
        
        df = df.sort_values('Date').ffill().dropna()
        analysis_df = df.tail(lookback).copy()

        # D. XỬ LÝ ENTROPY DYNAMIC (Không dùng 0.5 cố định)
        # Sử dụng Volatility để mô phỏng "độ hỗn loạn" lịch sử (thay vì để phẳng 0.5)
        v_min, v_max = analysis_df['Volatility Close'].min(), analysis_df['Volatility Close'].max()
        if v_max != v_min:
            # Chuyển đổi Volatility sang thang Entropy (0.2 - 0.8) để PCA có dữ liệu đầu vào
            analysis_df['Entropy'] = 0.2 + (analysis_df['Volatility Close'] - v_min) / (v_max - v_min) * 0.6
        else:
            analysis_df['Entropy'] = 0.5
            
        # Gán giá trị Entropy hôm nay bạn nhập từ tóm tắt thị trường
        analysis_df.iloc[-1, analysis_df.columns.get_loc('Entropy')] = entropy_today
        analysis_df['SD_Vector'] = sd_ratio

        # E. PHÂN TÍCH PCA (Principal Component Analysis)
        features = ['Close', 'Volatility Close', 'KCH26', 'Bags', 'Net_NonComm', 'Entropy', 'SD_Vector']
        scaler = StandardScaler()
        pca = PCA(n_components=1)
        
        scaled_data = scaler.fit_transform(analysis_df[features])
        analysis_df['PCA_Signal'] = pca.fit_transform(scaled_data)

        # F. LỌC NHIỄU KALMAN
        q, r, p = 0.01, 0.1, 1.0
        x = analysis_df['PCA_Signal'].iloc[0]
        kalman_list = []
        for val in analysis_df['PCA_Signal']:
            p += q
            kg = p / (p + r)
            x = x + kg * (val - x)
            p = (1 - kg) * p
            kalman_list.append(x)
        analysis_df['Kalman_Signal'] = kalman_list

        # G. DỰ BÁO PHIÊN TIẾP THEO
        last_date = analysis_df['Date'].max()
        forecast_date = last_date + trading_days
        
        y_recent = analysis_df['Kalman_Signal'].tail(10).values
        slope, _ = np.polyfit(np.arange(10), y_recent, 1)
        kalman_forecast = analysis_df['Kalman_Signal'].iloc[-1] + (slope * 1.5)

        # H. TRỰC QUAN HÓA
        fig, ax1 = plt.subplots(figsize=(15, 8))
        
        # Vẽ giá thực tế
        ax1.plot(analysis_df['Date'], analysis_df['Close'], color='#bdc3c7', alpha=0.5, label='Giá Close (Thực tế)')
        ax1.set_ylabel('Coffee Price (US cents/lb)', fontweight='bold')
        
        # Vẽ Vector nội tại (Kalman)
        ax2 = ax1.twinx()
        ax2.plot(analysis_df['Date'], analysis_df['Kalman_Signal'], color='#2980b9', linewidth=2.5, label='Market Internal Vector')
        
        # Vẽ điểm dự báo
        ax2.scatter(forecast_date, kalman_forecast, color='red', s=120, edgecolors='white', zorder=5)
        ax2.plot([last_date, forecast_date], [analysis_df['Kalman_Signal'].iloc[-1], kalman_forecast], 
                 color='red', linestyle='--', linewidth=2, label='Dự báo phiên kế tiếp')

        plt.title(f"HỆ THỐNG DỰ BÁO ĐA VECTOR (PRICE - COT - S&D - ENTROPY)\nPhiên: {forecast_date.strftime('%d/%m/%Y')} | S&D Ratio: {sd_ratio:.4f}", fontsize=14)
        ax1.grid(True, alpha=0.2)
        
        # Legend
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, loc='upper left')

        # In kết quả ra console
        print(f"\n--- KẾT QUẢ PHÂN TÍCH ---")
        print(f"S&D Ratio: {sd_ratio:.4f} ({'Dư cung/Bearish' if sd_ratio > 1 else 'Thiếu hụt/Bullish'})")
        print(f"Entropy hôm nay: {entropy_today}")
        print(f"Tín hiệu Vector: {'TĂNG (UP)' if slope > 0 else 'GIẢM (DOWN)'}")
        print(f"Dự báo cho ngày: {forecast_date.strftime('%d/%m/%Y')}")
        
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        import traceback
        traceback.print_exc()

# --- CHẠY THỬ NGHIỆM ---
# Nhập entropy hôm nay (ví dụ 0.7) dựa trên tóm tắt thị trường bạn đọc được
run_market_forecast_system(entropy_today=0.9)