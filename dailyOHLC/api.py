import pandas as pd
import numpy as np

def coffee_trading_system_2026(kc_daily_path, iv_path, cot_path):
    # 1. Load dữ liệu
    df_price = pd.read_excel(kc_daily_path, parse_dates=['Date']).sort_values('Date')
    df_iv = pd.read_excel(iv_path, parse_dates=['Date'])[['Date', 'KCH26']]
    df_iv.columns = ['Date', 'IV']
    
    df_cot = pd.read_excel(cot_path, parse_dates=['Report_Date_as_MM_DD_YYYY'])
    # Lấy các cột quan trọng từ file COT của bạn
    df_cot = df_cot[['Report_Date_as_MM_DD_YYYY', 'Open_Interest_All', 
                    'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All']]
    df_cot.columns = ['Date', 'OI', 'NC_Long', 'NC_Short']

    # 2. Hợp nhất dữ liệu (Xử lý lệch ngày)
    # Ta dùng merge 'outer' để không mất ngày nào, sau đó sort và fill
    df = pd.merge(df_price, df_iv, on='Date', how='left')
    df = pd.merge(df, df_cot, on='Date', how='left')
    df = df.sort_values('Date').reset_index(drop=True)
    # Điền dữ liệu COT và IV cho các ngày daily (Forward fill)
    df[['OI', 'NC_Long', 'NC_Short', 'IV']] = df[['OI', 'NC_Long', 'NC_Short', 'IV']].ffill()

    # 3. Tính toán các chỉ số theo 151 Strategies
    # Vị thế ròng và COT Index (Chương 19)
    df['Net_Pos'] = df['NC_Long'] - df['NC_Short']
    df['COT_Index'] = (df['Net_Pos'] - df['Net_Pos'].rolling(window=250, min_periods=1).min()) / \
                  (df['Net_Pos'].rolling(window=250, min_periods=1).max() - df['Net_Pos'].rolling(window=250, min_periods=1).min())
    # Momentum (Chương 10.1)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Price_Momentum'] = np.where(df['Close'] > df['MA20'], 1, -1)
    
    # Tính biến động OI
    df['OI_Diff'] = df['OI'].diff()

    # 4. Xác định Tín hiệu (Dựa trên dữ liệu đã có đến hôm qua)
    # Signal = 1 (Long), -1 (Short), 0 (Cash)
    df['Signal'] = 0
    
    # Điều kiện MUA: Momentum dương + Phe đầu cơ đang Long (Index > 0.5) + Tiền vào (OI tăng)
    buy_logic = (df['Price_Momentum'] == 1) & (df['COT_Index'] > 0.5) & (df['OI_Diff'] > 0)
    # Điều kiện BÁN: Momentum âm + Phe đầu cơ đang Short (Index < 0.5) + OI tăng (Short đuổi)
    sell_logic = (df['Price_Momentum'] == -1) & (df['COT_Index'] < 0.4) & (df['OI_Diff'] > 0)
    
    df.loc[buy_logic, 'Signal'] = 1
    df.loc[sell_logic, 'Signal'] = -1

    # 5. Kết quả cho ngày hôm nay (23/01/2026)
    # Chúng ta lấy hàng cuối cùng (ngày 22/01) để biết Action cho ngày 23/01
    last_row = df.iloc[-1]
    last_date = last_row['Date']
    
    print(f"--- PHÂN TÍCH DỮ LIỆU CUỐI PHIÊN NGÀY: {last_date.date()} ---")
    
    # Kiểm tra độ tươi của dữ liệu COT
    last_cot_update = df[df['NC_Long'].notnull()]['Date'].max()
    days_stale = (last_date - last_cot_update).days
    if days_stale > 10:
        print(f"⚠️ CẢNH BÁO: Dữ liệu COT đã cũ ({days_stale} ngày). Tín hiệu có thể kém chính xác.")

    print(f"1. Xu hướng giá (MA20): {'TĂNG' if last_row['Price_Momentum'] == 1 else 'GIẢM'}")
    print(f"2. Tâm lý quỹ (COT Index): {last_row['COT_Index']:.2f}")
    print(f"3. Dòng tiền (OI): {'ĐANG VÀO' if last_row['OI_Diff'] > 0 else 'ĐANG RÚT RA'}")
    print(f"4. Tín hiệu: {last_row['Signal']}")
    recommendation = "ĐỨNG NGOÀI"
    if last_row['Signal'] == 1: recommendation = "MỞ LỆNH MUA (LONG)"
    elif last_row['Signal'] == -1: recommendation = "MỞ LỆNH BÁN (SHORT)"
    
    print(f"\n==> HÀNH ĐỘNG CHO NGÀY TIẾP THEO: {recommendation}")
    
    return df

# Sử dụng:
result = coffee_trading_system_2026('C:/Users/COMPUTER/Desktop/KC_DAILY.xlsx', 'C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx', 'C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx')