from django.urls import path

from .views import ScanHistoryView
from .weather_forecast_views import WeatherForecastView

urlpatterns = [
    path('update/', ScanHistoryView.manage_keywords, name='manage-keywords'),
    path('get-weather-forecast/', WeatherForecastView.get_weather_forecast, name='get-weather-forecast'),
]
