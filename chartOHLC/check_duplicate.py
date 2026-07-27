import pandas as pd
from datetime import datetime

def process_chart_data_kc(file_path):
    # Lưu ý: Cần kiểm tra định dạng ngày tháng trong file thực tế
    df = pd.read_excel(file_path)
    
    # Chuyển đổi cột Timestamp sang định dạng datetime để tính toán
    # Thử các format phổ biến trong file tài chính
    df['Timestamp_dt'] = pd.to_datetime(df['Timestamp'], dayfirst=True)

    # --- PHẦN 1: TÌM CÁC DÒNG TRÙNG TIMESTAMP NHƯNG KHÁC SYMBOL ---
    # Tìm các timestamp có nhiều hơn 1 symbol khác nhau
    duplicates_mask = df.groupby('Timestamp')['Symbol'].transform('nunique') > 1
    df_check = df[duplicates_mask][['Symbol', 'Timestamp']].copy()
    
    # Xuất file check.xlsx
    check_filename = 'KC_check.xlsx'
    df_check.to_excel(check_filename, index=False)

    # --- PHẦN 2: XỬ LÝ AFTER_CHECK THEO QUY TẮC ƯU TIÊN ---
    
    def get_priority(row):
        ts = row['Timestamp_dt']
        symbol = row['Symbol']
        
        # Mốc 1: Đến ngày 11/02/2026 ưu tiên KCH2026
        limit1 = datetime(2026, 2, 11, 23, 59, 59)
        # Mốc 2: Từ sau đó đến ngày 10/04/2026 ưu tiên KCK2026
        limit2 = datetime(2026, 4, 10, 23, 59, 59)
        # Mốc 3: Còn lại đến 16/04/2026 ưu tiên KCN2026
        
        if ts <= limit1:
            return 0 if symbol == 'KCH2026' else 1
        elif ts <= limit2:
            return 0 if symbol == 'KCK2026' else 1
        else:
            return 0 if symbol == 'KCN2026' else 1

    # Tạo cột phụ để đánh dấu mức độ ưu tiên (0 là ưu tiên cao nhất)
    df['Priority'] = df.apply(get_priority, axis=1)

    # Sắp xếp theo Timestamp và sau đó là Priority
    df_sorted = df.sort_values(by=['Timestamp_dt', 'Priority'])

    # Xóa trùng: Chỉ giữ lại hàng đầu tiên cho mỗi Timestamp (hàng có Priority = 0 sẽ được giữ lại)
    df_after = df_sorted.drop_duplicates(subset=['Timestamp'], keep='first')

    # Loại bỏ các cột phụ trước khi lưu
    final_columns = ['Symbol', 'Timestamp', 'Open', 'High', 'Low', 'Close']
    df_after = df_after[final_columns]

    # Xuất file
    after_check_filename = 'KC_minute_history.xlsx'
    df_after.to_excel(after_check_filename, index=False)

    return check_filename, after_check_filename

def process_chart_data_rc(file_path):
    # Lưu ý: Cần kiểm tra định dạng ngày tháng trong file thực tế
    df = pd.read_excel(file_path)
    
    # Chuyển đổi cột Timestamp sang định dạng datetime để tính toán
    # Thử các format phổ biến trong file tài chính
    df['Timestamp_dt'] = pd.to_datetime(df['Timestamp'], dayfirst=True)

    # --- PHẦN 1: TÌM CÁC DÒNG TRÙNG TIMESTAMP NHƯNG KHÁC SYMBOL ---
    # Tìm các timestamp có nhiều hơn 1 symbol khác nhau
    duplicates_mask = df.groupby('Timestamp')['Symbol'].transform('nunique') > 1
    df_check = df[duplicates_mask][['Symbol', 'Timestamp']].copy()
    
    # Xuất file check.xlsx
    check_filename = 'RC_check.xlsx'
    df_check.to_excel(check_filename, index=False)

    # --- PHẦN 2: XỬ LÝ AFTER_CHECK THEO QUY TẮC ƯU TIÊN ---
    
    def get_priority(row):
        ts = row['Timestamp_dt']
        symbol = row['Symbol']
        
        # Mốc 1: Đến ngày 11/02/2026 ưu tiên RCH2026
        limit1 = datetime(2026, 2, 12, 00, 29, 59)
        # Mốc 2: Từ sau đó đến ngày 10/04/2026 ưu tiên RCK2026
        limit2 = datetime(2026, 4, 10, 23, 29, 59)
        # Mốc 3: Còn lại đến 16/04/2026 ưu tiên RCN2026
        
        if ts <= limit1:
            return 0 if symbol == 'RCH2026' else 1
        elif ts <= limit2:
            return 0 if symbol == 'RCK2026' else 1
        else:
            return 0 if symbol == 'RCN2026' else 1

    # Tạo cột phụ để đánh dấu mức độ ưu tiên (0 là ưu tiên cao nhất)
    df['Priority'] = df.apply(get_priority, axis=1)

    # Sắp xếp theo Timestamp và sau đó là Priority
    df_sorted = df.sort_values(by=['Timestamp_dt', 'Priority'])

    # Xóa trùng: Chỉ giữ lại hàng đầu tiên cho mỗi Timestamp (hàng có Priority = 0 sẽ được giữ lại)
    df_after = df_sorted.drop_duplicates(subset=['Timestamp'], keep='first')

    # Loại bỏ các cột phụ trước khi lưu
    final_columns = ['Symbol', 'Timestamp', 'Open', 'High', 'Low', 'Close']
    df_after = df_after[final_columns]

    # Xuất file
    after_check_filename = 'RC_minute_history.xlsx'
    df_after.to_excel(after_check_filename, index=False)

    return check_filename, after_check_filename

# Thực thi
# process_chart_data_kc('D:/Download/chart_kc_export_2026-04-16.xlsx')
process_chart_data_rc('D:/Download/chart_rc_export_2026-04-17.xlsx')