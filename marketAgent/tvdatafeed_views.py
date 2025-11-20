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

class TVGetDatafeedView(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                symbol_text = request.POST.get('symbol', '')
                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)
                
                if symbol_text == "KCH2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCF2026":
                    exchange_text = "ICEEUR"
                else:
                    return JsonResponse({
                        "status": "error",
                        "message": "Exchange is required"
                    }, status=400)
                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=Interval.in_1_minute,
                    n_bars=100000
                )
                print(df)
                output_file = f"data_{symbol_text}.xlsx"
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
                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)
                
                if symbol_text == "KCH2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCF2026":
                    exchange_text = "ICEEUR"
                else:
                    return JsonResponse({
                        "status": "error",
                        "message": "Exchange is required"
                    }, status=400)
                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=Interval.in_1_minute,
                    n_bars=100000
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

                    for _, row in future.iterrows():
                        if row["low"] <= high and row["high"] >= low:
                            g["filled"] = True
                            break
                
                unfilled = [g for g in gaps if g["filled"] == False]
                unfilled_gaps = pd.DataFrame(unfilled)
                output_file = f"unfilled_gaps_{symbol_text}.xlsx"
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
