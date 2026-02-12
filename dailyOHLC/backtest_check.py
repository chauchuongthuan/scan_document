import pandas as pd
import numpy as np

def scan_historical_signals(kc_daily_excel, iv_excel, cot_excel):
    # 1. Load và xử lý dữ liệu
    print("Đang đọc dữ liệu...")
    df_price = pd.read_excel(kc_daily_excel, parse_dates=['Date']).sort_values('Date')
    df_iv = pd.read_excel(iv_excel, parse_dates=['Date'])
    df_cot = pd.read_excel(cot_excel, parse_dates=['Report_Date_as_MM_DD_YYYY'])

    # Merge dữ liệu
    df = pd.merge(df_price, df_iv[['Date', 'KCH26']], on='Date', how='left')
    df_cot = df_cot.rename(columns={'Report_Date_as_MM_DD_YYYY': 'Date'})
    df = pd.merge(df, df_cot, on='Date', how='left')
    df = df.sort_values('Date').reset_index(drop=True)

    # Fill dữ liệu tuần xuống ngày
    cols_to_fill = ['Open_Interest_All', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All', 'KCH26']
    df[cols_to_fill] = df[cols_to_fill].ffill()

    # 2. TÍNH TOÁN CHỈ SỐ (LOGIC NÂNG CẤP)
    
    # A. COT Index (Dùng window nhỏ hơn nếu dữ liệu ít)
    df['Net_Pos'] = df['NonComm_Positions_Long_All'] - df['NonComm_Positions_Short_All']
    # Lưu ý: min_periods=1 để tính được ngay cả khi dữ liệu ít
    df['Net_Min'] = df['Net_Pos'].rolling(window=50, min_periods=1).min()
    df['Net_Max'] = df['Net_Pos'].rolling(window=50, min_periods=1).max()
    
    # Tránh lỗi chia cho 0
    df['COT_Index'] = 0.5 # Mặc định
    mask = (df['Net_Max'] - df['Net_Min']) != 0
    df.loc[mask, 'COT_Index'] = (df.loc[mask, 'Net_Pos'] - df.loc[mask, 'Net_Min']) / \
                                (df.loc[mask, 'Net_Max'] - df.loc[mask, 'Net_Min'])

    # B. Xu hướng giá (Price Trend)
    df['MA20'] = df['Close'].rolling(window=20).mean()

    # C. Xu hướng dòng tiền (OI Trend) - QUAN TRỌNG: Đã sửa logic
    # Thay vì soi từng ngày, ta so sánh OI với trung bình 20 ngày của chính nó
    df['OI_MA20'] = df['Open_Interest_All'].rolling(window=20).mean()
    
    # 3. TẠO TÍN HIỆU (Backtest Logic)
    df['Signal'] = "WAIT"
    
    # Điều kiện MUA: 
    # 1. Giá nằm trên MA20 (Xu hướng tăng)
    # 2. COT Index > 0.6 (Quỹ đang giữ Long nhiều)
    # 3. OI > OI_MA20 (Dòng tiền tổng thể đang vào)
    buy_cond = (df['Close'] > df['MA20']) & (df['COT_Index'] > 0.6) & (df['Open_Interest_All'] > df['OI_MA20'])
    
    # Điều kiện BÁN:
    # 1. Giá nằm dưới MA20
    # 2. COT Index < 0.4 (Quỹ đang giữ Short nhiều)
    # 3. OI > OI_MA20 (Dòng tiền tổng thể đang vào để đạp giá)
    sell_cond = (df['Close'] < df['MA20']) & (df['COT_Index'] < 0.4) & (df['Open_Interest_All'] > df['OI_MA20'])

    df.loc[buy_cond, 'Signal'] = "LONG"
    df.loc[sell_cond, 'Signal'] = "SHORT"

    # 4. IN KẾT QUẢ QUÉT LỊCH SỬ
    print("\n" + "="*50)
    print("BẢNG TỔNG HỢP CÁC ĐIỂM VÀO LỆNH TRONG QUÁ KHỨ")
    print("="*50)
    
    # Lọc ra những ngày có lệnh (Khác WAIT)
    signals = df[df['Signal'] != "WAIT"]
    
    if signals.empty:
        print("Vẫn chưa tìm thấy tín hiệu nào. Dữ liệu có thể quá ngắn hoặc thị trường đang Sideway biên độ hẹp.")
        # Debug: In ra vài dòng dữ liệu thô để kiểm tra
        print("\n--- DEBUG: 5 Dòng dữ liệu tính toán gần nhất ---")
        print(df[['Date', 'Close', 'MA20', 'COT_Index', 'Open_Interest_All', 'OI_MA20']].tail(5))
    else:
        print(f"Tìm thấy {len(signals)} điểm vào lệnh:\n")
        # In đẹp
        print(f"{'Ngày':<12} | {'Tín hiệu':<6} | {'Giá':<8} | {'COT Idx':<8} | {'OI Trend'}")
        print("-" * 60)
        for index, row in signals.iterrows():
            oi_status = "Tăng" if row['Open_Interest_All'] > row['OI_MA20'] else "Giảm"
            print(f"{row['Date'].date()} | {row['Signal']:<6} | {row['Close']:<8} | {row['COT_Index']:.2f}     | {oi_status}")

    return df

# Chạy thử
# Bạn thay tên file chính xác vào đây
scan_historical_signals('C:/Users/COMPUTER/Desktop/KC_DAILY.xlsx', 'C:/Users/COMPUTER/Desktop/IMPLIED_VOLATILITY.xlsx', 'C:/Users/COMPUTER/Desktop/Tong_Hop_CoT_Coffee_C.xlsx')