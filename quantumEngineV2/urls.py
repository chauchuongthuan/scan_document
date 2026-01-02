from django.urls import path

from .views import quantum_dashboard, analyze_numerical, analyze_text_input

urlpatterns = [
    path('', quantum_dashboard, name='quantum-dashboard-v2'),
    # path('import-history', import_data_historical, name='quantum-import-history'),

    path('api/analyze-numerical', analyze_numerical, name='api-analyze-numerical'),
    path('api/analyze-text', analyze_text_input, name='api-analyze-text'),
]