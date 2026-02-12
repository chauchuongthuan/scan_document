from django.urls import path
from .views import RevenueView, RevenueByHourView
# from documents.views import DocumentListView
from .api import RevenueAPIView, GetSumTotalOf7DaysEveryHourAPIView
urlpatterns = [
    path('api/fetch-and-sync-revenue', RevenueAPIView.as_view(), name='fetch-and-sync-revenue'),
    path('api/get-sum-total-of-7-days-every-hour', GetSumTotalOf7DaysEveryHourAPIView.as_view(), name='get-sum-total-of-7-days-every-hour'),

    path('', RevenueView.revenue_list, name='revenue-list'),
    path('by-hour', RevenueByHourView.revenue_by_hour_list, name='revenue-by-hour-list'),
]
