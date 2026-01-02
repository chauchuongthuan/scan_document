import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def fetch_historical_data(target_date):
    """
    Lấy dữ liệu phiên gần nhất có sẵn (<= target_date - 1)
    """
    # Đường dẫn file (Bạn hãy đảm bảo các file này nằm đúng vị trí)
    base_path = 'media/data_quantum_v2/'
    files = {
        'rc_daily': os.path.join(base_path, 'RC_DAILY.csv'),
        'kc_daily': os.path.join(base_path, 'KC_DAILY.csv'),
        'rc_stock': os.path.join(base_path, 'RC_STOCK.csv'),
        'kc_stock': os.path.join(base_path, 'KC_STOCK.csv'),
        'iv': os.path.join(base_path, 'IV.csv')
    }

    results = {'RC': {}, 'KC': {}}

    try:
        # 1. Đọc dữ liệu và chuyển đổi cột ngày sang kiểu dữ liệu DateTime để dễ so sánh
        # Dùng dayfirst=True vì format của bạn là DD/MM/YYYY
        rc_df = pd.read_csv(files['rc_daily'])
        rc_df['Date'] = pd.to_datetime(rc_df['Date'], dayfirst=True)

        rc_stock_df = pd.read_csv(files['rc_stock'])
        rc_stock_df['DATE'] = pd.to_datetime(rc_stock_df['DATE'], dayfirst=True)

        kc_df = pd.read_csv(files['kc_daily'])
        kc_df['Date'] = pd.to_datetime(kc_df['Date'], dayfirst=True)

        kc_stock_df = pd.read_csv(files['kc_stock'])
        kc_stock_df['Date'] = pd.to_datetime(kc_stock_df['Date'], dayfirst=True)

        iv_df = pd.read_csv(files['iv'])
        iv_df['Date'] = pd.to_datetime(iv_df['Date'], dayfirst=True)

        # Chuyển target_date sang datetime để so sánh
        target_dt = pd.to_datetime(target_date)

        # 2. Tìm dòng dữ liệu gần nhất TRƯỚC ngày target_date
        # Thay vì tìm đúng ngày T-1, ta lấy tất cả ngày < T và chọn dòng cuối cùng
        rc_hist = rc_df[rc_df['Date'] < target_dt]
        rc_stock_hist = rc_stock_df[rc_stock_df['DATE'] < target_dt]
        kc_hist = kc_df[kc_df['Date'] < target_dt]
        kc_stock_hist = kc_stock_df[kc_stock_df['Date'] < target_dt]
        iv_hist = iv_df[iv_df['Date'] < target_dt]

        if rc_hist.empty or iv_hist.empty:
            print(f"Không có dữ liệu lịch sử trước ngày {target_date}")
            return None

        # Lấy dòng cuối cùng có sẵn
        rc_row = rc_hist.iloc[-1]
        rc_stock_row = rc_stock_hist.iloc[-1]
        kc_row = kc_hist.iloc[-1]
        kc_stock_row = kc_stock_hist.iloc[-1]
        iv_row = iv_hist.iloc[-1]

        # 3. Trích xuất giá trị và xử lý dấu % ở cột IV
        def clean_iv(value):
            if isinstance(value, str):
                return float(value.replace('%', '')) / 100
            return float(value)

        results['RC']['close'] = float(rc_row['Close'])
        results['RC']['stock'] = float(rc_stock_row['LOTS WITH VAL CERT'])
        results['RC']['iv'] = clean_iv(iv_row['RMH26'])

        results['KC']['close'] = float(kc_row['Close'])
        results['KC']['stock'] = float(kc_stock_row['Bags'])
        results['KC']['iv'] = clean_iv(iv_row['KCH26'])
        
        print(f"Đã lấy dữ liệu phiên gần nhất ngày: {rc_row['Date'].strftime('%d/%m/%Y')}")

    except Exception as e:
        print(f"Lỗi xử lý dữ liệu: {str(e)}")
        return None
        
    return results