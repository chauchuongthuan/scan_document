import pandas as pd
from bs4 import BeautifulSoup

def export_html_to_excel(html_file_path, output_excel_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr')
    data_list = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 10:
            raw_row = [col.get_text(strip=True) for col in cols]
            record = {
                "ID": raw_row[0],
                "Ngày": raw_row[1],
                "Mở cửa": raw_row[2],
                "Cao nhất": raw_row[3],
                "Thấp nhất": raw_row[4],
                "Đóng cửa": raw_row[5],
                "Thay đổi %": raw_row[6],
                "Thay đổi giá": raw_row[7],
                "Khối lượng": raw_row[8],
                "HĐ mở (OI)": raw_row[9]
            }
            data_list.append(record)

    if data_list:
        df = pd.DataFrame(data_list)
        
        # Các cột cần chuyển sang số
        numeric_cols = ["Mở cửa", "Cao nhất", "Thấp nhất", "Đóng cửa", "Thay đổi giá", "Khối lượng", "HĐ mở (OI)"]
        
        for col in numeric_cols:
            # Bước 1: Xóa dấu phẩy phân cách phần nghìn
            df[col] = df[col].str.replace(',', '')
            
            # Bước 2: Chuyển sang số, lỗi hoặc trống sẽ biến thành NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Bước 3: (Tùy chọn) Thay thế các ô trống (NaN) bằng số 0
            df[col] = df[col].fillna(0)

        # Xuất ra file Excel
        df.to_excel(output_excel_path, index=False, engine='openpyxl')
        print(f"Xử lý xong! File đã lưu tại: {output_excel_path}")
    else:
        print("Không tìm thấy dữ liệu.")

# Chạy thử
export_html_to_excel('D:/PER_WORKSPACE/scan_document/media/kc_history.html', 'D:/PER_WORKSPACE/scan_document/media/kc_data_history_stooq.xlsx')