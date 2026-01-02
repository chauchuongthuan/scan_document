from django.urls import path
from .views import ChartView 
urlpatterns = [
    path('get-chart-json-kc/', ChartView.get_chart_json_kc, name='get-chart-json-kc'),
    path('view-chart-kc/', ChartView.view_chart_kc, name='view-chart-kc'),
    path('get-chart-json-rc/', ChartView.get_chart_json_rc, name='get-chart-json-rc'),
    path('view-chart-rc/', ChartView.view_chart_rc, name='view-chart-rc'),
]