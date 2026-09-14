import os
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings # Import settings
from django.db.models import Max
import numpy as np
import re
import pandas as pd
import json
import openpyxl
from django.shortcuts import render
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
import datetime
from chartOHLC.models import OHLCDataKC, OHLCDataRC
from marketAgent.models import GapKCData, GapRCData
from django.utils import timezone # Import thư viện timezone của Django
import pytz
from django.core.paginator import Paginator
from django.db.models import Q
# from dailyOHLC.models import OHLCDataKCZDaily, OHLCDataRCXDaily
# from coffee.helpers import calculate_and_set_stdev
class TVGetDatafeedView(View):
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                symbol_text = request.POST.get('symbol', '')
                n_bars_input = request.POST.get('n_bars', 10000)
                interval_input_text = request.POST.get('interval', '')
                save_change = request.POST.get('save_change', 'false')
                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)
                
                if interval_input_text == "in_daily":
                    interval_input = Interval.in_daily
                elif interval_input_text == "in_1_minute":
                    interval_input = Interval.in_1_minute
                elif interval_input_text == "in_5_minute":
                    interval_input = Interval.in_5_minute
                elif interval_input_text == "in_monthly":
                    interval_input = Interval.in_monthly

                if symbol_text == "KCH2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCH2026":
                    exchange_text = "ICEEUR"

                elif symbol_text == "KCK2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCK2026":
                    exchange_text = "ICEEUR"
                
                elif symbol_text == "KCN2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCN2026":
                    exchange_text = "ICEEUR"

                elif symbol_text == "KCU2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCU2026":
                    exchange_text = "ICEEUR"

                elif symbol_text == "KCZ2026":
                    exchange_text = "ICEUS"

                elif symbol_text == "RCX2026":
                    exchange_text = "ICEEUR"

                elif symbol_text == "VNFER":
                    exchange_text = "ECONOMICS"

                elif symbol_text == "USOIL":
                    exchange_text = "TVC"

                elif symbol_text == "UKOIL":
                    exchange_text = "TVC"

                elif symbol_text == "RC1!":
                    exchange_text = "ICEEUR"
                elif symbol_text == "RC2!":
                    exchange_text = "ICEEUR"

                elif symbol_text == "KC1!":
                    exchange_text = "ICEUS"
                elif symbol_text == "KC2!":
                    exchange_text = "ICEUS"
                
                elif symbol_text == "USDVND":
                    exchange_text = "FX_IDC"

                elif symbol_text == "UR2!":
                    exchange_text = "ZCE"
                
                elif symbol_text == "BDI":
                    exchange_text = "INDEX"
                else:
                    exchange_text = "ICEUS"

                print("symbol_text:", symbol_text)
                print("exchange_text:", exchange_text)
                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=interval_input,
                    n_bars=int(n_bars_input)
                )
                
                if save_change == 'true' and df is not None:
                    df = df.reset_index().drop_duplicates(subset=['datetime'], keep='last')
                    # Chuẩn bị danh sách objects
                    objs = []
                    for _, row in df.iterrows():
                        naive_dt = row['datetime']
                        timezone_dt = timezone.make_aware(naive_dt, pytz.timezone('Asia/Ho_Chi_Minh')).replace(microsecond=0)
                        model_class = OHLCDataKC if symbol_text in ["KCH2026", "KCK2026", "KCU2026", "KCN2026", "KCZ2026"] else OHLCDataRC
                        objs.append(model_class(
                            symbol=symbol_text,
                            timestamp=timezone_dt,
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            volume=row['volume']
                        ))

                    # Thực hiện upsert (update if conflict) hàng loạt
                    if objs:
                        model_class = objs[0].__class__
                        model_class.objects.bulk_create(
                            objs,
                            update_conflicts=True,
                            unique_fields=['symbol', 'timestamp'],
                            update_fields=['open', 'high', 'low', 'close', 'volume']
                        )
                # if save_change == 'true':
                #     if df is not None:
                #         df = df.reset_index()
                #         # Sắp xếp theo thời gian tăng dần để đảm bảo tính toán đúng trình tự
                #         df = df.sort_values('datetime')
                        
                #         # Xác định Model dựa trên symbol_text
                #         model_class = None
                #         if symbol_text == "KCZ2026":
                #             model_class = OHLCDataKCZDaily
                #         elif symbol_text == "RCX2026":
                #             model_class = OHLCDataRCXDaily

                #         if model_class:
                #             for _, row in df.iterrows():
                #                 naive_dt = row['datetime']
                #                 timezone_dt = timezone.make_aware(naive_dt, pytz.timezone('Asia/Ho_Chi_Minh'))
                                
                #                 # Tìm bản ghi gần nhất có timestamp nhỏ hơn ngày đang xử lý
                #                 prev_record = model_class.objects.filter(
                #                     timestamp__lt=timezone_dt
                #                 ).order_by('-timestamp').first()

                #                 # Tính toán Volatility
                #                 if prev_record:
                #                     v_open = (row['open'] / prev_record.open) - 1
                #                     v_high = (row['high'] / prev_record.high) - 1
                #                     v_low = (row['low'] / prev_record.low) - 1
                #                     v_close = (row['close'] / prev_record.close) - 1
                #                 else:
                #                     # Nếu là bản ghi đầu tiên, để giá trị mặc định là 0 hoặc None
                #                     v_open = v_high = v_low = v_close = 0

                #                 # Update hoặc Create bản ghi
                #                 obj, created = model_class.objects.update_or_create(
                #                     timestamp=timezone_dt,
                #                     defaults={
                #                         'open': row['open'], 
                #                         'high': row['high'],
                #                         'low': row['low'], 
                #                         'close': row['close'],
                #                         'volatility_open': v_open,
                #                         'volatility_high': v_high,
                #                         'volatility_low': v_low,
                #                         'volatility_close': v_close,
                #                     }
                #                 )
                                
                #                 # Tính toán và gán STDEV (hàm này sẽ lưu record sau khi tính)
                #                 calculate_and_set_stdev(obj)
                #                 obj.save()
                        
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

def is_gap_filled_by_intervals(gap_low, gap_high, future_df):
    """
    Kiểm tra gap đã fill hoàn toàn bằng union của intervals future.
    Đã tối ưu hiệu năng: không dùng iterrows, dùng numpy + merge intervals nhanh.
    """
    if future_df.empty:
        return False

    lows = future_df['low'].to_numpy(dtype=float)
    highs = future_df['high'].to_numpy(dtype=float)

    mask = ~np.isnan(lows) & ~np.isnan(highs)
    lows = lows[mask]
    highs = highs[mask]

    if len(lows) == 0:
        return False

    swap_mask = highs < lows
    lows[swap_mask], highs[swap_mask] = highs[swap_mask], lows[swap_mask]

    intervals = list(zip(lows, highs))
    intervals.sort(key=lambda x: x[0])

    merged = []
    cur_start, cur_end = intervals[0]

    for s, e in intervals[1:]:
        if s <= cur_end:
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e

    merged.append((cur_start, cur_end))

    for s, e in merged:
        if s <= gap_low and e >= gap_high:
            return True

    return False


def check_gap_fill_details(gap_low, gap_high, future_df):
    """
    Kiểm tra gap đã đóng chưa và xác định mốc thời gian (timestamp) chính xác khi gap được đóng.
    Sử dụng Binary Search trên future_df để tối ưu tốc độ tìm kiếm.
    """
    if not is_gap_filled_by_intervals(gap_low, gap_high, future_df):
        return False, None

    low_idx = 1
    high_idx = len(future_df)
    filled_time = None

    while low_idx <= high_idx:
        mid = (low_idx + high_idx) // 2
        sub_df = future_df.iloc[:mid]

        if is_gap_filled_by_intervals(gap_low, gap_high, sub_df):
            filled_time = future_df.iloc[mid - 1]['datetime']
            high_idx = mid - 1
        else:
            low_idx = mid + 1

    return True, filled_time

def make_tz_aware(dt):
    """Chuyển đổi Naive Datetime sang Aware Datetime dựa theo TIME_ZONE trong settings.py."""
    if dt is None:
        return None
    
    # Nếu là Timestamp của Pandas, chuyển về Python datetime
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
        
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt

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
                elif interval_input_text == "in_5_minute":
                    interval_input = Interval.in_5_minute

                if symbol_text == "":
                    return JsonResponse({
                        "status": "error",
                        "message": "Symbol is required"
                    }, status=400)

                if symbol_text == "KCH2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCH2026":
                    exchange_text = "ICEEUR"
                elif symbol_text == "KCK2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCK2026":
                    exchange_text = "ICEEUR"
                elif symbol_text == "KCN2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCN2026":
                    exchange_text = "ICEEUR"
                elif symbol_text == "KCU2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCU2026":
                    exchange_text = "ICEEUR"
                elif symbol_text == "KCZ2026":
                    exchange_text = "ICEUS"
                elif symbol_text == "RCX2026":
                    exchange_text = "ICEEUR"
                elif symbol_text == "KC1!":
                    exchange_text = "ICEUS"
                elif symbol_text == "KC2!":
                    exchange_text = "ICEUS"
                else:
                    exchange_text = "ICEUS"

                # Xác định Model Postgres tương ứng với Symbol
                if symbol_text.startswith("KC"):
                    TargetModel = GapKCData
                elif symbol_text.startswith("RC"):
                    TargetModel = GapRCData
                    
                df = tv.get_hist(
                    symbol=symbol_text,
                    exchange=exchange_text,
                    interval=interval_input,
                    n_bars=int(n_bars_input)
                )

                df = df.copy().reset_index()

                # Đảm bảo cột 'datetime' tồn tại và đúng kiểu datetime64[ns] không chứa timezone
                if 'datetime' not in df.columns and 'index' in df.columns:
                    df.rename(columns={'index': 'datetime'}, inplace=True)

                df['datetime'] = pd.to_datetime(df['datetime'])
                if df['datetime'].dt.tz is not None:
                    df['datetime'] = df['datetime'].dt.tz_localize(None)

                # 1. Kiểm tra và cập nhật các GAP CŨ trong PostgreSQL có filled = False
                existing_unfilled_gaps = TargetModel.objects.filter(symbol=symbol_text, filled=False)
                for db_gap in existing_unfilled_gaps:
                    if db_gap.timestamp:
                        # Chuẩn hóa timestamp từ DB về pd.Timestamp không timezone để so sánh với df
                        db_ts = pd.to_datetime(db_gap.timestamp)
                        if db_ts.tzinfo is not None:
                            db_ts = db_ts.tz_localize(None)

                        future_df_db = df[df["datetime"] > db_ts]
                        is_filled, time_filled = check_gap_fill_details(db_gap.gap_low, db_gap.gap_high, future_df_db)
                        if is_filled:
                            db_gap.filled = True
                            db_gap.time_filled = make_tz_aware(time_filled)
                            db_gap.save()

                # 2. Tìm các Gap trong dữ liệu hiện tại
                gaps = []
                for i in range(1, len(df)):
                    prev_high = df.loc[i-1, 'high']
                    prev_low = df.loc[i-1, 'low']
                    curr_high = df.loc[i, 'high']
                    curr_low  = df.loc[i, 'low']
                    bar_time  = df.loc[i, 'datetime']

                    # GAP UP
                    if curr_low > prev_high:
                        gaps.append({
                            "index": i,
                            "time": bar_time,
                            "type": "GAP_UP",
                            "gap_low": prev_high,
                            "gap_high": curr_low,
                            "gap_size": curr_low - prev_high,
                            "filled": False,
                            "time_filled": None
                        })

                    # GAP DOWN
                    elif curr_high < prev_low:
                        gaps.append({
                            "index": i,
                            "time": bar_time,
                            "type": "GAP_DOWN",
                            "gap_low": curr_high,
                            "gap_high": prev_low,
                            "gap_size": prev_low - curr_high,
                            "filled": False,
                            "time_filled": None
                        })

                # 3. Kiểm tra Gap mới đã đóng chưa & Lưu/Cập nhật vào PostgreSQL (Tránh trùng lặp)
                for g in gaps:
                    low = g["gap_low"]
                    high = g["gap_high"]
                    g_time = g["time"]

                    future = df[df["datetime"] > g_time]
                    filled, time_filled = check_gap_fill_details(low, high, future)

                    g["filled"] = filled
                    g["time_filled"] = time_filled

                    g_time_val = make_tz_aware(g_time)
                    time_filled_val = make_tz_aware(time_filled)

                    # Tránh lưu trùng 1 gap bằng cách filter theo (symbol, timestamp)
                    existing_gap = TargetModel.objects.filter(
                        symbol=symbol_text,
                        timestamp=g_time_val
                    ).first()

                    if existing_gap:
                        existing_gap.type = g["type"]
                        existing_gap.gap_low = g["gap_low"]
                        existing_gap.gap_high = g["gap_high"]
                        existing_gap.gap_size = g["gap_size"]
                        existing_gap.filled = g["filled"]
                        existing_gap.timestamp = g_time_val
                        existing_gap.time_filled = time_filled_val
                        existing_gap.save()
                    else:
                        target_index = g["index"]
                        if TargetModel.objects.filter(index=target_index).exists():
                            max_idx = TargetModel.objects.aggregate(Max('index'))['index__max'] or 0
                            target_index = max_idx + 1

                        TargetModel.objects.create(
                            index=target_index,
                            symbol=symbol_text,
                            timestamp=g_time_val,
                            type=g["type"],
                            gap_low=g["gap_low"],
                            gap_high=g["gap_high"],
                            gap_size=g["gap_size"],
                            filled=g["filled"],
                            time_filled=time_filled_val
                        )

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

class GapKCDataView:
    @login_required(login_url="login_cms")
    def list_gap_kc(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        datas = GapKCData.objects.all().order_by('-timestamp')
              
        paginator = Paginator(datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'market-agent/gap_kc_list.html', {'datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})

    @login_required(login_url="login_cms")
    def export_excel(request):
        try:
            gapKC = GapKCData.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data_export = []
            for data in gapKC:
                # Format date fields to dd/mm/yyyy
                def format_date(date_field):
                    if not date_field:
                        return ""
                    
                    # Nếu là datetime (có giờ phút giây)
                    if isinstance(date_field, datetime.datetime):
                        # Kiểm tra xem datetime đã có thông tin timezone (aware) chưa
                        if timezone.is_aware(date_field):
                            # Chuyển đổi chính xác sang GMT+7 trước khi format
                            date_field = timezone.localtime(date_field, target_timezone)
                        return date_field.strftime('%d/%m/%Y %H:%M')
                    
                    # Nếu chỉ là object date thuần túy (không có giờ)
                    elif isinstance(date_field, datetime.date):
                        return date_field.strftime('%d/%m/%Y %H:%M')
                    
                    # Nếu là string, ép kiểu và parse thử
                    try:
                        parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                        return parsed_date.strftime('%d/%m/%Y %H:%M')
                    except ValueError:
                        return str(date_field)
                
                data_export.append({
                    'Symbol': data.symbol,
                    'Timestamp': format_date(data.timestamp),
                    'Type': data.type,
                    'Gap low': data.gap_low,
                    'Gap high': data.gap_high,
                    'Gap size': data.gap_size,
                    'Filled': data.filled,
                    'Time filled': format_date(data.time_filled) if data.time_filled else '',
                })
            
            df = pd.DataFrame(data_export)
            output_file = f"gap_kc_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
            output_path = os.path.join(settings.MEDIA_ROOT, 'tvdatafeed', output_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_excel(output_path, index=False)
            return JsonResponse({
                "status": "success",
                "message": "Export Excel thành công",
                "result": f"/media/tvdatafeed/{output_file}"
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Export Excel thất bại: {str(e)}'
            }, status=400)

class GapRCDataView:
    @login_required(login_url="login_cms")
    def list_gap_rc(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        datas = GapRCData.objects.all().order_by('-timestamp')
              
        paginator = Paginator(datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'market-agent/gap_rc_list.html', {'datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})

    @login_required(login_url="login_cms")
    def export_excel(request):
        try:
            gapRC = GapRCData.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data_export = []
            for data in gapRC:
                # Format date fields to dd/mm/yyyy
                def format_date(date_field):
                    if not date_field:
                        return ""
                    
                    # Nếu là datetime (có giờ phút giây)
                    if isinstance(date_field, datetime.datetime):
                        # Kiểm tra xem datetime đã có thông tin timezone (aware) chưa
                        if timezone.is_aware(date_field):
                            # Chuyển đổi chính xác sang GMT+7 trước khi format
                            date_field = timezone.localtime(date_field, target_timezone)
                        return date_field.strftime('%d/%m/%Y %H:%M')
                    
                    # Nếu chỉ là object date thuần túy (không có giờ)
                    elif isinstance(date_field, datetime.date):
                        return date_field.strftime('%d/%m/%Y %H:%M')
                    
                    # Nếu là string, ép kiểu và parse thử
                    try:
                        parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                        return parsed_date.strftime('%d/%m/%Y %H:%M')
                    except ValueError:
                        return str(date_field)
                
                data_export.append({
                    'Symbol': data.symbol,
                    'Timestamp': format_date(data.timestamp),
                    'Type': data.type,
                    'Gap low': data.gap_low,
                    'Gap high': data.gap_high,
                    'Gap size': data.gap_size,
                    'Filled': data.filled,
                    'Time filled': format_date(data.time_filled) if data.time_filled else '',
                })
            
            df = pd.DataFrame(data_export)
            output_file = f"gap_rc_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
            output_path = os.path.join(settings.MEDIA_ROOT, 'tvdatafeed', output_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_excel(output_path, index=False)
            return JsonResponse({
                "status": "success",
                "message": "Export Excel thành công",
                "result": f"/media/tvdatafeed/{output_file}"
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Export Excel thất bại: {str(e)}'
            }, status=400)
     