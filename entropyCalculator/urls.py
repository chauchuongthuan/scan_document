from django.urls import path

from .views import CalculateEntropyByParagraphView, CalculateEntropyAllParagraphView

urlpatterns = [
    path('calculate', CalculateEntropyByParagraphView.post, name='calculate-entropy'),
    path('calculate-all-paragraph', CalculateEntropyAllParagraphView.post, name='calculate-entropy-all-paragraph'),
]
