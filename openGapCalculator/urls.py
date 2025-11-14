from django.urls import path

from .views import RCOpenGapCalculatorView
from .api import check_gap_kcc1
urlpatterns = [
    path('rc/', RCOpenGapCalculatorView.post, name='rc-open-gap-calculator'),
    path('api-kcc1/', check_gap_kcc1, name='api-kcc1-open-gap-calculator'),
]
