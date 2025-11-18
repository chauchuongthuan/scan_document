from tvDatafeed import TvDatafeed, Interval
import pandas as pd
from openpyxl import Workbook
import os
from datetime import datetime

tv = TvDatafeed()

df = tv.get_hist(
    symbol="KC2!",
    exchange="ICEUS",
    # symbol="RC1!",
    # exchange="ICEEUR",
    interval=Interval.in_1_minute,
    n_bars=100000
)
print(df)
# def detect_unfilled_gaps(df):
#     gaps = []

#     df = df.copy().reset_index()

#     for i in range(1, len(df)):
#         prev_high = df.loc[i-1, 'high']
#         prev_low = df.loc[i-1, 'low']
#         curr_high = df.loc[i, 'high']
#         curr_low  = df.loc[i, 'low']

#         # GAP UP
#         if curr_low > prev_high:
#             gaps.append({
#                 "index": i,
#                 "time": df.loc[i, 'datetime'],
#                 "type": "GAP_UP",
#                 "gap_low": prev_high,
#                 "gap_high": curr_low,
#                 "gap_size": curr_low - prev_high,
#                 "filled": False
#             })

#         # GAP DOWN
#         elif curr_high < prev_low:
#             gaps.append({
#                 "index": i,
#                 "time": df.loc[i, 'datetime'],
#                 "type": "GAP_DOWN",
#                 "gap_low": curr_high,
#                 "gap_high": prev_low,
#                 "gap_size": prev_low - curr_high,
#                 "filled": False
#             })

#     # Kiểm tra gap đã đóng chưa
#     for g in gaps:
#         low = g["gap_low"]
#         high = g["gap_high"]
#         future = df[df["datetime"] > g["time"]]

#         for _, row in future.iterrows():
#             if row["low"] <= high and row["high"] >= low:
#                 g["filled"] = True
#                 break

#     unfilled = [g for g in gaps if g["filled"] == False]

#     return pd.DataFrame(unfilled)

# # --- TÍNH GAP ---
# unfilled_gaps = detect_unfilled_gaps(df)
# print(unfilled_gaps)

# --- XUẤT FILE EXCEL ---
# output_file = f"unfilled_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
output_file = f"data_kc2.xlsx"
output_path = os.path.join(os.path.dirname(__file__), output_file)
df.to_excel(output_path)
# unfilled_gaps.to_excel(output_path, index=False)
print(f"\nFile Excel đã được tạo: {output_path}")
