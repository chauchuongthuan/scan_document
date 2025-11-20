from django.urls import path

from .api import RainPrecipView, ExportRainPrecipView, DownLoadFileFromCoastwWatch

urlpatterns = [
    path('api/rain-precip/', RainPrecipView.as_view(), name='rain-precip'),
    path('api/export-rain-precip/', ExportRainPrecipView.as_view(), name='export-rain-precip'),
    path('api/download-file-from-coastwatch/', DownLoadFileFromCoastwWatch.as_view(), name='download-file-from-coastwatch'),

]
