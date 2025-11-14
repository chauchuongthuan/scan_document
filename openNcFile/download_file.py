import os
import requests
from datetime import datetime

def download_chirps_pentad_split5(
    save_dir,
    lat_min=11,
    lat_max=13,
    lon_min=107,
    lon_max=109,
    start_year=2015,
    end_year=2025,
):
    """
    Tải dữ liệu CHIRPS Pentad theo 5 phần mỗi năm (để tránh lỗi 500 hoặc treo máy).
    """
    message = ""
    base_url = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalPentadP05_Lon0360.csv?"
    
    # Định nghĩa 5 phần mỗi năm
    parts = [
        ("P1", "01-01", "03-15"),
        ("P2", "03-16", "05-31"),
        ("P3", "06-01", "08-15"),
        ("P4", "08-16", "10-31"),
        ("P5", "11-01", "12-31"),
    ]

    os.makedirs(save_dir, exist_ok=True)

    for year in range(start_year, end_year + 1):
        for p_label, p_start, p_end in parts:

            # Ngừng ở 2/2025
            if year == 2025 and p_start > "02-26":
                break

            start_date = f"{year}-{p_start}T00:00:00Z"
            end_date = f"{year}-{p_end}T00:00:00Z"

            url = (
                f"{base_url}"
                f"precip[({start_date}):1:({end_date})]"
                f"[({lat_min}):1:({lat_max})]"
                f"[({lon_min}):1:({lon_max})]"
            )

            filename = f"chirps_pentad_{year}_{p_label}.csv"
            filepath = os.path.join(save_dir, filename)

            if os.path.exists(filepath):
                print(f"✅ Bỏ qua {filename} (đã tồn tại)")
                message += f"✅ Bỏ qua {filename} (đã tồn tại)\n"
                continue

            print(f"⬇️  Đang tải {filename} ...")
            try:
                response = requests.get(url, timeout=300)
                if response.status_code != 200:
                    print(f"⚠️  Lỗi {response.status_code} cho {filename}, bỏ qua.")
                    message += f"⚠️  Lỗi {response.status_code} cho {filename}, bỏ qua.\n"
                    continue

                with open(filepath, "wb") as f:
                    f.write(response.content)

                print(f"✅ Hoàn tất: {filename} ({len(response.content)/1e6:.2f} MB)")
                message += f"✅ Hoàn tất: {filename} ({len(response.content)/1e6:.2f} MB)\n"

            except Exception as e:
                print(f"❌ Lỗi khi tải {filename}: {e}")
                message += f"❌ Lỗi khi tải {filename}: {e}\n"
                continue
            
    print("\n🎯 Tải xong toàn bộ dữ liệu!")
    message += "\n🎯 Tải xong toàn bộ dữ liệu!\n"
    return message

# ================================
# 🧭 Gọi hàm ví dụ:
# ================================
if __name__ == "__main__":
    download_chirps_pentad_split5(
        save_dir="D:/CHIRPS_PENTAD_DAK_NONG",
        lat_min=11,
        lat_max=13,
        lon_min=107,
        lon_max=109,
        start_year=2015,
        end_year=2025
    )


# # ========== Cấu hình (SỬA THEO MÁY BẠN) ==========
# csv_path = r"D:/PER_WORKSPACE/scan_document/openNcFile/csv_output/chirps_1981_pentads.csv"
# gadm_path = r"D:/PER_WORKSPACE/scan_document/openNcFile/gadm41_VNM_1.json"  # hoặc .shp
# out_csv = r"rain_gialai_points_2025.csv"
# chunksize = 200000  # tăng/giảm tùy RAM; đặt None để đọc 1 lần nếu file nhỏ
# # =================================================

# def detect_cols(df):
#     """Tự động tìm tên cột time/lat/lon/precip trong dataframe"""
#     cols = [c for c in df.columns]
#     possible_lat = [c for c in cols if c.lower() in ("lat","latitude","y")]
#     possible_lon = [c for c in cols if c.lower() in ("lon","longitude","x")]
#     possible_time = [c for c in cols if c.lower() in ("time","date","datetime")]
#     possible_precip = [c for c in cols if c.lower() in ("precip","precipitation","value","precip_mm","precipitation(mm)")]
#     return possible_time[0] if possible_time else None, \
#            possible_lat[0] if possible_lat else None, \
#            possible_lon[0] if possible_lon else None, \
#            possible_precip[0] if possible_precip else None

# # 1) load polygon GiaLai
# print("Đọc shapefile/geojson:", gadm_path)
# vn = gpd.read_file(gadm_path)
# # tìm cột tên hành chính; ưu tiên NAME_1
# if 'NAME_1' in vn.columns:
#     gialai = vn[vn['NAME_1'].str.contains('GiaLai', case=False, na=False)].copy()
# else:
#     # fallback: tìm bất kỳ cột chuỗi nào có 'GiaLai'
#     found_col = None
#     for c in vn.columns:
#         if vn[c].dtype == object and vn[c].str.contains('GiaLai', case=False, na=False).any():
#             found_col = c
#             break
#     if not found_col:
#         raise SystemExit("Không tìm thấy polygon 'GiaLai' trong shapefile/geojson. Kiểm tra file.")
#     gialai = vn[vn[found_col].str.contains('GiaLai', case=False, na=False)].copy()

# if gialai.empty:
#     raise SystemExit("Không tìm thấy polygon GiaLai (kết quả rỗng). Kiểm tra file shapefile/geojson.")

# # chuẩn CRS về WGS84
# if gialai.crs is None:
#     gialai = gialai.set_crs("EPSG:4326")
# else:
#     gialai = gialai.to_crs("EPSG:4326")

# poly = gialai.unary_union  # polygon tổng hợp

# # 2) đọc CSV theo chunks và lọc
# print("Đang đọc CSV và lọc theo polygon GiaLai...")
# rows_kept = []  # list để append DataFrame nhỏ

# if chunksize:
#     reader = pd.read_csv(csv_path, low_memory=False, chunksize=chunksize)
# else:
#     reader = [pd.read_csv(csv_path, low_memory=False)]

# first_chunk = True
# time_col = lat_col = lon_col = precip_col = None

# for chunk in reader:
#     # phát hiện cột lần đầu
#     if first_chunk:
#         time_col, lat_col, lon_col, precip_col = detect_cols(chunk)
#         if not (time_col and lat_col and lon_col and precip_col):
#             raise SystemExit(f"Không phát hiện đủ cột trong CSV. Phát hiện: time={time_col}, lat={lat_col}, lon={lon_col}, precip={precip_col}")
#         print("Sử dụng cột:", "time=", time_col, "lat=", lat_col, "lon=", lon_col, "precip=", precip_col)
#         first_chunk = False

#     # ép kiểu an toàn
#     chunk[lat_col] = pd.to_numeric(chunk[lat_col], errors='coerce')
#     chunk[lon_col] = pd.to_numeric(chunk[lon_col], errors='coerce')
#     chunk[precip_col] = pd.to_numeric(chunk[precip_col], errors='coerce')
#     chunk[time_col] = pd.to_datetime(chunk[time_col], errors='coerce')

#     # drop hàng thiếu tọa độ hoặc thời gian
#     chunk = chunk.dropna(subset=[lat_col, lon_col, time_col])

#     if chunk.empty:
#         continue

#     # tạo geometry và GeoDataFrame
#     geometry = [Point(xy) for xy in zip(chunk[lon_col].values, chunk[lat_col].values)]
#     gchunk = gpd.GeoDataFrame(chunk, geometry=geometry, crs="EPSG:4326")

#     # lọc những điểm nằm trong polygon GiaLai
#     mask = gchunk.geometry.within(poly)
#     gchunk = gchunk[mask]

#     if gchunk.empty:
#         continue

#     # chỉ giữ 4 cột cần thiết: date (YYYY-MM-DD), lat, lon, precip
#     out_df = pd.DataFrame({
#         'date': gchunk[time_col].dt.date.astype(str),
#         'latitude': gchunk[lat_col].astype(float),
#         'longitude': gchunk[lon_col].astype(float),
#         'precip': gchunk[precip_col].astype(float)
#     })
#     rows_kept.append(out_df)

# # 3) ghép và lưu
# if not rows_kept:
#     raise SystemExit("Không có điểm nào thuộc GiaLai trong file CSV (sau lọc). Kiểm tra bounding box / dữ liệu.")
# result = pd.concat(rows_kept, ignore_index=True)

# # sắp xếp theo date, lat, lon (tuỳ chọn)
# result = result.sort_values(['date','latitude','longitude']).reset_index(drop=True)

# # lưu
# result.to_csv(out_csv, index=False)
# print(f"Hoàn thành — đã lưu {len(result)} hàng vào: {out_csv}")

