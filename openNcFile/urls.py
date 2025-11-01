from django.urls import path

from .api import RainPrecipView, ExportRainPrecipView

urlpatterns = [
    path('api/rain-precip/', RainPrecipView.as_view(), name='rain-precip'),
    path('api/export-rain-precip/', ExportRainPrecipView.as_view(), name='export-rain-precip'),
]
