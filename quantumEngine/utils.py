import pandas as pd
from .models import QuantumEngine
import io

def import_historical_data(rc_stock_file, kc_stock_file, rc_daily_file, kc_daily_file):
    """
    Hàm nhập liệu tổng hợp. 
    Lưu ý: Các file upload lên được giả định là file CSV hoặc Excel convert sang DataFrame.
    """
    
    # 1. Đọc RC Stock (Robusta Inventory)
    # File mẫu: DATE, LOTS WITH VAL CERT
    df_rc_stock = pd.read_csv(rc_stock_file)
    df_rc_stock['DATE'] = pd.to_datetime(df_rc_stock['DATE'], dayfirst=True)
    df_rc_stock.set_index('DATE', inplace=True)

    # 2. Đọc KC Stock (Arabica Inventory)
    # File mẫu: Date, Bags
    df_kc_stock = pd.read_csv(kc_stock_file)
    df_kc_stock['Date'] = pd.to_datetime(df_kc_stock['Date'], dayfirst=True)
    df_kc_stock.set_index('Date', inplace=True)

    # 3. Đọc RC Daily (OHLC)
    df_rc_daily = pd.read_csv(rc_daily_file)
    df_rc_daily['Date'] = pd.to_datetime(df_rc_daily['Date'])
    df_rc_daily.set_index('Date', inplace=True)

    # 4. Đọc KC Daily (OHLC)
    df_kc_daily = pd.read_csv(kc_daily_file)
    df_kc_daily['Date'] = pd.to_datetime(df_kc_daily['Date'])
    df_kc_daily.set_index('Date', inplace=True)

    # 5. Merge dữ liệu (Outer join để lấy tất cả các ngày)
    all_dates = sorted(list(set(df_rc_daily.index) | set(df_kc_daily.index) | set(df_rc_stock.index)))

    count = 0
    for date in all_dates:
        # Lấy dữ liệu hoặc None nếu không có (Handle missing data)
        rc_ohlc = df_rc_daily.loc[date] if date in df_rc_daily.index else None
        kc_ohlc = df_kc_daily.loc[date] if date in df_kc_daily.index else None
        
        # Tồn kho: Nếu ngày này không có, lấy ngày gần nhất trước đó (Forward Fill logic)
        # Nhưng ở bước import này ta chỉ lưu cái gì có thực. Logic fill sẽ xử lý lúc tính toán.
        rc_inv = df_rc_stock.loc[date]['LOTS WITH VAL CERT'] if date in df_rc_stock.index else None
        kc_inv = df_kc_stock.loc[date]['Bags'] if date in df_kc_stock.index else None
        
        # Lưu vào DB
        obj, created = QuantumEngine.objects.update_or_create(
            date=date.date(),
            defaults={
                'rc_open': rc_ohlc['Open'] if rc_ohlc is not None else None,
                'rc_high': rc_ohlc['High'] if rc_ohlc is not None else None,
                'rc_low': rc_ohlc['Low'] if rc_ohlc is not None else None,
                'rc_close': rc_ohlc['Close'] if rc_ohlc is not None else None,
                'kc_open': kc_ohlc['Open'] if kc_ohlc is not None else None,
                'kc_high': kc_ohlc['High'] if kc_ohlc is not None else None,
                'kc_low': kc_ohlc['Low'] if kc_ohlc is not None else None,
                'kc_close': kc_ohlc['Close'] if kc_ohlc is not None else None,
                'rc_inventory': rc_inv,
                'kc_inventory': kc_inv,
            }
        )
        if created: count += 1
    
    return f"Đã cập nhật dữ liệu cho {count} ngày mới."