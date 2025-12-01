import pandas as pd
import json

def json_to_excel(json_filepath, excel_filepath):
    """
    Đọc dữ liệu từ file JSON, chuyển đổi thành DataFrame có 2 cột 'Date' và 'Bags',
    và lưu vào file Excel.

    :param json_filepath: Đường dẫn tới file JSON đầu vào.
    :param excel_filepath: Đường dẫn tới file Excel đầu ra.
    """
    try:
        # 1. Đọc dữ liệu từ file JSON
        with open(json_filepath, 'r') as f:
            data = json.load(f)

        # 2. Chuyển đổi dữ liệu thành DataFrame
        # Mỗi phần tử trong list là một row: [Date, Bags]
        # Ta đặt tên cột là 'Date' và 'Bags'
        df = pd.DataFrame(data, columns=['Date', 'Bags'])

        # Tùy chọn: Chuyển đổi cột 'Bags' sang kiểu số (float)
        df['Bags'] = pd.to_numeric(df['Bags'], errors='coerce')
        
        # Tùy chọn: Chuyển đổi cột 'Date' sang kiểu datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # 3. Lưu DataFrame vào file Excel
        df.to_excel(excel_filepath, index=False) # index=False để không ghi số thứ tự hàng vào Excel

        print(f"✅ Chuyển đổi thành công! Dữ liệu đã được lưu vào: {excel_filepath}")
        print("\n---")
        print("Dữ liệu 5 hàng đầu trong DataFrame:")
        print(df.head())

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file tại đường dẫn: {json_filepath}")
    except json.JSONDecodeError:
        print(f"❌ Lỗi: File {json_filepath} không phải là JSON hợp lệ.")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi: {e}")

# --- Ví dụ sử dụng ---
# Lưu ý: Đảm bảo file 'stock_coffee_data.json' nằm cùng thư mục 
# hoặc bạn cung cấp đường dẫn đầy đủ.
input_file = "marketAgent\stock_coffee_data.json"
output_file = "marketAgent\coffee_stock_data.xlsx"

json_to_excel(input_file, output_file)