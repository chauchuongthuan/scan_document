from django.urls import path

from .views import SearchGGView
from .create_prompt_views import CreatePromptView
from .ft_search_views import FTSearchView
from .afr_search_views import AfrSearchView
from .tvdatafeed_views import TVGetDatafeedView, TVUnfilledGapView
urlpatterns = [
    # path('', MarketAgentView.post, name='market-agent'),
    path('create-prompt', CreatePromptView.post, name='create-prompt'),
    path('ft-search', FTSearchView.post, name='ft-search'),
    path('afr-search', AfrSearchView.post, name='afr-search'),
    path('gg-search', SearchGGView.get, name='gg-search'),
    path('get-datafeed', TVGetDatafeedView.post, name='get-datafeed'),
    path('get-datafeed-gap', TVUnfilledGapView.post, name='get-datafeed-gap'),
]
 