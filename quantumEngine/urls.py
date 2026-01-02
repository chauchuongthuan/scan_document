from django.urls import path

from .views import quantum_dashboard, import_data_historical

urlpatterns = [
    path('', quantum_dashboard, name='quantum-dashboard'),
    path('import-history', import_data_historical, name='quantum-import-history'),
]