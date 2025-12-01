import os
import re 
import pandas as pd
from datetime import datetime, date, timedelta
from django.db import IntegrityError
from django.conf import settings 
# from .models import IceRCStockData # Đảm bảo import Model của bạn

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import IceRCStockData

import openpyxl.styles

EXPORT_DIR = os.path.join(settings.MEDIA_ROOT, 'ice_rc_stock_data_export')
# Định nghĩa thư mục chứa các file Robusta đã được tải về
# Bạn cần đảm bảo thư mục này tồn tại và có thể truy cập được
try:
    RC_UPLOAD_DIR = os.path.join(settings.BASE_DIR, 'media/rc_local_uploads')
except AttributeError:
    # Fallback cho môi trường không có settings
    RC_UPLOAD_DIR = os.path.join(os.getcwd(), 'media/rc_local_uploads')

def extract_grand_total_rc(df: pd.DataFrame, column_name: str) -> str | None:
    """
    Tìm hàng có giá trị cột đầu tiên là 'GrandTotal' và trích xuất giá trị 
    từ cột được chỉ định.
    """
    try:
        # Lấy tên cột đầu tiên (thường là 'Commodity' trong file RC)
        first_col = df.columns[0]
        
        # 1. Tìm hàng 'GrandTotal'
        grand_total_row = df[df[first_col].astype(str).str.contains('GrandTotal', case=False, na=False)]
        
        if grand_total_row.empty:
            return None
        
        # 2. Lấy giá trị từ cột được chỉ định
        value = grand_total_row[column_name].iloc[0]
        
        # 3. Trả về kết quả dưới dạng chuỗi
        return str(value)
        
    except KeyError:
        return None
    except Exception:
        return None


def extract_date_from_filename(filename: str) -> date | None:
    """
    Trích xuất ngày (YYYYMMDD) từ tên file có dạng Stock_Report_RC_YYYYMMDD_######.csv
    """
    # Pattern: Stock_Report_RC_YYYYMMDD_######.csv
    match = re.search(r'Stock_Report_RC_(\d{8})_\d{6}\.csv', filename, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, '%Y%m%d').date()
        except ValueError:
            pass
    return None

def process_local_rc_files(file_paths: list[str]):
    """
    Đọc dữ liệu từ danh sách các file CSV Robusta local và lưu vào database.
    Mỗi phần tử trong file_paths là đường dẫn tuyệt đối hoặc tương đối.
    """
    results = {
        'success_count': 0, 
        'error_count': 0, 
        'total_files': len(file_paths), 
        'processed_files': []
    }
    
    COLUMN_NAMES = {
        'lots_with_val_cert': 'LotsWithValCert',
        'lots_non_tend': 'LotsNonTend',
        'lots_suspended': 'LotsSuspended'
    }

    for file_path in file_paths:
        
        file_name = os.path.basename(file_path)
        file_date = extract_date_from_filename(file_name)
        
        if file_date is None:
            results['error_count'] += 1
            results['processed_files'].append({'file': file_name, 'status': 'Error: Invalid Date in Filename'})
            continue
            
        try:
            # 1. Đọc file CSV local
            df = pd.read_csv(file_path, header=0)
            
            # 2. Trích xuất giá trị GrandTotal
            lots_with_val_cert_value = extract_grand_total_rc(df, COLUMN_NAMES['lots_with_val_cert'])
            lots_non_tend_value = extract_grand_total_rc(df, COLUMN_NAMES['lots_non_tend'])
            lots_suspended_value = extract_grand_total_rc(df, COLUMN_NAMES['lots_suspended'])
            
            # 3. Kiểm tra và lưu vào Database
            if lots_with_val_cert_value is None and lots_non_tend_value is None and lots_suspended_value is None:
                results['error_count'] += 1
                results['processed_files'].append({'file': file_name, 'status': 'Error: Data Not Found (Missing GrandTotal)'})
            else:
                IceRCStockData.objects.update_or_create(
                    date=file_date,
                    defaults={
                        'lots_with_val_cert': lots_with_val_cert_value,
                        'lots_non_tend': lots_non_tend_value,
                        'lots_suspended': lots_suspended_value
                    }
                )
                results['success_count'] += 1
                results['processed_files'].append({'file': file_name, 'status': 'Success'})

        except FileNotFoundError:
            results['error_count'] += 1
            results['processed_files'].append({'file': file_name, 'status': 'Error: File Not Found'})
        except Exception as e:
            results['error_count'] += 1
            results['processed_files'].append({'file': file_name, 'status': f'Error: Processing Failed ({str(e)})'})
            
    return results

class ImportLocalIceRCDataView(APIView): 
    @swagger_auto_schema(
        operation_description="Nhập dữ liệu Robusta từ các file CSV đã có sẵn trong thư mục local.",
        manual_parameters=[
            openapi.Parameter(
                'filenames', 
                in_=openapi.IN_QUERY, 
                description="Danh sách các tên file cần xử lý (cách nhau bằng dấu phẩy). Ví dụ: file1.csv,file2.csv", 
                type=openapi.TYPE_STRING, 
                required=False
            ),
        ]
    )
    def get(self, request):
        
        # Lấy danh sách tên file từ query params (hoặc đọc toàn bộ thư mục nếu không có param)
        filenames_str = request.query_params.get('filenames', None)
        
        if filenames_str:
            target_filenames = [f.strip() for f in filenames_str.split(',') if f.strip()]
        else:
            # Nếu không truyền tên file, đọc toàn bộ file CSV trong thư mục
            try:
                target_filenames = [f for f in os.listdir(RC_UPLOAD_DIR) if f.lower().endswith('.csv')]
            except FileNotFoundError:
                return Response({
                    'success': False,
                    'message': f'Thư mục chứa file "{RC_UPLOAD_DIR}" không tồn tại.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not target_filenames:
            return Response({
                'success': True,
                'message': 'Không tìm thấy file nào để xử lý.'
            }, status=status.HTTP_200_OK)
            
        # Tạo danh sách đường dẫn tuyệt đối
        file_paths = [os.path.join(RC_UPLOAD_DIR, filename) for filename in target_filenames]
        
        try:
            results = process_local_rc_files(file_paths)
            
            return Response({
                'success': True,
                'data': {
                    'message': f"Hoàn thành quá trình nhập dữ liệu từ {results['total_files']} file.",
                    'summary': results
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExportIceRCDataView(APIView):
    def get(self, request):
        try:
            # 1. Lấy dữ liệu
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
            filename = f"ice_rc_stock_data_export_{timestamp}.xlsx"
            file_path = os.path.join(EXPORT_DIR, filename)
            
            # 3. Tạo Excel file cục bộ
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
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
            
            # 4. Tạo đường link công khai (public URL)
            # Cần cấu hình Django để serve MEDIA_URL cho các file trong MEDIA_ROOT
            relative_path = os.path.join('exports', filename)
            download_url = f"{settings.MEDIA_URL}{relative_path}" # Hoặc chỉ trả về relative_path nếu cần
            
            return Response({
                'success': True,
                'message': 'Export dữ liệu thành công.',
                'file_name': filename,
                'file_path': file_path, # Đường dẫn cục bộ trên server
                'download_url': download_url # Đường link để tải file
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
