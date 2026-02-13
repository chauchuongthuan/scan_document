import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
us_cal = USFederalHolidayCalendar()
trading_days = CustomBusinessDay(calendar=us_cal)

path_price = "C:/Users/COMPUTER/Desktop/KCK_DAILY.xlsx"
path_iv = "C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx"
path_stock = "C:/Users/COMPUTER/Desktop/ice_kc_stock_data_export_full.xlsx"
path_cot = "C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx"

def run_market_forecast_system(entropy_today, lookback=60):
    try:
        # Load dữ liệu (Sử dụng đúng tên file bạn cung cấp)
        df_price = pd.read_excel(path_price)
        df_iv = pd.read_excel(path_iv)
        df_stock = pd.read_excel(path_stock)
        df_cot = pd.read_excel(path_cot)

        # Xử lý Date
        df_price['Date'] = pd.to_datetime(df_price['Date'])
        df_iv['Date'] = pd.to_datetime(df_iv['Date'])
        df_stock['Date'] = pd.to_datetime(df_stock['Date'])
        df_cot['Date'] = pd.to_datetime(df_cot['Report_Date_as_MM_DD_YYYY'])

        # Merge & Clean
        df = pd.merge(df_price[['Date', 'Close', 'Volatility Close']], df_iv[['Date', 'KCH26']], on='Date', how='left')
        df = pd.merge(df, df_stock[['Date', 'Bags']], on='Date', how='left')
        df_cot['Net_NonComm'] = df_cot['NonComm_Positions_Long_All'] - df_cot['NonComm_Positions_Short_All']
        df = pd.merge(df, df_cot[['Date', 'Net_NonComm']], on='Date', how='left')
        df = df.sort_values('Date').fillna(method='ffill').dropna()

        # Dữ liệu phân tích
        analysis_df = df.tail(lookback).copy()
        analysis_df.loc[analysis_df.index[-1], 'Entropy'] = entropy_today # Gán entropy phiên cuối
        analysis_df['Entropy'] = analysis_df['Entropy'].fillna(0.5)

        # PCA & Kalman
        features = ['Close', 'Volatility Close', 'KCH26', 'Bags', 'Net_NonComm', 'Entropy']
        scaler = StandardScaler()
        pca = PCA(n_components=1)
        
        scaled = scaler.fit_transform(analysis_df[features])
        analysis_df['PCA_Signal'] = pca.fit_transform(scaled)

        # Kalman Filter
        q, r = 0.01, 0.1
        p, x = 1.0, analysis_df['PCA_Signal'].iloc[0]
        kalman_list = []
        for val in analysis_df['PCA_Signal']:
            p += q
            kg = p / (p + r)
            x = x + kg * (val - x)
            p = (1 - kg) * p
            kalman_list.append(x)
        analysis_df['Kalman_Signal'] = kalman_list

        # --- DỰ BÁO TƯƠNG LAI (EXTRAPOLATION) ---
        last_date = analysis_df['Date'].max()
        forecast_date = last_date + trading_days
        
        # Tính Slope 10 phiên gần nhất để dự báo
        y_recent = analysis_df['Kalman_Signal'].tail(10).values
        x_recent = np.arange(10)
        slope, intercept = np.polyfit(x_recent, y_recent, 1)
        
        # Giá trị Kalman dự báo cho phiên tới
        kalman_forecast = slope * 10 + intercept 

        # ==========================================
        # 2. VẼ BIỂU ĐỒ CÓ PHẦN DỰ BÁO
        # ==========================================
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # Trục trái: Giá thực tế (Dừng ở hiện tại)
        ax1.plot(analysis_df['Date'], analysis_df['Close'], color='black', alpha=0.8, label='Giá Close (Thực tế)')
        ax1.set_ylabel('Price', fontweight='bold')
        
        # Trục phải: Kalman Signal
        ax2 = ax1.twinx()
        # 1. Vẽ đường quá khứ (Solid line)
        ax2.plot(analysis_df['Date'], analysis_df['Kalman_Signal'], color='blue', linewidth=2, label='Nội tại (Quá khứ)')
        
        # 2. Vẽ đường dự báo (Dashed line nối từ phiên cuối đến phiên tới)
        future_dates = [last_date, forecast_date]
        future_values = [analysis_df['Kalman_Signal'].iloc[-1], kalman_forecast]
        ax2.plot(future_dates, future_values, color='red', linestyle='--', linewidth=2, marker='o', label='Dự báo phiên tới')

        # Định dạng biểu đồ
        plt.title(f"XU HƯỚNG NỘI TẠI & DỰ BÁO PHIÊN {forecast_date.strftime('%d/%m/%Y')}", fontsize=14)
        ax1.grid(True, alpha=0.2)
        
        # Legend gom cả 2 trục
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        print(f"Dự báo Kalman cho ngày {forecast_date.date()}: {kalman_forecast:.4f}")
        plt.show()

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

# Chạy lệnh
run_market_forecast_system(entropy_today=0.3)