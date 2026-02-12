import pandas as pd
import numpy as np

def coffee_short_term_strategy(kc_daily_excel, iv_excel, cot_excel):
    # 1. ĐỌC VÀ XỬ LÝ DỮ LIỆU
    df_price = pd.read_excel(kc_daily_excel, parse_dates=['Date']).sort_values('Date')
    df_iv = pd.read_excel(iv_excel, parse_dates=['Date'])
    df_cot = pd.read_excel(cot_excel, parse_dates=['Report_Date_as_MM_DD_YYYY'])

    # Merge Price và IV
    df = pd.merge(df_price, df_iv[['Date', 'KCH26']], on='Date', how='left')
    
    # Merge COT (Vẫn giữ nguyên dữ liệu tuần, không nội suy)
    df_cot = df_cot.rename(columns={'Report_Date_as_MM_DD_YYYY': 'Date'})
    df = pd.merge(df, df_cot, on='Date', how='left')
    df = df.sort_values('Date').reset_index(drop=True)

    # Fill dữ liệu COT (Giữ nguyên giá trị của tuần trước cho đến khi có số mới)
    cols_to_fill = ['Open_Interest_All', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All', 'KCH26']
    df[cols_to_fill] = df[cols_to_fill].ffill()

    # 2. TÍNH TOÁN CHỈ SỐ
    # A. COT Index (Chỉ dùng để xác định Xu hướng chủ đạo - BIAS)
    df['Net_Pos'] = df['NonComm_Positions_Long_All'] - df['NonComm_Positions_Short_All']
    rolling_min = df['Net_Pos'].rolling(window=52, min_periods=1).min() # Dùng 52 tuần (1 năm)
    rolling_max = df['Net_Pos'].rolling(window=52, min_periods=1).max()
    df['COT_Bias'] = (df['Net_Pos'] - rolling_min) / (rolling_max - rolling_min)

    # B. Daily Signals (Tín hiệu hàng ngày)
    # 1. Dòng tiền nóng (Daily OI Change)
    df['Daily_OI_Change'] = df['Open_Interest_All'].diff()
    
    # 2. Áp lực giá ngắn hạn (Giá đóng cửa so với giá mở cửa)
    df['Daily_Pressure'] = df['Close'] - df['Open']
    
    # 3. Biến động (IV)
    df['IV_MA5'] = df['KCH26'].rolling(5).mean() # IV trung bình 5 ngày

    # 3. LOGIC RA LỆNH NGẮN HẠN (1-3 NGÀY)
    df['Signal'] = "WAIT"

    # --- KỊCH BẢN MUA (LONG) ---
    # Điều kiện 1 (Bias): Quỹ lớn đang gom hàng (COT > 0.5)
    # Điều kiện 2 (Money): Hôm qua tiền vào mạnh (OI tăng)
    # Điều kiện 3 (Price): Giá đóng cửa cao hơn mở cửa (Nến xanh)
    long_condition = (
        (df['COT_Bias'] > 0.5) & 
        (df['Daily_OI_Change'] > 0) & 
        (df['Daily_Pressure'] > 0)
    )

    # --- KỊCH BẢN BÁN (SHORT) ---
    # Điều kiện 1 (Bias): Quỹ lớn đang xả hàng (COT < 0.5)
    # Điều kiện 2 (Money): Hôm qua tiền vào mạnh (để Short)
    # Điều kiện 3 (Price): Giá đóng cửa thấp hơn mở cửa (Nến đỏ)
    short_condition = (
        (df['COT_Bias'] < 0.5) & 
        (df['Daily_OI_Change'] > 0) & 
        (df['Daily_Pressure'] < 0)
    )

    df.loc[long_condition, 'Signal'] = "BUY_NOW"
    df.loc[short_condition, 'Signal'] = "SELL_NOW"

    # 4. IN KẾT QUẢ CHO NGÀY HÔM NAY (23/01/2026)
    last_row = df.iloc[-1]
    
    print(f"--- CHIẾN LƯỢC NGẮN HẠN (DAILY TRADING) NGÀY {last_row['Date'].date()} ---")
    print(f"1. Xu hướng Chủ đạo (COT Bias): {last_row['COT_Bias']:.2f} ({'PHE MUA' if last_row['COT_Bias']>0.5 else 'PHE BÁN'})")
    print(f"2. Dòng tiền hôm qua (Daily OI): {last_row['Daily_OI_Change']:+} Hợp đồng")
    print(f"3. Hành động giá (Close-Open): {last_row['Daily_Pressure']}")
    
    print("-" * 30)
    if last_row['Signal'] == "BUY_NOW":
        print("KHUYẾN NGHỊ: MUA NGAY (Day Trade)")
        print("Lý do: Quỹ hỗ trợ + Tiền vào + Nến xanh")
    elif last_row['Signal'] == "SELL_NOW":
        print("KHUYẾN NGHỊ: BÁN NGAY (Day Trade)")
        print("Lý do: Quỹ xả + Tiền vào + Nến đỏ")
    else:
        print("KHUYẾN NGHỊ: ĐỨNG NGOÀI (WAIT)")
        print("Lý do: Tín hiệu giá và dòng tiền không đồng thuận với Quỹ lớn.")

    return df

result = coffee_short_term_strategy('C:/Users/COMPUTER/Desktop/KC_DAILY.xlsx', 'C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx', 'C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx')