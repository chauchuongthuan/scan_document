from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .weather_forecast import process_weather_forecast
from .models import WeatherProblemHistory, CoffeeRegionWeatherForecast
from .weather_forecast_service import export_history_weather_forecast_service
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
import docx
import re
import os
import openpyxl

class WeatherForecastView:
    @login_required(login_url="login_cms")
    def get_weather_forecast(request):
        if request.method == 'POST':
            try:
                INPUT_FILENAME = "C:/Users/COMPUTER/Desktop/Coffee Regions.xlsx" # Đảm bảo tên file chính xác
                OUTPUT_FILENAME = f"D:/PER_WORKSPACE/scan_document/media/coffee_regions_weather/coffee_regions_weather_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
                process_weather_forecast(INPUT_FILENAME, OUTPUT_FILENAME)
                return JsonResponse({
                        "status": "success",
                        "message": "Lấy dữ liệu thành công!",
                        "result": f"/media/coffee_regions_weather/coffee_regions_weather_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
                    }, status=200)
            except Exception as e:
                return JsonResponse({
                        "status": "error",
                        "message": f"Lấy dữ liệu thất bại: {str(e)}"
                    }, status=400)
        return render(request, "weather_forecast/get-weather-forecast.html")

    def _apply_filters(queryset, region, start_date, end_date):
        """Hàm bổ trợ lọc dữ liệu theo region, start_date, end_date (tùy chọn)"""
        if region:
            queryset = queryset.filter(region__icontains=region.strip())
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_dt)
            except ValueError:
                pass
        return queryset

    @login_required(login_url="login_cms")
    def list_data_weather_problem_history(request):
        per_page_options = [10, 25, 50, 100]
        per_page = request.GET.get('per_page', 50)
        
        # Lấy thông số filter từ GET hoặc POST
        region = request.GET.get('region') or request.POST.get('region', '')
        start_date = request.GET.get('start_date') or request.POST.get('start_date', '')
        end_date = request.GET.get('end_date') or request.POST.get('end_date', '')

        queryset = WeatherProblemHistory.objects.all().order_by('-date', '-coffee_region_id')
        queryset = WeatherForecastView._apply_filters(queryset, region, start_date, end_date)
        
        paginator = Paginator(queryset, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'datas': page_obj,
            'per_page_options': per_page_options,
            'per_page': int(per_page),
            'region': region,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request, 'weather_forecast/list_history.html', context)

    @login_required(login_url="login_cms")
    def export_history_weather_forecast(request):
        try:
            # Lấy tham số từ URL query
            region = request.GET.get('region', '').strip()
            start_date = request.GET.get('start_date', '').strip()
            end_date = request.GET.get('end_date', '').strip()

            filters = {
                'region': region,
                'start_date': start_date,
                'end_date': end_date,
            }

            print(f"📥 [VIEW LOG] Bắt đầu xử lý Export với bộ lọc: {filters}")
            file_name = f"history_weather_forecast_problem_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.xlsx"
            # Gọi service tạo file
            file_path = export_history_weather_forecast_service(output_directory="media/weather_problem", file_name_str=file_name, filters=filters)
            
            # Kiểm tra file sinh ra
            if not file_path or not os.path.exists(file_path):
                print("⚠️ [VIEW LOG] File không tồn tại hoặc dữ liệu trống.")
                return JsonResponse({
                    "status": "error",
                    "message": "Không tìm thấy dữ liệu phù hợp với bộ lọc để xuất file Excel!"
                }, status=400)

            # Trả về FileResponse trực tiếp để trình duyệt tự kích hoạt Download
            file_name = os.path.basename(file_path)
            response = FileResponse(
                open(file_path, 'rb'), 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response

        except Exception as e:
            print(f"❌ [VIEW ERROR] Lỗi tại export_history_weather_forecast View: {str(e)}")
            return JsonResponse({
                "status": "error", 
                "message": f"Lỗi hệ thống khi export file: {str(e)}"
            }, status=500)
    @login_required(login_url="login_cms")
    def import_history_weather_forecast(request):
        if request.method != "POST" or not request.FILES.get('docx_file'):
            return JsonResponse({"status": "error", "message": "Vui lòng chọn file .docx hợp lệ!"}, status=400)

        file = request.FILES['docx_file']
        if not file.name.endswith('.docx'):
            return JsonResponse({"status": "error", "message": "Định dạng file không hỗ trợ, vui lòng tải lên file .docx!"}, status=400)

        try:
            doc = docx.Document(file)
            current_date = None
            records_created = 0

            date_pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{4})$")
            data_pattern = re.compile(
                r"^Country:\s*(?P<country>[^,]+),\s*Region:\s*(?P<region>[^:]+):\s*(?P<index>[-?\d.]+)(?:\s*:|\s*->)\s*(?P<note>.+)$"
            )

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue

                date_match = date_pattern.match(text)
                if date_match:
                    current_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
                    continue

                data_match = data_pattern.match(text)
                if data_match and current_date:
                    country = data_match.group('country').strip()
                    region_str = data_match.group('region').strip()
                    index_val = float(data_match.group('index'))
                    note = data_match.group('note').strip()

                    # Lấy hoặc tự động tạo region object để đảm bảo luôn có khóa ngoại
                    region_obj, _ = CoffeeRegionWeatherForecast.objects.get_or_create(
                        region=region_str,
                        defaults={'country': country}
                    )

                    WeatherProblemHistory.objects.update_or_create(
                        country=country,
                        region=region_str,      
                        coffee_region=region_obj,
                        date=current_date,
                        defaults={
                            'frost_drought_index': index_val,
                            'note': note
                        }
                    )
                    records_created += 1

            return JsonResponse({
                "status": "success",
                "message": f"Import thành công {records_created} bản ghi dữ liệu lịch sử thời tiết!"
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Lỗi khi xử lý file .docx: {str(e)}"}, status=500)