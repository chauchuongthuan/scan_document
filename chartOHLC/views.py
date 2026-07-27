from django.shortcuts import render
from django.http import JsonResponse
from .models import OHLCDataKC, OHLCDataRC
import datetime
from django.utils import timezone
import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pandas as pd
import openpyxl
from django.utils.timezone import localtime

class ChartView:
    @login_required(login_url="login_cms")
    def view_chart_kc(request):
        # Hiển thị trang dashboard
        return render(request, 'chart/kc.html')

    @login_required(login_url="login_cms")
    def get_chart_json_kc(request):
        symbol = request.GET.get('symbol', 'KCU2026')
        
        # 1. Lấy tham số lùi ngày từ request, mặc định là 0 (phiên gần nhất)
        try:
            days_back = int(request.GET.get('days_back', 0))
        except ValueError:
            days_back = 0
            
        # 2. Lấy thời gian hiện tại và tính toán ngày mục tiêu
        now_local = timezone.localtime()
        target_date = now_local - timezone.timedelta(days=days_back)
        start_date = target_date - timezone.timedelta(days=1)
        
        # 3. Đặt mốc thời gian: Bắt đầu lúc 16:15 ngày trước đó, kết thúc lúc 00:30 ngày mục tiêu
        session_start = start_date.replace(hour=16, minute=15, second=0, microsecond=0)
        session_end = target_date.replace(hour=1, minute=30, second=0, microsecond=0)

        # 4. Lọc dữ liệu trong khoảng thời gian đã tính (sử dụng < session_end để lấy đến 00:29)
        data = OHLCDataKC.objects.filter(
            symbol=symbol, 
            timestamp__gte=session_start,
            timestamp__lt=session_end
        ).order_by('-timestamp')[:600]
        
        chart_data = []
        for d in reversed(data):
            chart_data.append({
                'time': int(timezone.localtime(d.timestamp).timestamp()),
                'open': d.open, 
                'high': d.high,
                'low': d.low, 
                'close': d.close
            })
        return JsonResponse(chart_data, safe=False)

    @login_required(login_url="login_cms")
    def view_chart_rc(request):
        # Hiển thị trang dashboard
        return render(request, 'chart/rc.html')

    @login_required(login_url="login_cms")
    def get_chart_json_rc(request):
        symbol = request.GET.get('symbol', 'RCU2026')
        
        # 1. Lấy tham số lùi ngày từ request, mặc định là 0 (phiên gần nhất)
        try:
            days_back = int(request.GET.get('days_back', 0))
        except ValueError:
            days_back = 0
            
        # 2. Lấy thời gian hiện tại và tính toán ngày mục tiêu
        now_local = timezone.localtime()
        target_date = now_local - timezone.timedelta(days=days_back)
        start_date = target_date - timezone.timedelta(days=1)
        
        # 3. Đặt mốc thời gian: Bắt đầu lúc 16:15 ngày trước đó, kết thúc lúc 00:30 ngày mục tiêu
        session_start = start_date.replace(hour=16, minute=15, second=0, microsecond=0)
        session_end = target_date.replace(hour=1, minute=30, second=0, microsecond=0)
        
        # 4. Lọc dữ liệu trong khoảng thời gian đã tính
        data = OHLCDataRC.objects.filter(
            symbol=symbol, 
            timestamp__gte=session_start,
            timestamp__lt=session_end
        ).order_by('-timestamp')[:600]
        
        chart_data = []
        for d in reversed(data):
            chart_data.append({
                'time': int(timezone.localtime(d.timestamp).timestamp()),
                'open': d.open, 
                'high': d.high,
                'low': d.low, 
                'close': d.close
            })
            
        return JsonResponse(chart_data, safe=False)

    @login_required(login_url="login_cms")
    def export_excel_kc(request):
        try:
            kc_datas = OHLCDataKC.objects.all().order_by('timestamp')
            
            data = []
            for kc_data in kc_datas:
                # Format date fields to dd/mm/yyyy
                def format_date(date_field):
                    if date_field:
                        if isinstance(date_field, (datetime.date, datetime.datetime)):
                            return date_field.strftime('%d/%m/%Y %H:%M')
                        # Nếu là string, cố gắng parse và format lại
                        try:
                            parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                            return parsed_date.strftime('%d/%m/%Y %H:%M')
                        except:
                            return str(date_field)
                    return ""
                dt_local = localtime(kc_data.timestamp)
                data.append({
                    'symbol': kc_data.symbol,
                    'timestamp': format_date(dt_local),
                    'open': kc_data.open,
                    'high': kc_data.high,
                    'low': kc_data.low,
                    'close': kc_data.close,
                    
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"kc_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
                    'Symbol', 'Timestamp', 'Open', 'High', 'Low', 'Close', 
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
    def export_excel_rc(request):
        try:
            rc_datas = OHLCDataRC.objects.all().order_by('timestamp')
            
            data = []
            for rc_data in rc_datas:
                # Format date fields to dd/mm/yyyy
                def format_date(date_field):
                    if date_field:
                        if isinstance(date_field, (datetime.date, datetime.datetime)):
                            return date_field.strftime('%d/%m/%Y %H:%M')
                        # Nếu là string, cố gắng parse và format lại
                        try:
                            parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                            return parsed_date.strftime('%d/%m/%Y %H:%M')
                        except:
                            return str(date_field)
                    return ""
                dt_local = localtime(rc_data.timestamp)
                data.append({
                    'symbol': rc_data.symbol,
                    'timestamp': format_date(dt_local),
                    'open': rc_data.open,
                    'high': rc_data.high,
                    'low': rc_data.low,
                    'close': rc_data.close,
                    
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"rc_data__{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
                    'Symbol', 'Timestamp', 'Open', 'High', 'Low', 'Close', 
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
