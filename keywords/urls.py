from django.urls import path

from .views import KeywordListView

urlpatterns = [
    path('', KeywordListView.keyword, name='keyword-create'),
]
