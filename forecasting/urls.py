from django.urls import path

from .views import CoffeeForecastView

urlpatterns = [
    path('coffee-forecast', CoffeeForecastView.post, name='coffee-forecast'),
]
 