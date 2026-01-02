from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from .models import OHLCDataRCDaily, OHLCDataKCDaily, ImpliedVolatility
from django.utils import timezone
import os
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
import json
from coffee.helpers import extract_fields_from_pdf
import openpyxl
import datetime
# Document Views
class DocumentListView:
    @login_required(login_url="login_cms")
    def list_documents(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 10)

        documents = OHLCDataKCDaily.objects.all().order_by('-created_at')
            
        paginator = Paginator(documents, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'documents/list.html', {'documents': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def create_document(request):
        if request.method == 'POST':
            try:
                # Lấy dữ liệu từ request.POST
                timestamp = request.POST.get('timestamp')
                open = request.POST.get('open')
                high = request.POST.get('high')
                low = request.POST.get('low')
                close = request.POST.get('close')
                
                kc_daily = OHLCDataKCDaily(
                    timestamp=timestamp,
                    open=open,
                    high=high,
                    low=low,
                    close=close,
                )
                kc_daily.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm thành công!',
                    'redirect': reverse('document-list')
                })
            except Exception as e:
                print("Error:", str(e))
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm: {str(e)}'
                }, status=400)  
        
        return render(request, 'documents/create.html')
    
    @login_required(login_url="login_cms")
    def import_excel(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                symbol = request.POST.get('symbol')
                excel_file = request.FILES['excel_file']

                # Save the uploaded file temporarily
                temp_file_path = default_storage.save('temp/' + excel_file.name, excel_file)
                file_path = os.path.join(default_storage.location, temp_file_path)

                # Read Excel file
                df = pd.read_excel(
                    file_path,
                    header=1,
                )

                df.columns = df.columns.str.strip().str.upper()
                
                expected_columns = [
                    'Date', 'Open', 'High', 'Low', 'Close'
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
                        if symbol == 'KCH2026':
                            kc_daily = OHLCDataKCDaily(
                                timestamp=row.get('Date'),
                                open=row.get('Open'),
                                high=row.get('High'),
                                low=row.get('Low'),
                                close=row.get('Close'),
                            )
                            kc_daily.save()
                            imported_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Dòng {index + 1}") 

                
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
            # Lấy tất cả documents từ database
            documents = Document.objects.all().order_by('comco_ref')
            
            # Tạo DataFrame từ dữ liệu documents
            data = []
            for document in documents:
                # Format date fields to dd/mm/yyyy
                def format_date(date_field):
                    if date_field:
                        if isinstance(date_field, (datetime.date, datetime.datetime)):
                            return date_field.strftime('%d/%m/%Y')
                        # Nếu là string, cố gắng parse và format lại
                        try:
                            parsed_date = datetime.datetime.strptime(str(date_field), '%Y-%m-%d')
                            return parsed_date.strftime('%d/%m/%Y')
                        except:
                            return str(date_field)
                    return ""
                
                data.append({
                    'COMCO REF': document.comco_ref,
                    'BUYER REF': document.buyer_ref,
                    'CONTRACT DATE': format_date(document.contract_date),
                    'PRICE': document.price,
                    'DDS & GEO': document.dds_and_geo,
                    'DOCS': document.docs,
                    'SHIPPERS': document.shippers,
                    'BUYERS': document.buyers,
                    'SHIPMENT PERIOD': document.shipment_period,
                    'QUALITY': document.quality,
                    'QUANTITY': document.quantity,
                    'CONTS NO': document.conts_no,
                    'PACKING': document.packing,
                    'SAMPLE': document.sample,
                    'RESULTS': document.result,
                    'STUFFING DATE': format_date(document.stuffing_date),
                    'CARRIERS': document.carriers,
                    'BOOKING NO': document.booking_no,
                    'ETD': format_date(document.etd),
                    'ETA': document.eta,
                    'DESTINATION': document.destination,
                    'INSPECTORS': document.inspectors,
                    'WAREHOUSE': document.warehouse,
                    'STATUS': document.status,
                    'WEIGHT CLAIM': document.weight_claim,
                    'REMARK': document.remark
                })
            
            df = pd.DataFrame(data)
            # Tạo HTTP response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            filename = f"schedule_export.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Tạo Excel file với cấu trúc giống file mẫu
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                # Tạo workbook
                workbook = writer.book
                
                worksheet = workbook.create_sheet("SCHEDULE", 0)
                
                # Xóa sheet mặc định nếu có
                if 'Sheet' in workbook.sheetnames:
                    del workbook['Sheet']
                
                # Merge dòng 1 và dòng 2: Tiêu đề "SCHEDULE" (merge từ A1 đến Z2)
                worksheet.merge_cells('A1:Z2')
                worksheet['A1'] = 'SCHEDULE'
                
                # Dòng 3: Headers
                headers = [
                    'COMCO REF', 'BUYER REF', 'CONTRACT DATE', 'PRICE', 'DDS & GEO', 'DOCS',
                    'SHIPPERS', 'BUYERS', 'SHIPMENT PERIOD', 'QUALITY', 'QUANTITY', 'CONTS NO',
                    'PACKING', 'SAMPLE', 'RESULTS', 'STUFFING DATE', 'CARRIERS', 'BOOKING NO',
                    'ETD', 'ETA', 'DESTINATION', 'INSPECTORS', 'WAREHOUSE', 'STATUS',
                    'WEIGHT CLAIM', 'REMARK'
                ]
                
                for col, header in enumerate(headers, 1):
                    cell = worksheet.cell(row=3, column=col, value=header)
                    # Có thể thêm style cho header nếu cần
                    cell.font = openpyxl.styles.Font(bold=True)
                
                # Ghi dữ liệu từ DataFrame (bắt đầu từ dòng 4)
                if not df.empty:
                    for row_idx, row_data in enumerate(df.itertuples(), 4):
                        for col_idx, value in enumerate(row_data[1:], 1):  # Bỏ qua index
                            worksheet.cell(row=row_idx, column=col_idx, value=value)
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Export Excel thất bại: {str(e)}'
            }, status=400)