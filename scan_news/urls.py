from django.urls import path

from .views import ScanHistoryView

urlpatterns = [
    path('update/', ScanHistoryView.manage_keywords, name='manage-keywords'),
]
