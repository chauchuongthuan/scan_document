from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .weather_forecast import process_weather_forecast

from datetime import datetime
from django.http import JsonResponse
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
        return render(request, "weather_forecast.html/get-weather-forecast.html")
