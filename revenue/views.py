from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from coffee.upload import pathByDate, uploadFile, upload_editor_image
from .models import Revenue, RevenueByHour
from django.utils import timezone
import os
import urllib.parse
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
import json
from coffee.helpers import extract_fields_from_pdf
import openpyxl
from datetime import datetime, timedelta
from .api import fetch_and_sync_revenue, calculate_total_revenue_last_n_hours, REQUIRED_HOURS

today = datetime.now().date()
yesterday = today - timedelta(days=1)

class RevenueView:
    @login_required(login_url="login_cms")
    def revenue_list(request):
        if request.method == 'POST':
            try:
                start_date = request.POST.get('start_date', None)
                end_date = request.POST.get('end_date', None)
                
                if start_date and end_date:
                    fetch_and_sync_revenue(start_date, end_date)
                    return JsonResponse({
                        "status": "success",
                        "message": "Lấy dữ liệu thành công!"
                    }, status=200) 
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Lấy dữ liệu thất bại: {str(e)}"
                }, status=400)

        per_page_options = [10, 20, 50, 100]

        per_page = request.GET.get('per_page', 20)

        datas = Revenue.objects.all().order_by('-timestamp')
        
        for data in datas:
            data.total_of_day = sum([item['total'] for item in data.revenue_data])
        paginator = Paginator(datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'revenue/list.html', {'datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page), 'today': today, 'yesterday': yesterday})

class RevenueByHourView:
    @login_required(login_url="login_cms")
    def revenue_by_hour_list(request):
        if request.method == 'POST':
            try:
                start_datetime = request.POST.get('start_datetime', None)
                end_datetime = request.POST.get('end_datetime', None)
                if start_datetime:
                    start_datetime_str = start_datetime.replace("T", " ")
                    
                    if end_datetime:
                        # Case 1: Both start and end datetime provided
                        end_datetime_str = end_datetime.replace("T", " ")
                        
                        # Parse dates
                        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
                        end_dt = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
                        end_dt = end_dt - timedelta(hours=1)
                        # Generate all datetime slots in the range
                        current_dt = start_dt
                        processed_slots = []
                        
                        while current_dt <= end_dt:
                            if current_dt.hour in REQUIRED_HOURS:
                                processed_slots.append(current_dt.strftime("%Y-%m-%d %H:%M"))
                            current_dt += timedelta(hours=1)
                        
                        # Process each slot
                        for slot in processed_slots:
                            calculate_total_revenue_last_n_hours(slot, 133)
                            
                    else:
                        # Case 2: Only start datetime provided
                        calculate_total_revenue_last_n_hours(start_datetime_str, 133)
                    
                    return JsonResponse({
                        "status": "success",
                        "message": "Lấy dữ liệu thành công!"
                    }, status=200)
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Lấy dữ liệu thất bại: {str(e)}"
                }, status=400)

        per_page_options = [10, 20, 50, 100]

        per_page = request.GET.get('per_page', 50)

        datas = RevenueByHour.objects.all().order_by('-date', '-hour')
        
        paginator = Paginator(datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'revenue/list_by_hour.html', {'datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page), 'today': today, 'yesterday': yesterday})

    @login_required(login_url="login_cms")
    def export_excel(request):
        try:
            data = []
            for data_item in RevenueByHour.objects.all().order_by('-date', '-hour'):
                data.append({
                    'Date': data_item.date,
                    'Hour': data_item.hour,
                    'Total': data_item.total,
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"data__{datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
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
                    'Date', 'Hour', 'Total', 
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