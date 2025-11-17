from django.urls import path

from .views import MarketAgentView
from .create_prompt_views import CreatePromptView
from .ft_search_views import FTSearchView
from .afr_search_views import AfrSearchView
urlpatterns = [
    path('', MarketAgentView.post, name='market-agent'),
    path('create-prompt', CreatePromptView.post, name='create-prompt'),
    path('ft-search', FTSearchView.post, name='ft-search'),
    path('afr-search', AfrSearchView.post, name='afr-search'),
]
