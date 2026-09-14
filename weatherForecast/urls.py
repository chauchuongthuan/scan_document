from django.urls import path

from .views import WeatherForecastView

urlpatterns = [
    path('get-weather-forecast/', WeatherForecastView.get_weather_forecast, name='get-weather-forecast'),
    path('get-history-weather-forecast-problem/', WeatherForecastView.list_data_weather_problem_history, name='get-history-weather-forecast-problem'),
    path('import-history-weather-forecast-problem/', WeatherForecastView.import_history_weather_forecast, name='import-history-weather-forecast-problem'),
    path('export-history-weather-forecast-problem/', WeatherForecastView.export_history_weather_forecast, name='export-history-weather-forecast-problem'),
]
