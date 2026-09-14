# Thêm các import này ở đầu file views.py
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings # Import settings
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from django.shortcuts import render
from datetime import datetime, timedelta
import requests
import pandas as pd
import json
from .models import IceRCStockData
import openpyxl.styles
from django.core.paginator import Paginator

class KCDataStockJsonToExcel(View):
    def post(request):
        if request.method == 'POST':
            try:
                timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
                input_file = f"media/kc_local_uploads/stock_coffee_data.json"
                output_file = f"ice_kc_stock_data_export_{timestamp}.xlsx"
                output_path = os.path.join(settings.MEDIA_ROOT, 'ice_kc_stock_data_export', output_file)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(input_file, 'r') as f:
                    data = json.load(f)

                # 2. Chuyển đổi dữ liệu thành DataFrame
                df = pd.DataFrame(data, columns=['Date', 'Bags'])

                df['Bags'] = pd.to_numeric(df['Bags'], errors='coerce')
                
                # Tùy chọn: Chuyển đổi cột 'Date' sang kiểu datetime
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                # 3. Lưu DataFrame vào file Excel
                df.to_excel(output_path, index=False) # index=False để không ghi số thứ tự hàng vào Excel

                print(f"✅ Chuyển đổi thành công! Dữ liệu đã được lưu vào: {output_file}")
                print("\n---")
                print("Dữ liệu 5 hàng đầu trong DataFrame:")
                print(df.head())

                return JsonResponse({
                        "status": "success",
                        "message": "Lấy dữ liệu thành công!",
                        "result": f"/media/ice_kc_stock_data_export/{output_file}"
                    }, status=200)
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Lấy dữ liệu thất bại: {str(e)}"
                }, status=400)
        
        per_page_options = [10, 25, 50, 100]
        per_page = request.GET.get('per_page', 25)
        
        file_path = os.path.join(settings.MEDIA_ROOT, 'kc_local_uploads', 'stock_coffee_data.json')
        with open(file_path, 'r') as f:
            raw_data = json.load(f)

        formatted_data = []
        for item in reversed(raw_data):
            formatted_data.append({
                'date': item[0],
                'stock': item[1]
            })
            
        last_data = formatted_data[0] if formatted_data else None
        pre_last_data = formatted_data[1] if len(formatted_data) > 1 else None
        paginator = Paginator(formatted_data, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        change = float(last_data['stock']) - float(pre_last_data['stock']) if last_data and pre_last_data else 0
        return render(request, 'market-agent/get-kc-stock-data.html', {
            'datas': page_obj, 
            'per_page_options': per_page_options, 
            'per_page': int(per_page),
            'last_data': last_data,
            'pre_last_data': pre_last_data,
            'change': change
        })

class RCDataStockView(View):
    def post(request):
        if request.method == 'POST':
            try:
                EXPORT_DIR = os.path.join(settings.MEDIA_ROOT, 'ice_rc_stock_data_export')

                start_date = request.POST.get('start_date', None)
                end_date = request.POST.get('end_date', None)
                
                if start_date and end_date:
                    ice_rc_stock_datas = IceRCStockData.objects.filter(date__range=(start_date, end_date)).order_by('date')
                else:
                    ice_rc_stock_datas = IceRCStockData.objects.all().order_by('date')
                
                data = []
                
                for ice_rc_stock_data in ice_rc_stock_datas:
                    # Định dạng date: DateField của Django là datetime.date object
                    date_formatted = ice_rc_stock_data.date.strftime('%d/%m/%Y') if ice_rc_stock_data.date else ""
                    
                    # Xử lý trường hợp lots_with_val_cert là None (NULL)
                    lots_with_val_cert_value = str(ice_rc_stock_data.lots_with_val_cert) if ice_rc_stock_data.lots_with_val_cert is not None else ''
                    lots_non_tend_value = str(ice_rc_stock_data.lots_non_tend) if ice_rc_stock_data.lots_non_tend is not None else ''
                    lots_suspended_value = str(ice_rc_stock_data.lots_suspended) if ice_rc_stock_data.lots_suspended is not None else ''

                    data.append({
                        'date': date_formatted,
                        'lots_with_val_cert': lots_with_val_cert_value,
                        'lots_non_tend': lots_non_tend_value,
                        'lots_suspended': lots_suspended_value
                    })
                
                df = pd.DataFrame(data)
                
                # 2. Định nghĩa tên file và đường dẫn cục bộ
                timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
                output_file = f"ice_rc_stock_data_export_{timestamp}.xlsx"
                output_path = os.path.join(settings.MEDIA_ROOT, 'ice_rc_stock_data_export', output_file)
                # 3. Tạo Excel file cục bộ
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # Tương tự như trước, tạo sheet tạm để khởi tạo writer
                    df.to_excel(writer, sheet_name='Temp', index=False)
                    
                    workbook = writer.book
                    
                    # Xóa sheet mặc định và tạo sheet mới
                    if 'Temp' in workbook.sheetnames:
                        del workbook['Temp']
                    if 'Sheet' in workbook.sheetnames:
                        del workbook['Sheet']
                        
                    worksheet = workbook.create_sheet("SCHEDULE", 0)
                    
                    # Cấu hình Style
                    header_font = openpyxl.styles.Font(bold=True)
                    center_align = openpyxl.styles.Alignment(horizontal='center', vertical='center')

                    # Merge dòng 1 và dòng 2: Tiêu đề "SCHEDULE"
                    worksheet.merge_cells('A1:D2') 
                    worksheet['A1'] = 'SCHEDULE'
                    worksheet['A1'].font = header_font
                    worksheet['A1'].alignment = center_align
                    
                    # Dòng 3: Headers
                    headers = ['DATE', 'LOTS WITH VAL CERT', 'LOTS NON TEND', 'LOTS SUSPENDED']
                    
                    for col, header in enumerate(headers, 1):
                        cell = worksheet.cell(row=3, column=col, value=header)
                        cell.font = header_font
                        cell.alignment = center_align
                    
                    # Ghi dữ liệu
                    if not df.empty:
                        for r_idx, row_data in enumerate(df.itertuples(), 4):
                            # Ghi dữ liệu ngày (cột 1)
                            worksheet.cell(row=r_idx, column=1, value=row_data[1])
                            # Ghi dữ liệu lots_with_val_cert (cột 2)
                            worksheet.cell(row=r_idx, column=2, value=row_data[2])
                            # Ghi dữ liệu lots_non_tend (cột 3)
                            worksheet.cell(row=r_idx, column=3, value=row_data[3])
                            # Ghi dữ liệu lots_suspended (cột 4)
                            worksheet.cell(row=r_idx, column=4, value=row_data[4])
                            
                    # Tùy chỉnh độ rộng cột
                    worksheet.column_dimensions['A'].width = 15
                    worksheet.column_dimensions['B'].width = 20
                    worksheet.column_dimensions['C'].width = 20
                    worksheet.column_dimensions['D'].width = 20
                                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Export dữ liệu thành công.',
                    'result': f"/media/ice_rc_stock_data_export/{output_file}", # Đường dẫn cục bộ trên server
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Lấy dữ liệu thất bại: {str(e)}"
                }, status=400)
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 25)
        datas = IceRCStockData.objects.all().order_by('-date')
        last_data = datas.first()
        pre_last_data = datas[1] if len(datas) > 1 else None
        paginator = Paginator(datas, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        today = datetime.now().date()
        change = int(last_data.lots_with_val_cert) - int(pre_last_data.lots_with_val_cert)
        return render(request, 'market-agent/get-rc-stock-data.html', {'datas': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page), 'today': today, 'last_data': last_data, 'pre_last_data': pre_last_data, 'change': change})
