# import pandas as pd

# # 1. Đọc file CSV
# df = pd.read_csv("C:/Users/COMPUTER/Desktop/VietNam_coffee_regions.csv")

# # 2. Xuất sang Parquet (tự động nén Snappy)
# df.to_parquet("C:/Users/COMPUTER/Desktop/VietNam_coffee_regions.parquet", index=False)

# print("Chuyển đổi thành công!")

# import pyarrow.parquet as pq

# table = pq.read_table("C:/Users/COMPUTER/Desktop/VietNam_coffee_regions.parquet")
# print(table.schema)

import geopandas as gpd

gdf = gpd.read_file("D:/Download/vietnam_admin3.geojson")
gdf.to_file("D:/Download/vietnam_admin3.shp")