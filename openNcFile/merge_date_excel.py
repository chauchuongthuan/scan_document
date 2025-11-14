import pandas as pd
import os

def merge_by_day(filepath: str, sheet_name: str = 0, output_path: str = None):
    # Đọc file Excel gốc
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    # Tìm các cột là năm (kiểu số)
    years = [col for col in df.columns if isinstance(col, (int, float))]
    merged_df = pd.DataFrame()

    for year in years:
        # Tìm cột ngày đứng trước cột năm
        year_col_index = df.columns.get_loc(year)
        date_col = df.columns[year_col_index - 1]

        temp = df[[date_col, year]].dropna()
        temp.columns = ["ExcelDate", str(int(year))]

        # Chuyển đổi Excel serial date sang datetime
        temp["Date"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(temp["ExcelDate"], unit="D")

        # Chuyển sang dạng chỉ ngày-tháng (loại bỏ năm)
        temp["Day"] = temp["Date"].dt.strftime("%m-%d")

        # Giữ lại cột Day và năm
        temp = temp[["Day", str(int(year))]]

        # Gộp với bảng tổng
        if merged_df.empty:
            merged_df = temp
        else:
            merged_df = pd.merge(merged_df, temp, on="Day", how="outer")

    # Sắp xếp theo thứ tự ngày trong năm (MM-DD)
    merged_df = merged_df.sort_values("Day").reset_index(drop=True)

    # Đặt đường dẫn xuất file
    if output_path is None:
        base, ext = os.path.splitext(filepath)
        output_path = f"{base}_merged_by_day.xlsx"

    # Xuất ra file Excel
    merged_df.to_excel(output_path, index=False)
    print(f"✅ Đã xuất file tổng hợp: {output_path}")

    return merged_df


# --- Ví dụ sử dụng ---
if __name__ == "__main__":
    file_path = r"C:\Users\COMPUTER\Desktop\AskGPTLamDong.xlsx"
    merged = merge_by_day(file_path)
