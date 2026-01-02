import os
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings # Import settings
import numpy as np
import re
import pandas as pd
from django.shortcuts import render
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
import datetime
import math
from chartOHLC.models import OHLCDataKC, OHLCDataRC
from django.utils import timezone # Import thư viện timezone của Django
import pytz

class TVGetDatafeedView(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                symbol_text = request.POST.get('symbol', '')
                n_bars_input = request.POST.get('n_bars', 10000)
                interval_input_text = request.POST.get('interval', '')
                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)
                
                if interval_input_text == "in_daily":
                    interval_input = Interval.in_daily
                elif interval_input_text == "in_1_minute":
                    interval_input = Interval.in_1_minute

                if symbol_text == "KCH2026": # Cuối tháng 1 đổi sang KCK
                    exchange_text = "ICEUS"
                elif symbol_text == "RCH2026":
                    exchange_text = "ICEEUR"
                else:
                    exchange_text = "ICEUS"

                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=interval_input,
                    n_bars=int(n_bars_input)
                )
                
                print(df)
                # if df is not None:
                #     df = df.reset_index()
                #     for _, row in df.iterrows():
                #         naive_dt = row['datetime']
                #         timezone_dt = timezone.make_aware(naive_dt, pytz.timezone('Asia/Ho_Chi_Minh'))
                #         if symbol_text == "KCH2026":
                #             OHLCDataKC.objects.update_or_create(
                #                 symbol=symbol_text,
                #                 timestamp=timezone_dt,
                #                 defaults={
                #                     'open': row['open'], 'high': row['high'],
                #                     'low': row['low'], 'close': row['close'],
                #                     'volume': row['volume']
                #                 }
                #             )
                #         elif symbol_text == "RCH2026":
                #             OHLCDataRC.objects.update_or_create(
                #                 symbol=symbol_text,
                #                 timestamp=timezone_dt,
                #                 defaults={
                #                     'open': row['open'], 'high': row['high'],
                #                     'low': row['low'], 'close': row['close'],
                #                     'volume': row['volume']
                #                 }
                #             )
                        
                output_file = f"data_{symbol_text}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
                output_path = os.path.join(settings.MEDIA_ROOT, 'tvdatafeed', output_file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_excel(output_path)
                return JsonResponse({
                    "status": "success",
                    "message": "Created successfully",
                    "result": f"/media/tvdatafeed/{output_file}"
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Get data failed: {str(e)}"
                }, status=500)
        return render(request, 'market-agent/get-datafeed.html')

class TVUnfilledGapView(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                symbol_text = request.POST.get('symbol', '')
                n_bars_input = request.POST.get('n_bars', 10000)
                interval_input_text = request.POST.get('interval', '')

                if interval_input_text == "in_daily":
                    interval_input = Interval.in_daily
                elif interval_input_text == "in_1_minute":
                    interval_input = Interval.in_1_minute
                    
                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)
                
                if symbol_text == "KCH2026": # Cuối tháng 1 đổi sang KCK
                    exchange_text = "ICEUS"
                elif symbol_text == "RCH2026":
                    exchange_text = "ICEEUR"
                else:
                    exchange_text = "ICEUS"
                
                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=interval_input,
                    n_bars=int(n_bars_input)
                )
                gaps = []
                
                df = df.copy().reset_index()

                for i in range(1, len(df)):
                    prev_high = df.loc[i-1, 'high']
                    prev_low = df.loc[i-1, 'low']
                    curr_high = df.loc[i, 'high']
                    curr_low  = df.loc[i, 'low']

                    # GAP UP
                    if curr_low > prev_high:
                        gaps.append({
                            "index": i,
                            "time": df.loc[i, 'datetime'],
                            "type": "GAP_UP",
                            "gap_low": prev_high,
                            "gap_high": curr_low,
                            "gap_size": curr_low - prev_high,
                            "filled": False
                        })

                    # GAP DOWN
                    elif curr_high < prev_low:
                        gaps.append({
                            "index": i,
                            "time": df.loc[i, 'datetime'],
                            "type": "GAP_DOWN",
                            "gap_low": curr_high,
                            "gap_high": prev_low,
                            "gap_size": prev_low - curr_high,
                            "filled": False
                        })

                # Kiểm tra gap đã đóng chưa
                for g in gaps:
                    low = g["gap_low"]
                    high = g["gap_high"]
                    future = df[df["datetime"] > g["time"]]

                    filled = is_gap_filled_by_intervals(low, high, future)
                    g["filled"] = bool(filled)
                
                unfilled = [g for g in gaps if g["filled"] == False]
                unfilled_gaps = pd.DataFrame(unfilled)
                output_file = f"unfilled_gaps_{symbol_text}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
                output_path = os.path.join(settings.MEDIA_ROOT, 'tvdatafeed', output_file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                unfilled_gaps.to_excel(output_path, index=False)
                return JsonResponse({
                    "status": "success",
                    "message": "Created successfully",
                    "result": f"/media/tvdatafeed/{output_file}"
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Get data failed: {str(e)}"
                }, status=500)
        return render(request, 'market-agent/get-datafeed-gap.html')

def is_gap_filled_by_intervals(gap_low, gap_high, future_df):
    """
    Kiểm tra gap đã fill hoàn toàn bằng union của intervals future.
    Đã tối ưu hiệu năng: không dùng iterrows, dùng numpy + merge intervals nhanh.
    """

    if future_df.empty:
        return False

    # Dùng numpy nhanh hơn nhiều
    lows = future_df['low'].to_numpy(dtype=float)
    highs = future_df['high'].to_numpy(dtype=float)

    # Loại bỏ NaN
    mask = ~np.isnan(lows) & ~np.isnan(highs)
    lows = lows[mask]
    highs = highs[mask]

    if len(lows) == 0:
        return False

    # Normalize nếu có trường hợp high < low
    swap_mask = highs < lows
    lows[swap_mask], highs[swap_mask] = highs[swap_mask], lows[swap_mask]

    # Tạo intervals
    intervals = list(zip(lows, highs))

    # Sort intervals theo start
    intervals.sort(key=lambda x: x[0])

    # Merge intervals nhanh
    merged = []
    cur_start, cur_end = intervals[0]

    for s, e in intervals[1:]:
        if s <= cur_end:
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e

    merged.append((cur_start, cur_end))

    # Kiểm tra bao phủ toàn bộ gap
    for s, e in merged:
        if s <= gap_low and e >= gap_high:
            return True

    return False
