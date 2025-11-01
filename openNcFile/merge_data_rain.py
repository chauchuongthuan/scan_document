import os
import re
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

# PostgreSQL engine
engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/scan_document")

def detect_cols(df):
    cols = [c for c in df.columns]
    time_cols = [c for c in cols if c.lower() in ("date","time","datetime")]
    lat_cols = [c for c in cols if c.lower() in ("lat","latitude","y")]
    lon_cols = [c for c in cols if c.lower() in ("lon","longitude","x")]
    precip_cols = [c for c in cols if c.lower() in ("precip","precipitation","value","precip_mm")]
    return (time_cols[0] if time_cols else None,
            lat_cols[0] if lat_cols else None,
            lon_cols[0] if lon_cols else None,
            precip_cols[0] if precip_cols else None)

def merge_filtered_to_postgres(folder, table_name="rain_lamdong", chunksize=100000):
    """
    Gộp các file filtered_*.csv trong folder vào PostgreSQL table.
    Tự loại trùng (date, lat, lon) nhờ PRIMARY KEY.
    """

    files = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]

    # Sắp xếp file theo ngày bắt đầu trong tên
    def extract_start_date(fname):
        m = re.search(r"(\d{1,2})_(\d{1,2})_(\d{4})", fname)
        if not m:
            return datetime.max
        d, mth, y = map(int, m.groups())
        return datetime(y, mth, d)
    files.sort(key=extract_start_date)

    # 🧱 Tạo bảng nếu chưa có
    with engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date DATE NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                precip DOUBLE PRECISION,
                PRIMARY KEY (date, latitude, longitude)
            );
        """))
        conn.commit()

    total_inserted = 0
    total_skipped = 0

    for fname in files:
        fpath = os.path.join(folder, fname)
        print(f"🔹 Đang xử lý file: {fname}")

        try:
            reader = pd.read_csv(fpath, low_memory=False, chunksize=chunksize)
        except Exception as e:
            print(f"⚠️ Không đọc được {fname}: {e}")
            continue

        first_chunk = True
        time_col = lat_col = lon_col = precip_col = None

        for chunk in reader:
            if first_chunk:
                time_col, lat_col, lon_col, precip_col = detect_cols(chunk)
                if not (time_col and lat_col and lon_col and precip_col):
                    print(f"❌ Không phát hiện đủ cột trong {fname}")
                    break
                first_chunk = False

            # Làm sạch dữ liệu
            chunk[lat_col] = pd.to_numeric(chunk[lat_col], errors='coerce')
            chunk[lon_col] = pd.to_numeric(chunk[lon_col], errors='coerce')
            chunk[precip_col] = pd.to_numeric(chunk[precip_col], errors='coerce')
            chunk[time_col] = pd.to_datetime(chunk[time_col], errors='coerce')
            chunk = chunk.dropna(subset=[time_col, lat_col, lon_col])
            if chunk.empty:
                continue

            # Chuyển về định dạng chuẩn
            chunk["date"] = chunk[time_col].dt.date
            chunk = chunk.rename(columns={
                lat_col: "latitude",
                lon_col: "longitude",
                precip_col: "precip"
            })[["date", "latitude", "longitude", "precip"]]

            # Ghi từng chunk vào Postgres (insert conflict → ignore)
            try:
                with engine.begin() as conn:
                    for i in range(0, len(chunk), 5000):
                        sub = chunk.iloc[i:i+5000]
                        values = ",".join(
                            conn.engine.dialect.execute_sequence_format(
                                f"({','.join(['%s'] * 4)})", len(sub)
                            )
                        )
                        data = [tuple(x) for x in sub.to_numpy()]
                        conn.execute(
                            text(f"""
                                INSERT INTO {table_name} (date, latitude, longitude, precip)
                                VALUES {','.join(['(:date, :latitude, :longitude, :precip)'])}
                                ON CONFLICT (date, latitude, longitude) DO NOTHING
                            """),
                            [dict(zip(["date", "latitude", "longitude", "precip"], row)) for row in data]
                        )
            except Exception as e:
                print(f"⚠️ Lỗi khi chèn {fname}: {e}")
                continue

        print(f"✅ Hoàn tất {fname}")

    print("🎯 Gộp dữ liệu hoàn tất. Chuẩn bị xuất ra CSV...")

    # Xuất ra file CSV kết quả
    out_csv = os.path.join(folder, "rain_Lam_Dong_2015_2025.csv")
    with engine.connect() as conn, open(out_csv, "w", encoding="utf-8") as fout:
        fout.write("date,latitude,longitude,precip\n")
        for chunk in pd.read_sql(text(f"SELECT date, latitude, longitude, precip FROM {table_name} ORDER BY date, latitude, longitude"), conn, chunksize=100000):
            chunk.to_csv(fout, header=False, index=False)

    print(f"✅ Xuất hoàn tất: {out_csv}")
    return out_csv
