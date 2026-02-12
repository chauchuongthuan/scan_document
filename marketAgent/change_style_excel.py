import pandas as pd

def transform_revenue_data(input_file, output_file):
    # 1. Đọc file Excel
    df = pd.read_excel(input_file)
    
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    # Lấy danh sách các cột giờ thực tế từ file (trừ cột datetime)
    # Đây chính là danh sách "set cứng" thứ tự các cột như file gốc
    hour_order = [col for col in df.columns if col != 'datetime']

    # 2. Melt dữ liệu
    df_melted = df.melt(id_vars=['datetime'], 
                        var_name='Time', 
                        value_name='Revenue')

    # 3. SET CỨNG THỨ TỰ CHO CỘT TIME
    # Chuyển cột Time sang dạng Categorical với danh sách đã lấy ở bước 1
    df_melted['Time'] = pd.Categorical(df_melted['Time'], categories=hour_order, ordered=True)

    # 4. CHUẨN HÓA DATETIME ĐỂ SORT NGÀY
    df_melted['datetime'] = pd.to_datetime(df_melted['datetime'])

    # 5. SẮP XẾP: Theo ngày trước, sau đó theo thứ tự "set cứng" của Time
    df_melted = df_melted.sort_values(by=['datetime', 'Time'])

    # 6. ĐỊNH DẠNG HIỂN THỊ VÀ XUẤT FILE
    df_melted['datetime'] = df_melted['datetime'].dt.strftime('%d/%m/%Y')
    
    df_melted.to_excel(output_file, index=False)
    print(f"Đã chuyển đổi thành công! Thứ tự giờ được giữ nguyên như file gốc.")

# Thực thi
input_path = 'C:/Users/COMPUTER/Downloads/doanh_thu_theo_gio.xlsx'
output_path = 'D:/PER_WORKSPACE/scan_document/media/doanh_thu_theo_gio_display.xlsx'
transform_revenue_data(input_path, output_path)
