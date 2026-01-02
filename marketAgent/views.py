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
from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import render
from datetime import datetime, timedelta
import requests
import pandas as pd
import json
from .models import IceRCStockData
import openpyxl.styles

class SearchGGView(View):
    def get(request):
        api_key = os.environ.get('API_KEY_GG_SEARCH')
        cx = os.environ.get('CX_GG_SEARCH')
        url = "https://www.googleapis.com/customsearch/v1"
        keywords_query = [
            # 'thiên tai tây nguyên mới nhất', 
            # 'thiên tai Gia Lai mới nhất', 
            # 'thiên tai dak lak mới nhất', 
            # 'thiên tai dak nong mới nhất',
            # 'lũ lụt mới nhất',
            # 'tin tức cà phê hôm nay',
            'reuters coffee',
            'tin tức thiên tai tây nguyên hôm nay',
            'tin tức cà phê hôm nay'
        ]
        
        final_data = []

        for keyword in keywords_query:
            params = {
                'key': api_key,
                'cx': cx,
                'q': keyword,
                'dateRestrict': 'd1',  # Giới hạn 1 ngày qua (d1 = 1 day)
                'gl': 'vn',
            }
            
            response = requests.get(url, params=params)
            print("response", response)
            data = response.json()

            current_keyword_articles = []
            
            if 'items' in data:
                for item in data['items']:
                    current_keyword_articles.append({
                        'title': item['title'],
                        'link': item['link'],
                        'snippet': item['snippet']
                    })

            final_data.append({
                'keyword': keyword,
                'articles': current_keyword_articles,
                'count': len(current_keyword_articles)
            })
        print("final_data", final_data)
        return render(request, 'market-agent/gg-search.html', {'results': final_data})

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
                # Mỗi phần tử trong list là một row: [Date, Bags]
                # Ta đặt tên cột là 'Date' và 'Bags'
                df = pd.DataFrame(data, columns=['Date', 'Bags'])

                # Tùy chọn: Chuyển đổi cột 'Bags' sang kiểu số (float)
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


        return render(request, 'market-agent/get-kc-stock-data.html')

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
        return render(request, 'market-agent/get-rc-stock-data.html')