from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from .models import IceData
import os
from io import BytesIO
import requests
from datetime import datetime, date, timedelta
import pandas as pd
import openpyxl.styles
from django.core.paginator import Paginator
from django.conf import settings

EXPORT_DIR = os.path.join(settings.MEDIA_ROOT, 'ice_data_export')

class IceDataViewSet(APIView): 
    def get(self, request):
        # 1. Lấy và kiểm tra start_date
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        print("start_date_str", start_date_str)
        print("end_date_str", end_date_str)
        if not start_date_str or not end_date_str:
            return Response({
                'success': False,
                'message': 'Vui lòng cung cấp tham số start_date và end_date (YYYY-MM-DD).'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Chuyển đổi start_date từ string sang date object
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'message': 'Định dạng ngày không hợp lệ. Vui lòng sử dụng YYYY-MM-DD.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if start_date > end_date:
                 return Response({
                    'success': False,
                    'message': 'start_date không được lớn hơn ngày hiện tại.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. Thực thi logic tải và lưu dữ liệu
            results = fetch_and_save_ice_data_range(start_date, end_date)
            
            return Response({
                'success': True,
                'data': {
                    'message': f"Hoàn thành quá trình tải dữ liệu từ {start_date_str} đến {end_date.strftime('%Y-%m-%d')}.",
                    'summary': results
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def fetch_and_save_ice_data_range(start_date: date, end_date: date):
    """
    Truy vấn dữ liệu Coffee Certified Stock từ ICE, trích xuất giá trị 
    'Total in Bags', và lưu vào database cho một khoảng ngày.
    """
    from .models import IceData
    
    BASE_URL = "https://www.ice.com/publicdocs/futures_us_reports/coffee/coffee_cert_stock_{date_str}.XLS"
    
    current_date = start_date
    results = {'success_count': 0, 'not_found_count': 0, 'error_count': 0, 'total_days': (end_date - start_date).days + 1}
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        url = BASE_URL.format(date_str=date_str)
        
        total_in_bag_value = None
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code == 404:
                results['not_found_count'] += 1
                total_in_bag_value = None
            elif response.status_code == 200:
                
                data_io = BytesIO(response.content)
                
                try:
                    df = pd.read_excel(data_io, header=None)
                except Exception:
                    results['error_count'] += 1
                    current_date += timedelta(days=1)
                    continue 

                # 5. TÌM KIẾM HÀNG CHỨA GIÁ TRỊ CẦN THIẾT
                row_index = None
                
                # --- THỬ 1: TÌM CHUỖI CHÍNH XÁC: "Total in Bags" ---
                try:
                    df_filtered_bags = df[
                        df.astype(str).apply(
                            lambda x: x.str.contains('Total in Bags', case=False, na=False)
                        ).any(axis=1)
                    ]
                    row_index = df_filtered_bags.index[0]
                except IndexError:
                    # --- THỬ 2 (Fallback): TÌM CHUỖI RỘNG HƠN: "Total" ---
                    try:
                        df_filtered_total = df[
                            df.astype(str).apply(
                                lambda x: x.str.contains('Total', case=False, na=False)
                            ).any(axis=1)
                        ]
                        row_index = df_filtered_total.index[1]
                    except IndexError:
                        # Cả hai đều không tìm thấy
                        results['error_count'] += 1
                        current_date += timedelta(days=1)
                        continue # Chuyển sang ngày tiếp theo
                
                # --- TRÍCH XUẤT GIÁ TRỊ (Chỉ chạy khi tìm thấy row_index) ---
                try:
                    target_row = df.iloc[row_index]
                    
                    # Lấy giá trị cuối cùng không phải NaN/trống trong hàng đó.
                    value = target_row.dropna().iloc[-1]
                    
                    total_in_bag_value = str(value)
                    results['success_count'] += 1

                except Exception:
                    # Lỗi khi xử lý nội dung/trích xuất giá trị
                    results['error_count'] += 1
                    total_in_bag_value = None
            else:
                # Xử lý các lỗi HTTP khác
                results['error_count'] += 1
                total_in_bag_value = None
                
        except requests.exceptions.RequestException:
            # Xử lý lỗi kết nối/request
            results['error_count'] += 1
            total_in_bag_value = None
            
        # Lưu vào Database Django
        try:
            if total_in_bag_value is not None: 
                IceData.objects.update_or_create(
                    date=current_date,
                    defaults={'total_in_bag': total_in_bag_value}
                )
        except IntegrityError:
            pass 
        
        current_date += timedelta(days=1)
        
    return results

class ExportIceDataView(APIView):
    def get(self, request):
        try:
            # 1. Lấy dữ liệu
            ice_datas = IceData.objects.all().order_by('date')
            data = []
            
            for ice_data in ice_datas:
                # Định dạng date: DateField của Django là datetime.date object
                date_formatted = ice_data.date.strftime('%d/%m/%Y') if ice_data.date else ""
                
                # Xử lý trường hợp total_in_bag là None (NULL)
                total_in_bag_value = str(ice_data.total_in_bag) if ice_data.total_in_bag is not None else ''

                data.append({
                    'date': date_formatted,
                    'total_in_bag': total_in_bag_value
                })
            
            df = pd.DataFrame(data)
            
            # 2. Định nghĩa tên file và đường dẫn cục bộ
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
            filename = f"ice_data_export_{timestamp}.xlsx"
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
                worksheet.merge_cells('A1:B2') 
                worksheet['A1'] = 'SCHEDULE'
                worksheet['A1'].font = header_font
                worksheet['A1'].alignment = center_align
                
                # Dòng 3: Headers
                headers = ['DATE', 'TOTAL IN BAG']
                
                for col, header in enumerate(headers, 1):
                    cell = worksheet.cell(row=3, column=col, value=header)
                    cell.font = header_font
                    cell.alignment = center_align
                
                # Ghi dữ liệu
                if not df.empty:
                    for r_idx, row_data in enumerate(df.itertuples(), 4):
                        # Ghi dữ liệu ngày (cột 1)
                        worksheet.cell(row=r_idx, column=1, value=row_data[1])
                        # Ghi dữ liệu total_in_bag (cột 2)
                        worksheet.cell(row=r_idx, column=2, value=row_data[2])
                        
                # Tùy chỉnh độ rộng cột
                worksheet.column_dimensions['A'].width = 15
                worksheet.column_dimensions['B'].width = 20
            
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
