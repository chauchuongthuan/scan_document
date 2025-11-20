import os
import pandas as pd 
import geopandas as gpd 
from shapely.geometry import Point 
import os
import sys
import subprocess

# Thư mục chứa các file CSV tải từ ERDDAP
input_dir = r"D:/CHIRPS_PENTAD_DAK_NONG"

# Đường dẫn script gốc
script_path = r"D:\PER_WORKSPACE\scan_document\openNcFile\transformFile.py"

# Thư mục xuất kết quả lọc
output_dir = r"D:/TransformFileDakNong"
os.makedirs(output_dir, exist_ok=True)

for fname in os.listdir(input_dir):
    if not fname.lower().endswith(".csv"):
        continue

    csv_path = os.path.join(input_dir, fname)
    out_csv = os.path.join(output_dir, f"filtered_{fname}")

    print(f"🔹 Đang xử lý: {fname}")

    # Gọi script transformFile.py bằng subprocess và truyền tham số động
    cmd = [
        sys.executable,  # dùng Python đang chạy script hiện tại (có pandas)
        script_path,
        csv_path,
        out_csv
    ]
    subprocess.run(cmd)