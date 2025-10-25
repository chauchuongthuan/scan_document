from django.urls import path

from .views import CalculateViralPotentialView

urlpatterns = [
    path('calculate-viral-potential', CalculateViralPotentialView.post, name='calculate-viral-potential'),
]
