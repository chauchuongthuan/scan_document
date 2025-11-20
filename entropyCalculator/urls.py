from django.urls import path

from .views import CalculateEntropyByEachParagraphView, CalculateEntropyAllParagraphView, CalculateEntropyByEachParagraphViewV2

urlpatterns = [
    path('calculate', CalculateEntropyByEachParagraphView.post, name='calculate-entropy'),
    path('calculate-all-paragraph', CalculateEntropyAllParagraphView.post, name='calculate-entropy-all-paragraph'),
    path('calculate-v2', CalculateEntropyByEachParagraphViewV2.post, name='calculate-entropy-v2'),
]
