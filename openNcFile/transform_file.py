import pandas as pd 
import geopandas as gpd 
from shapely.geometry import Point 
import os
import sys
print(sys.executable)
print(sys.path)

import sys

if len(sys.argv) < 3:
    print("⚠️  Cách dùng: python transformFile.py <input_csv> <output_csv>")
    sys.exit(1)

csv_path = sys.argv[1]
out_csv = sys.argv[2]
gadm_path = r"D:/PER_WORKSPACE/scan_document/openNcFile/gadm41_VNM_1.json"  # hoặc .shp
chunksize = 200000

def detect_cols(df):
    """Tự động tìm tên cột time/lat/lon/precip trong dataframe"""
    cols = [c for c in df.columns]
    possible_lat = [c for c in cols if c.lower() in ("lat","latitude","y")]
    possible_lon = [c for c in cols if c.lower() in ("lon","longitude","x")]
    possible_time = [c for c in cols if c.lower() in ("time","date","datetime")]
    possible_precip = [c for c in cols if c.lower() in ("precip","precipitation","value","precip_mm","precipitation(mm)")]
    return possible_time[0] if possible_time else None, \
           possible_lat[0] if possible_lat else None, \
           possible_lon[0] if possible_lon else None, \
           possible_precip[0] if possible_precip else None

# 1) load polygon daknong
print("Đọc shapefile/geojson:", gadm_path)
vn = gpd.read_file(gadm_path)
# tìm cột tên hành chính; ưu tiên NAME_1
if 'NAME_1' in vn.columns:
    daknong = vn[vn['NAME_1'].str.contains('ĐắkNông', case=False, na=False)].copy()
else:
    # fallback: tìm bất kỳ cột chuỗi nào có 'daknong'
    found_col = None
    for c in vn.columns:
        if vn[c].dtype == object and vn[c].str.contains('ĐắkNông', case=False, na=False).any():
            found_col = c
            break
    if not found_col:
        raise SystemExit("Không tìm thấy polygon 'ĐắkNông' trong shapefile/geojson. Kiểm tra file.")
    daknong = vn[vn[found_col].str.contains('ĐắkNông', case=False, na=False)].copy()

if daknong.empty:
    raise SystemExit("Không tìm thấy polygon daknong (kết quả rỗng). Kiểm tra file shapefile/geojson.")

# chuẩn CRS về WGS84
if daknong.crs is None:
    daknong = daknong.set_crs("EPSG:4326")
else:
    daknong = daknong.to_crs("EPSG:4326")

poly = daknong.unary_union  # polygon tổng hợp

# 2) đọc CSV theo chunks và lọc
print("Đang đọc CSV và lọc theo polygon daknong...")
rows_kept = []  # list để append DataFrame nhỏ

if chunksize:
    reader = pd.read_csv(csv_path, low_memory=False, chunksize=chunksize)
else:
    reader = [pd.read_csv(csv_path, low_memory=False)]

first_chunk = True
time_col = lat_col = lon_col = precip_col = None

for chunk in reader:
    # phát hiện cột lần đầu
    if first_chunk:
        time_col, lat_col, lon_col, precip_col = detect_cols(chunk)
        if not (time_col and lat_col and lon_col and precip_col):
            raise SystemExit(f"Không phát hiện đủ cột trong CSV. Phát hiện: time={time_col}, lat={lat_col}, lon={lon_col}, precip={precip_col}")
        print("Sử dụng cột:", "time=", time_col, "lat=", lat_col, "lon=", lon_col, "precip=", precip_col)
        first_chunk = False

    # ép kiểu an toàn
    chunk[lat_col] = pd.to_numeric(chunk[lat_col], errors='coerce')
    chunk[lon_col] = pd.to_numeric(chunk[lon_col], errors='coerce')
    chunk[precip_col] = pd.to_numeric(chunk[precip_col], errors='coerce')
    chunk[time_col] = pd.to_datetime(chunk[time_col], errors='coerce')

    # drop hàng thiếu tọa độ hoặc thời gian
    chunk = chunk.dropna(subset=[lat_col, lon_col, time_col])

    if chunk.empty:
        continue

    # tạo geometry và GeoDataFrame
    geometry = [Point(xy) for xy in zip(chunk[lon_col].values, chunk[lat_col].values)]
    gchunk = gpd.GeoDataFrame(chunk, geometry=geometry, crs="EPSG:4326")

    # lọc những điểm nằm trong polygon daknong
    mask = gchunk.geometry.within(poly)
    gchunk = gchunk[mask]

    if gchunk.empty:
        continue

    # chỉ giữ 4 cột cần thiết: date (YYYY-MM-DD), lat, lon, precip
    out_df = pd.DataFrame({
        'date': gchunk[time_col].dt.date.astype(str),
        'latitude': gchunk[lat_col].astype(float),
        'longitude': gchunk[lon_col].astype(float),
        'precip': gchunk[precip_col].astype(float)
    })
    rows_kept.append(out_df)

# 3) ghép và lưu
if not rows_kept:
    raise SystemExit("Không có điểm nào thuộc daknong trong file CSV (sau lọc). Kiểm tra bounding box / dữ liệu.")
result = pd.concat(rows_kept, ignore_index=True)

# sắp xếp theo date, lat, lon (tuỳ chọn)
result = result.sort_values(['date','latitude','longitude']).reset_index(drop=True)

# lưu
result.to_csv(out_csv, index=False)
print(f"Hoàn thành — đã lưu {len(result)} hàng vào: {out_csv}")

