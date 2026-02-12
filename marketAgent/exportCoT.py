import pandas as pd
import os
import logging
from pathlib import Path

# 1. Cấu hình Logging để theo dõi tiến trình và lỗi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("process_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def process_coffee_cot_data(input_folder, output_filename):
    """
    Đọc tất cả file .xls trong thư mục, lọc dữ liệu Coffee và xuất ra Excel.
    """
    market_code = [
        "083731"
    ]
    
    all_data = []
    folder_path = Path(input_folder)
    
    # Lấy danh sách file .xls và .xlsx
    files = [f for f in os.listdir(input_folder) if f.endswith(('.xls', '.xlsx'))]
    files.sort() # Sắp xếp theo tên để xử lý theo thứ tự thời gian
    
    logging.info(f"Tìm thấy {len(files)} file trong thư mục {input_folder}")

    for file_name in files:
        file_path = folder_path / file_name
        logging.info(f"Đang xử lý file: {file_name}")
        
        try:
            # Đọc file Excel
            # Lưu ý: engine='xlrd' cho .xls và engine='openpyxl' cho .xlsx
            engine = 'xlrd' if file_name.endswith('.xls') else 'openpyxl'
            df = pd.read_excel(file_path, engine=engine)
            
            # Kiểm tra xem cột CFTC_Contract_Market_Code có tồn tại không
            col_name = 'CFTC_Contract_Market_Code'
            if col_name not in df.columns:
                # Thử tìm cột có tên tương tự (xóa khoảng trắng, viết hoa)
                df.columns = [c.strip() for c in df.columns]
                if col_name not in df.columns:
                    logging.warning(f"File {file_name} không có cột '{col_name}'. Bỏ qua.")
                    continue

            # Lọc dữ liệu Coffee (sử dụng .isin để lọc nhanh)
            # Dùng str.strip() để tránh lỗi do khoảng trắng thừa trong dữ liệu gốc
            filtered_df = df[df[col_name].astype(str).str.strip().isin(market_code)].copy()
            
            if not filtered_df.empty:
                all_data.append(filtered_df)
                logging.info(f"--> Tìm thấy {len(filtered_df)} dòng dữ liệu Coffee.")
            else:
                logging.warning(f"--> Không tìm thấy tên thị trường phù hợp trong file {file_name}.")
                
        except Exception as e:
            logging.error(f"Lỗi khi xử lý file {file_name}: {str(e)}")

    # 2. Tổng hợp và Xuất dữ liệu
    if all_data:
        logging.info("Đang tổng hợp dữ liệu...")
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Chuyển đổi cột ngày tháng nếu cần (giúp sắp xếp chuẩn hơn)
        date_col = 'Report_Date_as_MM_DD_YYYY'
        if date_col in final_df.columns:
            final_df[date_col] = pd.to_datetime(final_df[date_col], errors='coerce')
            final_df = final_df.sort_values(by=date_col)

        try:
            final_df.to_excel(output_filename, index=False)
            logging.info(f"XUẤT FILE THÀNH CÔNG: {output_filename}")
            logging.info(f"Tổng số dòng thu thập được: {len(final_df)}")
        except Exception as e:
            logging.error(f"Lỗi khi lưu file Excel tổng: {str(e)}")
    else:
        logging.error("Không có dữ liệu nào được tìm thấy để xuất file.")

if __name__ == "__main__":
    folder_input = "D:/PER_WORKSPACE/scan_document/media/tong_hop_du_lieu_cot_2026"
    output_file = "D:/PER_WORKSPACE/scan_document/media/tong_hop_du_lieu_cot_2026/Tong_Hop_CoT_Coffee_C.xlsx"
    process_coffee_cot_data(folder_input, output_file)