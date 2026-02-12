import pandas as pd

def transform_data_structure(input_file, output_file):
    # 1. Đọc file CSV (bỏ qua dòng trống đầu tiên nếu có)
    df = pd.read_excel(input_file)
    
    # 2. Xác định cột chứa Ngày (thường là cột đầu tiên sau index)
    # Dựa trên snippet, cột ngày đang không có tên hoặc nằm ở cột 0/1
    # Chúng ta sẽ đặt tên lại cho cột để dễ xử lý
    df.columns = ['Unnamed', 'datetime', '2022', '2023', '2024', '2025']
    
    # 3. Tách cột datetime thành 2 cột: Date và Time
    # Logic: Nếu giá trị chứa dấu gạch ngang '-' thì đó là Ngày (01-Apr), 
    # Nếu chứa 'AM'/'PM' thì đó là Giờ.
    
    current_date = None
    new_rows = []
    
    for index, row in df.iterrows():
        val = str(row['datetime']).strip()
        
        # Kiểm tra nếu là dòng chứa Ngày (VD: 01-Apr, 31-May)
        if '-' in val and 'AM' not in val and 'PM' not in val:
            current_date = val
            continue # Bỏ qua không thêm dòng này vào data vì nó chỉ là tiêu đề ngày
            
        # Nếu là dòng chứa Giờ (VD: 1 PM, 10 AM)
        elif 'AM' in val or 'PM' in val:
            new_row = row.copy()
            new_row['Unnamed'] = current_date # Điền ngày vào cột đầu tiên
            new_rows.append(new_row)
            
    # 4. Tạo DataFrame mới từ list kết quả
    final_df = pd.DataFrame(new_rows)
    
    # 5. Lưu kết quả
    final_df.to_excel(output_file, index=False)
    print(f"Đã chuyển đổi thành công! File lưu tại: {output_file}")

# Sử dụng hàm
input_path = 'C:/Users/COMPUTER/Downloads/new_data.xlsx'
output_path = 'D:/PER_WORKSPACE/scan_document/media/new_data_display.xlsx'
transform_data_structure(input_path, output_path)