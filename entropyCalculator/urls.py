from django.urls import path

from .views import CalculateEntropyByEachParagraphView, CalculateEntropyAllParagraphView, CalculateEntropyByEachParagraphViewV2, CalculateEntropyByEachParagraphViewV3, CalculateEntropyByEachParagraphViewV4
from .view_expand import CalculateEntropyByEachParagraphViewV5
from .view_test import PredictTodayMarketMoveView, GetMarketDataView
urlpatterns = [
    path('calculate', CalculateEntropyByEachParagraphView.post, name='calculate-entropy'),
    path('calculate-all-paragraph', CalculateEntropyAllParagraphView.post, name='calculate-entropy-all-paragraph'),
    path('calculate-v2', CalculateEntropyByEachParagraphViewV2.post, name='calculate-entropy-v2'),
    path('calculate-v3', CalculateEntropyByEachParagraphViewV3.post, name='calculate-entropy-v3'),
    path('calculate-v4', CalculateEntropyByEachParagraphViewV4.post, name='calculate-entropy-v4'),
    path('calculate-v5', CalculateEntropyByEachParagraphViewV5.post, name='calculate-entropy-v5'),

    path('predict-today', PredictTodayMarketMoveView.post, name='predict-today'),
    path('get-market-data', GetMarketDataView.post, name='get-market-data'),
]
