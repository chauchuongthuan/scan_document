from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from .models import OHLCDataKCZDaily, OHLCDataRCXDaily
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
class OHLCDataKCZDailyView:
    @login_required(login_url="login_cms")
    def list_data_kcz(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataKCZDaily.objects.all().order_by('-timestamp')
        
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

        return render(request, 'daily_datas/kcz_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_kcz(request):
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
                kcz_daily_most_recent_date = OHLCDataKCZDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not kcz_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / kcz_daily_most_recent_date.open) - 1
                volatility_high = (high / kcz_daily_most_recent_date.high) - 1
                volatility_low = (low / kcz_daily_most_recent_date.low) - 1
                volatility_close = (close / kcz_daily_most_recent_date.close) - 1
                kcz_daily = OHLCDataKCZDaily(
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
                calculate_and_set_stdev(kcz_daily)
                kcz_daily.save()
                print("kcz_daily:", kcz_daily)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-kcz-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/kcz_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_kcz(request):
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
                        kcz_daily, created = OHLCDataKCZDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        kcz_daily.open = row['Open']
                        kcz_daily.high = row['High']
                        kcz_daily.low = row['Low']
                        kcz_daily.close = row['Close']
                        kcz_daily.volatility_open = row['Volatility Open']
                        kcz_daily.volatility_high = row['Volatility High']
                        kcz_daily.volatility_low = row['Volatility Low']
                        kcz_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(kcz_daily)

                        # 3. Lưu vào database
                        kcz_daily.save()
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
            kcz_daily_datas = OHLCDataKCZDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for kcz_daily_data in kcz_daily_datas:
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
                    'Date': format_date(kcz_daily_data.timestamp),
                    'Open': kcz_daily_data.open,
                    'High': kcz_daily_data.high,
                    'Low': kcz_daily_data.low,
                    'Close': kcz_daily_data.close,
                    'Volatility open': kcz_daily_data.volatility_open,
                    'Volatility high': kcz_daily_data.volatility_high,
                    'Volatility low': kcz_daily_data.volatility_low,
                    'Volatility close': kcz_daily_data.volatility_close,
                    'STDEV open': kcz_daily_data.stdev_vol_open_20_days if kcz_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': kcz_daily_data.stdev_vol_high_20_days if kcz_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': kcz_daily_data.stdev_vol_low_20_days if kcz_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': kcz_daily_data.stdev_vol_close_20_days if kcz_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"kcz_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
    def delete_data_kcz(request, pk):
        data = get_object_or_404(OHLCDataKCZDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu KCZ thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu KCZ: {str(e)}',
                }, status=400)

class OHLCDataRCXDailyView:
    @login_required(login_url="login_cms")
    def list_data_rcx(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataRCXDaily.objects.all().order_by('-timestamp')
        
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

        return render(request, 'daily_datas/rcx_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_rcx(request):
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
                rcx_daily_most_recent_date = OHLCDataRCXDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not rcx_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / rcx_daily_most_recent_date.open) - 1
                volatility_high = (high / rcx_daily_most_recent_date.high) - 1
                volatility_low = (low / rcx_daily_most_recent_date.low) - 1
                volatility_close = (close / rcx_daily_most_recent_date.close) - 1
                rcx_daily = OHLCDataRCXDaily(
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
                calculate_and_set_stdev(rcx_daily)
                rcx_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-rcx-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/rcx_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_rcx(request):
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
                        rcx_daily, created = OHLCDataRCXDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        rcx_daily.open = row['Open']
                        rcx_daily.high = row['High']
                        rcx_daily.low = row['Low']
                        rcx_daily.close = row['Close']
                        rcx_daily.volatility_open = row['Volatility Open']
                        rcx_daily.volatility_high = row['Volatility High']
                        rcx_daily.volatility_low = row['Volatility Low']
                        rcx_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(rcx_daily)

                        # 3. Lưu vào database
                        rcx_daily.save()
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
            rcx_daily_datas = OHLCDataRCXDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for rcx_daily_data in rcx_daily_datas:
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
                    'Date': format_date(rcx_daily_data.timestamp),
                    'Open': rcx_daily_data.open,
                    'High': rcx_daily_data.high,
                    'Low': rcx_daily_data.low,
                    'Close': rcx_daily_data.close,
                    'Volatility open': rcx_daily_data.volatility_open,
                    'Volatility high': rcx_daily_data.volatility_high,
                    'Volatility low': rcx_daily_data.volatility_low,
                    'Volatility close': rcx_daily_data.volatility_close,
                    'STDEV open': rcx_daily_data.stdev_vol_open_20_days if rcx_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': rcx_daily_data.stdev_vol_high_20_days if rcx_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': rcx_daily_data.stdev_vol_low_20_days if rcx_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': rcx_daily_data.stdev_vol_close_20_days if rcx_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"rcx_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
    def delete_data_rcx(request, pk):
        data = get_object_or_404(OHLCDataRCXDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu RCX thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu RCX: {str(e)}',
                }, status=400)

def clean_percxentage(value):
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