from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from .models import OHLCDataKCNDaily, OHLCDataRCNDaily
from django.utils import timezone
import os
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
import json
import openpyxl
from django.utils import timezone
import datetime
from coffee.helpers import calculate_and_set_stdev
class OHLCDataKCNDailyView:
    @login_required(login_url="login_cms")
    def list_data_kcn(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataKCNDaily.objects.all().order_by('-timestamp')
        
        for data in daily_datas:
            data.volatility_open = data.volatility_open * 100 if data.volatility_open is not None else None
            data.volatility_high = data.volatility_high * 100 if data.volatility_high is not None else None
            data.volatility_low = data.volatility_low * 100 if data.volatility_low is not None else None
            data.volatility_close = data.volatility_close * 100 if data.volatility_close is not None else None
            data.stdev_vol_open_20_days = data.stdev_vol_open_20_days * 100 if data.stdev_vol_open_20_days is not None else None
            data.stdev_vol_high_20_days = data.stdev_vol_high_20_days * 100 if data.stdev_vol_high_20_days is not None else None
            data.stdev_vol_low_20_days = data.stdev_vol_low_20_days * 100 if data.stdev_vol_low_20_days is not None else None
            data.stdev_vol_close_20_days = data.stdev_vol_close_20_days * 100 if data.stdev_vol_close_20_days is not None else None
        
        paginator = Paginator(daily_datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'daily_datas/kcn_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_kcn(request):
        if request.method == 'POST':
            try:
                # Lấy dữ liệu từ request.POST
                timestamp_str = request.POST.get('timestamp')
                # 1. Chuyển string thành object datetime "aware" (có múi giờ)
                input_date = timezone.make_aware(datetime.datetime.strptime(timestamp_str, '%Y-%m-%d'))
                open = float(request.POST.get('open'))
                high = float(request.POST.get('high'))
                low = float(request.POST.get('low'))
                close = float(request.POST.get('close'))
                
                # 2. Lấy bản ghi có timestamp lớn nhất nhưng PHẢI NHỎ HƠN ngày đang nhập
                kcn_daily_most_recent_date = OHLCDataKCNDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not kcn_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / kcn_daily_most_recent_date.open) - 1
                volatility_high = (high / kcn_daily_most_recent_date.high) - 1
                volatility_low = (low / kcn_daily_most_recent_date.low) - 1
                volatility_close = (close / kcn_daily_most_recent_date.close) - 1
                kcn_daily = OHLCDataKCNDaily(
                    timestamp=input_date,
                    open=open,
                    high=high,
                    low=low,
                    close=close,
                    volatility_open=volatility_open,
                    volatility_high=volatility_high,
                    volatility_low=volatility_low,
                    volatility_close=volatility_close,
                )
                calculate_and_set_stdev(kcn_daily)
                kcn_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-kcn-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/kcn_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_kcn(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                excel_file = request.FILES['excel_file']

                # Save the uploaded file temporarily
                temp_file_path = default_storage.save('temp/' + excel_file.name, excel_file)
                file_path = os.path.join(default_storage.location, temp_file_path)

                # Read Excel file
                df = pd.read_excel(
                    file_path,
                    header=0,
                    engine='openpyxl',
                    engine_kwargs={'data_only': True} 
                )

                df.columns = df.columns.str.strip().str.title()
                expected_columns = [
                    'Date', 'Open', 'High', 'Low', 'Close', 
                    'Volatility Open', 'Volatility High', 'Volatility Low', 'Volatility Close'
                ]
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Các cột thiếu trong file Excel: {", ".join(missing_columns)}'
                    }, status=400)

                imported_count = 0
                error_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        # 1. Tạo instance nhưng chưa save ngay để tính toán
                        kcn_daily, created = OHLCDataKCNDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        kcn_daily.open = row['Open']
                        kcn_daily.high = row['High']
                        kcn_daily.low = row['Low']
                        kcn_daily.close = row['Close']
                        kcn_daily.volatility_open = row['Volatility Open']
                        kcn_daily.volatility_high = row['Volatility High']
                        kcn_daily.volatility_low = row['Volatility Low']
                        kcn_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(kcn_daily)

                        # 3. Lưu vào database
                        kcn_daily.save()
                        imported_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Dòng {index + 1}: {str(e)}") 

                
                os.remove(file_path)    
                
                message = f'Import thành công {imported_count} bản ghi. {error_count} bản ghi lỗi: {errors}'

                if error_count > 0 and error_count < len(df):
                    return JsonResponse({
                        'status': 'warning',
                        'message': message,
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                    })
                elif error_count > 0 and error_count == len(df):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Import thất bại, tất cả các bản ghi đều lỗi',
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                    })
                elif error_count == 0:
                    return JsonResponse({
                        'status': 'success',
                        'message': message,
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                })

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi import file Excel: {str(e)}'
                }, status=400)

        return JsonResponse({
            'status': 'error',
            'message': 'Phương thức không được hỗ trợ hoặc thiếu file Excel'
        }, status=405)

    @login_required(login_url="login_cms")
    def export_excel(request):
        try:
            kcn_daily_datas = OHLCDataKCNDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for kcn_daily_data in kcn_daily_datas:
                # Format date fields to dd/mm/yyyy and convert to GMT +7
                def format_date(date_field):
                    if not date_field:
                        return ""
                    
                    # Nếu là datetime (có giờ phút giây)
                    if isinstance(date_field, datetime.datetime):
                        # Kiểm tra xem datetime đã có thông tin timezone (aware) chưa
                        if timezone.is_aware(date_field):
                            # Chuyển đổi chính xác sang GMT+7 trước khi format
                            date_field = timezone.localtime(date_field, target_timezone)
                        return date_field.strftime('%d/%m/%Y')
                    
                    # Nếu chỉ là object date thuần túy (không có giờ)
                    elif isinstance(date_field, datetime.date):
                        return date_field.strftime('%d/%m/%Y')
                    
                    # Nếu là string, ép kiểu và parse thử
                    try:
                        parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                        return parsed_date.strftime('%d/%m/%Y')
                    except ValueError:
                        return str(date_field)
                
                data.append({
                    'Date': format_date(kcn_daily_data.timestamp),
                    'Open': kcn_daily_data.open,
                    'High': kcn_daily_data.high,
                    'Low': kcn_daily_data.low,
                    'Close': kcn_daily_data.close,
                    'Volatility open': kcn_daily_data.volatility_open,
                    'Volatility high': kcn_daily_data.volatility_high,
                    'Volatility low': kcn_daily_data.volatility_low,
                    'Volatility close': kcn_daily_data.volatility_close,
                    'STDEV open': kcn_daily_data.stdev_vol_open_20_days if kcn_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': kcn_daily_data.stdev_vol_high_20_days if kcn_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': kcn_daily_data.stdev_vol_low_20_days if kcn_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': kcn_daily_data.stdev_vol_close_20_days if kcn_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"kcn_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Tạo Excel file với cấu trúc giống file mẫu
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                # Tạo workbook
                workbook = writer.book
                
                worksheet = workbook.create_sheet("Data", 0)
                
                # Xóa sheet mặc định nếu có
                if 'Sheet' in workbook.sheetnames:
                    del workbook['Sheet']
                
                # Dòng 3: Headers
                headers = [
                    'Date', 'Open', 'High', 'Low', 'Close', 
                    'Volatility open', 'Volatility high', 'Volatility low', 'Volatility close',
                    'STDEV open', 'STDEV high', 'STDEV low', 'STDEV close'
                ]
                
                for col, header in enumerate(headers, 1):
                    cell = worksheet.cell(row=1, column=col, value=header)
                    # Có thể thêm style cho header nếu cần
                    cell.font = openpyxl.styles.Font(bold=True)
                
                # Ghi dữ liệu từ DataFrame (bắt đầu từ dòng 2)
                if not df.empty:
                    for row_idx, row_data in enumerate(df.itertuples(), 2):
                        for col_idx, value in enumerate(row_data[1:], 1):  # Bỏ qua index
                            worksheet.cell(row=row_idx, column=col_idx, value=value)
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Export Excel thất bại: {str(e)}'
            }, status=400)
    @login_required(login_url="login_cms")
    def delete_data_kcn(request, pk):
        data = get_object_or_404(OHLCDataKCNDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu KCN thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu KCN: {str(e)}',
                }, status=400)

class OHLCDataRCNDailyView:
    @login_required(login_url="login_cms")
    def list_data_rcn(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataRCNDaily.objects.all().order_by('-timestamp')
        
        for data in daily_datas:
            data.volatility_open = data.volatility_open * 100
            data.volatility_high = data.volatility_high * 100
            data.volatility_low = data.volatility_low * 100
            data.volatility_close = data.volatility_close * 100
            data.stdev_vol_open_20_days = data.stdev_vol_open_20_days * 100 if data.stdev_vol_open_20_days is not None else None
            data.stdev_vol_high_20_days = data.stdev_vol_high_20_days * 100 if data.stdev_vol_high_20_days is not None else None
            data.stdev_vol_low_20_days = data.stdev_vol_low_20_days * 100 if data.stdev_vol_low_20_days is not None else None
            data.stdev_vol_close_20_days = data.stdev_vol_close_20_days * 100 if data.stdev_vol_close_20_days is not None else None
        
        paginator = Paginator(daily_datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'daily_datas/rcn_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_rcn(request):
        if request.method == 'POST':
            try:
                # Lấy dữ liệu từ request.POST
                timestamp_str = request.POST.get('timestamp')
                # 1. Chuyển string thành object datetime "aware" (có múi giờ)
                input_date = timezone.make_aware(datetime.datetime.strptime(timestamp_str, '%Y-%m-%d'))
                open = float(request.POST.get('open'))
                high = float(request.POST.get('high'))
                low = float(request.POST.get('low'))
                close = float(request.POST.get('close'))
                
                # 2. Lấy bản ghi có timestamp lớn nhất nhưng PHẢI NHỎ HƠN ngày đang nhập
                rcn_daily_most_recent_date = OHLCDataRCNDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not rcn_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / rcn_daily_most_recent_date.open) - 1
                volatility_high = (high / rcn_daily_most_recent_date.high) - 1
                volatility_low = (low / rcn_daily_most_recent_date.low) - 1
                volatility_close = (close / rcn_daily_most_recent_date.close) - 1
                rcn_daily = OHLCDataRCNDaily(
                    timestamp=input_date,
                    open=open,
                    high=high,
                    low=low,
                    close=close,
                    volatility_open=volatility_open,
                    volatility_high=volatility_high,
                    volatility_low=volatility_low,
                    volatility_close=volatility_close,
                )
                calculate_and_set_stdev(rcn_daily)
                rcn_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-rcn-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/rcn_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_rcn(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                excel_file = request.FILES['excel_file']

                # Save the uploaded file temporarily
                temp_file_path = default_storage.save('temp/' + excel_file.name, excel_file)
                file_path = os.path.join(default_storage.location, temp_file_path)

                # Read Excel file
                df = pd.read_excel(
                    file_path,
                    header=0,
                    engine='openpyxl',
                    engine_kwargs={'data_only': True} 
                )

                df.columns = df.columns.str.strip().str.title()
                expected_columns = [
                    'Date', 'Open', 'High', 'Low', 'Close', 
                    'Volatility Open', 'Volatility High', 'Volatility Low', 'Volatility Close'
                ]
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Các cột thiếu trong file Excel: {", ".join(missing_columns)}'
                    }, status=400)

                imported_count = 0
                error_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        # 1. Tạo instance nhưng chưa save ngay để tính toán
                        rcn_daily, created = OHLCDataRCNDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        rcn_daily.open = row['Open']
                        rcn_daily.high = row['High']
                        rcn_daily.low = row['Low']
                        rcn_daily.close = row['Close']
                        rcn_daily.volatility_open = row['Volatility Open']
                        rcn_daily.volatility_high = row['Volatility High']
                        rcn_daily.volatility_low = row['Volatility Low']
                        rcn_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(rcn_daily)

                        # 3. Lưu vào database
                        rcn_daily.save()
                        imported_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Dòng {index + 1}: {str(e)}") 

                
                os.remove(file_path)    
                
                message = f'Import thành công {imported_count} bản ghi. {error_count} bản ghi lỗi: {errors}'

                if error_count > 0 and error_count < len(df):
                    return JsonResponse({
                        'status': 'warning',
                        'message': message,
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                    })
                elif error_count > 0 and error_count == len(df):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Import thất bại, tất cả các bản ghi đều lỗi',
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                    })
                elif error_count == 0:
                    return JsonResponse({
                        'status': 'success',
                        'message': message,
                        'imported_count': imported_count,
                        'error_count': error_count,
                        'errors': errors
                })

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi import file Excel: {str(e)}'
                }, status=400)

        return JsonResponse({
            'status': 'error',
            'message': 'Phương thức không được hỗ trợ hoặc thiếu file Excel'
        }, status=405)

    @login_required(login_url="login_cms")
    def export_excel(request):
        try:
            rcn_daily_datas = OHLCDataRCNDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for rcn_daily_data in rcn_daily_datas:
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
                        return date_field.strftime('%d/%m/%Y')
                    
                    # Nếu chỉ là object date thuần túy (không có giờ)
                    elif isinstance(date_field, datetime.date):
                        return date_field.strftime('%d/%m/%Y')
                    
                    # Nếu là string, ép kiểu và parse thử
                    try:
                        parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                        return parsed_date.strftime('%d/%m/%Y')
                    except ValueError:
                        return str(date_field)
                
                data.append({
                    'Date': format_date(rcn_daily_data.timestamp),
                    'Open': rcn_daily_data.open,
                    'High': rcn_daily_data.high,
                    'Low': rcn_daily_data.low,
                    'Close': rcn_daily_data.close,
                    'Volatility open': rcn_daily_data.volatility_open,
                    'Volatility high': rcn_daily_data.volatility_high,
                    'Volatility low': rcn_daily_data.volatility_low,
                    'Volatility close': rcn_daily_data.volatility_close,
                    'STDEV open': rcn_daily_data.stdev_vol_open_20_days if rcn_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': rcn_daily_data.stdev_vol_high_20_days if rcn_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': rcn_daily_data.stdev_vol_low_20_days if rcn_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': rcn_daily_data.stdev_vol_close_20_days if rcn_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"rcn_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Tạo Excel file với cấu trúc giống file mẫu
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                # Tạo workbook
                workbook = writer.book
                
                worksheet = workbook.create_sheet("Data", 0)
                
                # Xóa sheet mặc định nếu có
                if 'Sheet' in workbook.sheetnames:
                    del workbook['Sheet']
                
                # Dòng 3: Headers
                headers = [
                    'Date', 'Open', 'High', 'Low', 'Close', 
                    'Volatility open', 'Volatility high', 'Volatility low', 'Volatility close',
                    'STDEV open', 'STDEV high', 'STDEV low', 'STDEV close',
                ]
                
                for col, header in enumerate(headers, 1):
                    cell = worksheet.cell(row=1, column=col, value=header)
                    # Có thể thêm style cho header nếu cần
                    cell.font = openpyxl.styles.Font(bold=True)
                
                # Ghi dữ liệu từ DataFrame (bắt đầu từ dòng 2)
                if not df.empty:
                    for row_idx, row_data in enumerate(df.itertuples(), 2):
                        for col_idx, value in enumerate(row_data[1:], 1):  # Bỏ qua index
                            worksheet.cell(row=row_idx, column=col_idx, value=value)
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Export Excel thất bại: {str(e)}'
            }, status=400)

    @login_required(login_url="login_cms")
    def delete_data_rcn(request, pk):
        data = get_object_or_404(OHLCDataRCNDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu RCN thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu RCN: {str(e)}',
                }, status=400)

def clean_percnentage(value):
    if pd.isna(value) or value == '':
        return None  # Hoặc None nếu field trong Model cho phép null
    
    # Chuyển về string để xử lý dấu %
    str_val = str(value).strip()
    
    if '%' in str_val:
        # Nếu có dấu %: Xóa %, chuyển sang float rồi chia 100
        return float(str_val.replace('%', '')) / 100
    else:
        # Nếu không có dấu %: Kiểm tra xem nó là 35.88 hay 0.3588
        val = float(str_val)
        # Nếu giá trị > 1 (ví dụ 35.88) thì chia 100, nếu đã là 0.3588 thì giữ nguyên
        # (Lưu ý: Logic này tùy thuộc vào việc file của bạn ghi số nguyên hay số thập phân)
        return val / 100 if val > 1 else val