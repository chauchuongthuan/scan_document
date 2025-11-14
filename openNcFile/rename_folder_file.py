import os
import re
from datetime import datetime

def rename_filtered_files(folder):
    """
    Đổi tên file filtered_chirps_pentad_YYYY_PX.csv -> filtered_DD_MM_YYYY - DD_MM_YYYY.csv
    Giữ nguyên nếu file đã đúng định dạng filtered_DD_MM_YYYY - DD_MM_YYYY.csv
    """

    parts = {
        "P1": ("01-01", "03-15"),
        "P2": ("03-16", "05-31"),
        "P3": ("06-01", "08-15"),
        "P4": ("08-16", "10-31"),
        "P5": ("11-01", "12-31"),
    }

    renamed = []

    for fname in os.listdir(folder):
        if not fname.lower().endswith(".csv"):
            continue

        old_path = os.path.join(folder, fname)
        new_name = None

        # -------- Trường hợp filtered_chirps_pentad_YYYY_PX.csv --------
        match = re.match(r"filtered_chirps_pentad_(\d{4})_(P[1-5])", fname)
        if match:
            year = int(match.group(1))
            part = match.group(2)
            start_str, end_str = parts[part]

            start_date = datetime.strptime(f"{start_str}-{year}", "%m-%d-%Y")
            end_date = datetime.strptime(f"{end_str}-{year}", "%m-%d-%Y")

            new_name = f"filtered_{start_date.day:02d}_{start_date.month:02d}_{start_date.year} - {end_date.day:02d}_{end_date.month:02d}_{end_date.year}.csv"

        # -------- Trường hợp đã đúng dạng filtered_DD_MM_YYYY - DD_MM_YYYY.csv --------
        elif re.match(r"filtered_\d{1,2}_\d{1,2}_\d{4}\s*-\s*\d{1,2}_\d{1,2}_\d{4}", fname):
            new_name = fname  # giữ nguyên

        # -------- Không khớp mẫu nào --------
        else:
            print(f"⚠️  Bỏ qua: {fname} (không khớp mẫu đặt tên)")
            continue

        new_path = os.path.join(folder, new_name)

        # Đổi tên nếu khác
        if fname != new_name:
            os.rename(old_path, new_path)
            print(f"✅ Đã đổi: {fname}  →  {new_name}")
        else:
            print(f"↔️  Giữ nguyên: {fname}")

        renamed.append(new_name)

    # -------- In danh sách sau khi sắp xếp theo ngày bắt đầu --------
    def extract_start_date(name):
        m = re.match(r"filtered_(\d{1,2})_(\d{1,2})_(\d{4})", name)
        if not m:
            return datetime.max
        d, mth, y = map(int, m.groups())
        return datetime(y, mth, d)

    renamed.sort(key=extract_start_date)

    print("\n📅 Danh sách sau khi sắp xếp:")
    for n in renamed:
        print("   ", n)

    return renamed


# ========== GỌI CHẠY ==========
if __name__ == "__main__":
    folder = r"D:\TransformFileGiaLai"
    rename_filtered_files(folder)
