from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from .models import OHLCDataKCDaily, OHLCDataRCDaily, OHLCDataKCKDaily, OHLCDataRCKDaily, OHLCDataKCNDaily, OHLCDataRCNDaily, OHLCDataKCUDaily, OHLCDataRCUDaily, ImpliedVolatility
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
class OHLCDataKCDailyView:
    @login_required(login_url="login_cms")
    def list_data_kc(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataKCDaily.objects.all().order_by('-timestamp')
        
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

        return render(request, 'daily_datas/kc_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_kc(request):
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
                kc_daily_most_recent_date = OHLCDataKCDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not kc_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / kc_daily_most_recent_date.open) - 1
                volatility_high = (high / kc_daily_most_recent_date.high) - 1
                volatility_low = (low / kc_daily_most_recent_date.low) - 1
                volatility_close = (close / kc_daily_most_recent_date.close) - 1
                kc_daily = OHLCDataKCDaily(
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
                calculate_and_set_stdev(kc_daily)
                kc_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-kc-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/kc_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_kc(request):
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
                        kc_daily, created = OHLCDataKCDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        kc_daily.open = row['Open']
                        kc_daily.high = row['High']
                        kc_daily.low = row['Low']
                        kc_daily.close = row['Close']
                        kc_daily.volatility_open = row['Volatility Open']
                        kc_daily.volatility_high = row['Volatility High']
                        kc_daily.volatility_low = row['Volatility Low']
                        kc_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(kc_daily)

                        # 3. Lưu vào database
                        kc_daily.save()
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
            kc_daily_datas = OHLCDataKCDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for kc_daily_data in kc_daily_datas:
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
                    'Date': format_date(kc_daily_data.timestamp),
                    'Open': kc_daily_data.open,
                    'High': kc_daily_data.high,
                    'Low': kc_daily_data.low,
                    'Close': kc_daily_data.close,
                    'Volatility open': kc_daily_data.volatility_open,
                    'Volatility high': kc_daily_data.volatility_high,
                    'Volatility low': kc_daily_data.volatility_low,
                    'Volatility close': kc_daily_data.volatility_close,
                    'STDEV open': kc_daily_data.stdev_vol_open_20_days if kc_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': kc_daily_data.stdev_vol_high_20_days if kc_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': kc_daily_data.stdev_vol_low_20_days if kc_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': kc_daily_data.stdev_vol_close_20_days if kc_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"kc_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
    def delete_data_kc(request, pk):
        data = get_object_or_404(OHLCDataKCDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu KC thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu KC: {str(e)}',
                }, status=400)

class OHLCDataRCDailyView:
    @login_required(login_url="login_cms")
    def list_data_rc(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = OHLCDataRCDaily.objects.all().order_by('-timestamp')
        
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

        return render(request, 'daily_datas/rc_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_rc(request):
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
                rc_daily_most_recent_date = OHLCDataRCDaily.objects.filter(
                    timestamp__lt=input_date
                ).order_by('-timestamp').first()
                if not rc_daily_most_recent_date:
                    return JsonResponse({'error': 'No previous data found'}, status=400)
                volatility_open = (open / rc_daily_most_recent_date.open) - 1
                volatility_high = (high / rc_daily_most_recent_date.high) - 1
                volatility_low = (low / rc_daily_most_recent_date.low) - 1
                volatility_close = (close / rc_daily_most_recent_date.close) - 1
                rc_daily = OHLCDataRCDaily(
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
                calculate_and_set_stdev(rc_daily)
                rc_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-ohlc-rc-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/rc_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_rc(request):
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
                        rc_daily, created = OHLCDataRCDaily.objects.get_or_create(
                            timestamp=row['Date']
                        )
                        
                        rc_daily.open = row['Open']
                        rc_daily.high = row['High']
                        rc_daily.low = row['Low']
                        rc_daily.close = row['Close']
                        rc_daily.volatility_open = row['Volatility Open']
                        rc_daily.volatility_high = row['Volatility High']
                        rc_daily.volatility_low = row['Volatility Low']
                        rc_daily.volatility_close = row['Volatility Close']

                        # 2. Gọi hàm tính toán STDEV
                        calculate_and_set_stdev(rc_daily)

                        # 3. Lưu vào database
                        rc_daily.save()
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
            rc_daily_datas = OHLCDataRCDaily.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for rc_daily_data in rc_daily_datas:
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
                    'Date': format_date(rc_daily_data.timestamp),
                    'Open': rc_daily_data.open,
                    'High': rc_daily_data.high,
                    'Low': rc_daily_data.low,
                    'Close': rc_daily_data.close,
                    'Volatility open': rc_daily_data.volatility_open,
                    'Volatility high': rc_daily_data.volatility_high,
                    'Volatility low': rc_daily_data.volatility_low,
                    'Volatility close': rc_daily_data.volatility_close,
                    'STDEV open': kc_daily_data.stdev_vol_open_20_days if kc_daily_data.stdev_vol_open_20_days is not None else '',
                    'STDEV high': kc_daily_data.stdev_vol_high_20_days if kc_daily_data.stdev_vol_high_20_days is not None else '',
                    'STDEV low': kc_daily_data.stdev_vol_low_20_days if kc_daily_data.stdev_vol_low_20_days is not None else '',
                    'STDEV close': kc_daily_data.stdev_vol_close_20_days if kc_daily_data.stdev_vol_close_20_days is not None else ''
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"rc_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
    def delete_data_rc(request, pk):
        data = get_object_or_404(OHLCDataRCDaily, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu RC thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu RC: {str(e)}',
                }, status=400)

class ImpliedVolatilityView:
    @login_required(login_url="login_cms")
    def list_data_iv(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 50)

        daily_datas = ImpliedVolatility.objects.all().order_by('-timestamp')
        
        for data in daily_datas:
            data.implied_volatility_rc = data.implied_volatility_rc * 100 if data.implied_volatility_rc is not None else None
            data.implied_volatility_kc = data.implied_volatility_kc * 100 if data.implied_volatility_kc is not None else None
            data.rv_passed_value_kc = data.rv_passed_value_kc * 100 if data.rv_passed_value_kc is not None else None
            data.rv_passed_value_rc = data.rv_passed_value_rc * 100 if data.rv_passed_value_rc is not None else None

            data.implied_volatility_rck = data.implied_volatility_rck * 100 if data.implied_volatility_rck is not None else None
            data.implied_volatility_kck = data.implied_volatility_kck * 100 if data.implied_volatility_kck is not None else None
            data.rv_passed_value_kck = data.rv_passed_value_kck * 100 if data.rv_passed_value_kck is not None else None
            data.rv_passed_value_rck = data.rv_passed_value_rck * 100 if data.rv_passed_value_rck is not None else None

            data.implied_volatility_rcn = data.implied_volatility_rcn * 100 if data.implied_volatility_rcn is not None else None
            data.implied_volatility_kcn = data.implied_volatility_kcn * 100 if data.implied_volatility_kcn is not None else None
            data.rv_passed_value_kcn = data.rv_passed_value_kcn * 100 if data.rv_passed_value_kcn is not None else None
            data.rv_passed_value_rcn = data.rv_passed_value_rcn * 100 if data.rv_passed_value_rcn is not None else None

            data.implied_volatility_rcu = data.implied_volatility_rcu * 100 if data.implied_volatility_rcu is not None else None
            data.implied_volatility_kcu = data.implied_volatility_kcu * 100 if data.implied_volatility_kcu is not None else None
            data.rv_passed_value_kcu = data.rv_passed_value_kcu * 100 if data.rv_passed_value_kcu is not None else None
            data.rv_passed_value_rcu = data.rv_passed_value_rcu * 100 if data.rv_passed_value_rcu is not None else None
        
        paginator = Paginator(daily_datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'daily_datas/iv_list.html', {'daily_datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_data_iv(request):
        if request.method == 'POST':
            try:
                # Lấy dữ liệu từ request.POST
                timestamp_str = request.POST.get('timestamp')
                input_date = timezone.make_aware(datetime.datetime.strptime(timestamp_str, '%Y-%m-%d'))

                implied_volatility_rc = round(float(request.POST.get('implied_volatility_rc')) / 100, 4) if request.POST.get('implied_volatility_rc') else None
                implied_volatility_kc = round(float(request.POST.get('implied_volatility_kc')) / 100, 4) if request.POST.get('implied_volatility_kc') else None

                implied_volatility_kck = round(float(request.POST.get('implied_volatility_kck')) / 100, 4) if request.POST.get('implied_volatility_kck') else None
                implied_volatility_rck = round(float(request.POST.get('implied_volatility_rck')) / 100, 4) if request.POST.get('implied_volatility_rck') else None

                implied_volatility_kcn = round(float(request.POST.get('implied_volatility_kcn')) / 100, 4) if request.POST.get('implied_volatility_kcn') else None
                implied_volatility_rcn = round(float(request.POST.get('implied_volatility_rcn')) / 100, 4) if request.POST.get('implied_volatility_rcn') else None
                
                implied_volatility_kcu = round(float(request.POST.get('implied_volatility_kcu')) / 100, 4) if request.POST.get('implied_volatility_kcu') else None
                implied_volatility_rcu = round(float(request.POST.get('implied_volatility_rcu')) / 100, 4) if request.POST.get('implied_volatility_rcu') else None

                rc_passed = False
                kc_passed = False

                kck_passed = False
                rck_passed = False
                
                kcn_passed = False
                rcn_passed = False
                
                kcu_passed = False
                rcu_passed = False

                rv_passed_value_rc = None
                rv_passed_value_kc = None

                rv_passed_value_kck = None
                rv_passed_value_rck = None

                rv_passed_value_kcn = None
                rv_passed_value_rcn = None
                
                rv_passed_value_kcu = None
                rv_passed_value_rcu = None

                # Kiểm tra điều kiện cho RC (Robusta Coffee Mar)
                if implied_volatility_rc:
                    ohlc_rc = OHLCDataRCDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_rc:
                        # Lấy tất cả các chỉ số STDEV, lọc bỏ giá trị None
                        stdev_values_rc = [
                            ohlc_rc.stdev_vol_open_20_days,
                            ohlc_rc.stdev_vol_high_20_days,
                            ohlc_rc.stdev_vol_low_20_days,
                            ohlc_rc.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_rc
                        if any(v is not None and v > implied_volatility_rc for v in stdev_values_rc):
                            rc_passed = True
                            rv_passed_value_rc = max(v for v in stdev_values_rc if v is not None) - implied_volatility_rc

                # Kiểm tra điều kiện cho KC (Arabica Coffee Mar)
                if implied_volatility_kc:
                    ohlc_kc = OHLCDataKCDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_kc:
                        stdev_values_kc = [
                            ohlc_kc.stdev_vol_open_20_days,
                            ohlc_kc.stdev_vol_high_20_days,
                            ohlc_kc.stdev_vol_low_20_days,
                            ohlc_kc.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_kc
                        if any(v is not None and v > implied_volatility_kc for v in stdev_values_kc):
                            kc_passed = True
                            rv_passed_value_kc = max(v for v in stdev_values_kc if v is not None) - implied_volatility_kc
                
                # Kiểm tra điều kiện cho KCK (Arabica Coffee May)
                if implied_volatility_kck:
                    ohlc_kck = OHLCDataKCKDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_kck:
                        stdev_values_kck = [
                            ohlc_kck.stdev_vol_open_20_days,
                            ohlc_kck.stdev_vol_high_20_days,
                            ohlc_kck.stdev_vol_low_20_days,
                            ohlc_kck.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_kc
                        if any(v is not None and v > implied_volatility_kck for v in stdev_values_kck):
                            kck_passed = True
                            rv_passed_value_kck = max(v for v in stdev_values_kck if v is not None) - implied_volatility_kck

                # Kiểm tra điều kiện cho RCK (Robusta Coffee May)
                if implied_volatility_rck:
                    ohlc_rck = OHLCDataRCKDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_rck:
                        # Lấy tất cả các chỉ số STDEV, lọc bỏ giá trị None
                        stdev_values_rck = [
                            ohlc_rck.stdev_vol_open_20_days,
                            ohlc_rck.stdev_vol_high_20_days,
                            ohlc_rck.stdev_vol_low_20_days,
                            ohlc_rck.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_rck
                        if any(v is not None and v > implied_volatility_rck for v in stdev_values_rck):
                            rck_passed = True
                            rv_passed_value_rck = max(v for v in stdev_values_rck if v is not None) - implied_volatility_rck

                # Kiểm tra điều kiện cho KCN (Arabica Coffee July)
                if implied_volatility_kcn:
                    ohlc_kcn = OHLCDataKCNDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_kcn:
                        stdev_values_kcn = [
                            ohlc_kcn.stdev_vol_open_20_days,
                            ohlc_kcn.stdev_vol_high_20_days,
                            ohlc_kcn.stdev_vol_low_20_days,
                            ohlc_kcn.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_kc
                        if any(v is not None and v > implied_volatility_kcn for v in stdev_values_kcn):
                            kcn_passed = True
                            rv_passed_value_kcn = max(v for v in stdev_values_kcn if v is not None) - implied_volatility_kcn

                # Kiểm tra điều kiện cho RCN (Robusta Coffee July)
                if implied_volatility_rcn:
                    ohlc_rcn = OHLCDataRCNDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_rcn:
                        # Lấy tất cả các chỉ số STDEV, lọc bỏ giá trị None
                        stdev_values_rcn = [
                            ohlc_rcn.stdev_vol_open_20_days,
                            ohlc_rcn.stdev_vol_high_20_days,
                            ohlc_rcn.stdev_vol_low_20_days,
                            ohlc_rcn.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_rcn
                        if any(v is not None and v > implied_volatility_rcn for v in stdev_values_rcn):
                            rcn_passed = True
                            rv_passed_value_rcn = max(v for v in stdev_values_rcn if v is not None) - implied_volatility_rcn


                # Kiểm tra điều kiện cho KCU (Arabica Coffee Sep)
                if implied_volatility_kcu:
                    ohlc_kcu = OHLCDataKCUDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_kcu:
                        stdev_values_kcu = [
                            ohlc_kcu.stdev_vol_open_20_days,
                            ohlc_kcu.stdev_vol_high_20_days,
                            ohlc_kcu.stdev_vol_low_20_days,
                            ohlc_kcu.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_kc
                        if any(v is not None and v > implied_volatility_kcu for v in stdev_values_kcu):
                            kcu_passed = True
                            rv_passed_value_kcu = max(v for v in stdev_values_kcu if v is not None) - implied_volatility_kcu

                # Kiểm tra điều kiện cho RCU (Robusta Coffee Sep)
                if implied_volatility_rcu:
                    ohlc_rcu = OHLCDataRCUDaily.objects.filter(timestamp__date=input_date).first()
                    if ohlc_rcu:
                        # Lấy tất cả các chỉ số STDEV, lọc bỏ giá trị None
                        stdev_values_rcu = [
                            ohlc_rcu.stdev_vol_open_20_days,
                            ohlc_rcu.stdev_vol_high_20_days,
                            ohlc_rcu.stdev_vol_low_20_days,
                            ohlc_rcu.stdev_vol_close_20_days
                        ]
                        # Nếu bất kỳ giá trị STDEV nào > implied_volatility_rcu
                        if any(v is not None and v > implied_volatility_rcu for v in stdev_values_rcu):
                            rcu_passed = True
                            rv_passed_value_rcu = max(v for v in stdev_values_rcu if v is not None) - implied_volatility_rcu

                iv_daily = ImpliedVolatility(
                    timestamp=input_date,
                    implied_volatility_rc=implied_volatility_rc,
                    implied_volatility_kc=implied_volatility_kc,

                    implied_volatility_kck=implied_volatility_kck,
                    implied_volatility_rck=implied_volatility_rck,

                    implied_volatility_kcn=implied_volatility_kcn,
                    implied_volatility_rcn=implied_volatility_rcn,

                    implied_volatility_kcu=implied_volatility_kcu,
                    implied_volatility_rcu=implied_volatility_rcu,

                    realized_volatility_rc_has_passed=rc_passed,
                    realized_volatility_kc_has_passed=kc_passed,

                    realized_volatility_kck_has_passed=kck_passed,
                    realized_volatility_rck_has_passed=rck_passed,

                    realized_volatility_kcn_has_passed=kcn_passed,
                    realized_volatility_rcn_has_passed=rcn_passed,

                    realized_volatility_kcu_has_passed=kcu_passed,
                    realized_volatility_rcu_has_passed=rcu_passed,
                    
                    rv_passed_value_rc=rv_passed_value_rc,
                    rv_passed_value_kc=rv_passed_value_kc,
                    
                    rv_passed_value_kck=rv_passed_value_kck,
                    rv_passed_value_rck=rv_passed_value_rck,
                    
                    rv_passed_value_kcn=rv_passed_value_kcn,
                    rv_passed_value_rcn=rv_passed_value_rcn,
                    
                    rv_passed_value_kcu=rv_passed_value_kcu,
                    rv_passed_value_rcu=rv_passed_value_rcu,
                )
                iv_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('daily-iv-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'daily_datas/iv_create.html')
    
    @login_required(login_url="login_cms")
    def import_excel_iv(request):
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

                df.columns = df.columns.str.strip()
                expected_columns = [
                    'Date','RMH26','KCH26'
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
                        rc_val = clean_percentage(row['RMH26'])
                        kc_val = clean_percentage(row['KCH26'])
                        iv = ImpliedVolatility.objects.update_or_create(
                            timestamp=row['Date'],
                            defaults={
                                'implied_volatility_rc': rc_val,
                                'implied_volatility_kc': kc_val,
                            }
                        )
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
            iv_daily_datas = ImpliedVolatility.objects.all().order_by('timestamp')
            target_timezone = timezone.get_current_timezone()
            data = []
            for iv_daily_data in iv_daily_datas:
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
                    'Date': format_date(iv_daily_data.timestamp),
                    'KCH': iv_daily_data.implied_volatility_kc * 100 if iv_daily_data.implied_volatility_kc else "",
                    'RCH': iv_daily_data.implied_volatility_rc * 100 if iv_daily_data.implied_volatility_rc else "",
                    'KCK': iv_daily_data.implied_volatility_kck * 100 if iv_daily_data.implied_volatility_kck else "",
                    'RCK': iv_daily_data.implied_volatility_rck * 100 if iv_daily_data.implied_volatility_rck else "",
                    'KCN': iv_daily_data.implied_volatility_kcn * 100 if iv_daily_data.implied_volatility_kcn else "",
                    'RCN': iv_daily_data.implied_volatility_rcn * 100 if iv_daily_data.implied_volatility_rcn else "",
                    'KCU': iv_daily_data.implied_volatility_kcu * 100 if iv_daily_data.implied_volatility_kcu else "",
                    'RCU': iv_daily_data.implied_volatility_rcu * 100 if iv_daily_data.implied_volatility_rcu else "",
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"iv_daily_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
                    'Date', 'KCH', 'RCH', 'KCK', 'RCK', 'KCN', 'RCN', 'KCU', 'RCU'
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
    def delete_data_iv(request, pk):
        data = get_object_or_404(ImpliedVolatility, pk=pk)
        if request.method == 'POST':
            try:    
                data.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa dữ liệu IV thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa dữ liệu IV: {str(e)}',
                }, status=400)

class OpenGapView:
    @login_required(login_url="login_cms")
    def calculate_open_gap(request):
        result = 0
        if request.method == 'POST':
            open_index = request.POST.get('open_index')
            symbol = request.POST.get('symbol', 'KC')
            
            if symbol == 'KCH':
                last_data = OHLCDataKCDaily.objects.order_by('-timestamp').first()            
            elif symbol == 'RCH':
                last_data = OHLCDataRCDaily.objects.order_by('-timestamp').first()
            elif symbol == 'KCK':
                last_data = OHLCDataKCKDaily.objects.order_by('-timestamp').first()
            elif symbol == 'RCK':
                last_data = OHLCDataRCKDaily.objects.order_by('-timestamp').first()
            elif symbol == 'KCU':
                last_data = OHLCDataKCUDaily.objects.order_by('-timestamp').first()
            elif symbol == 'RCU':
                last_data = OHLCDataRCUDaily.objects.order_by('-timestamp').first()

            if last_data:
                result = float(open_index) - float(last_data.close)
            else:
                result = 0
            
            print("last_data.timestamp,", timezone.localtime(last_data.timestamp))
            return JsonResponse({
                'status': 'success',
                'message': 'Tính toán thành công',
                'last_day_close': float(last_data.close) if last_data else 0.0,
                'last_day': timezone.localtime(last_data.timestamp).strftime('%Y-%m-%d') if last_data else '',
                'open_index': float(open_index) if open_index else 0.0,
                'result': result
            })

        return render(request, 'daily_datas/open_gap.html')


def clean_percentage(value):
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