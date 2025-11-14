from django.urls import path

from .views import MarketAgentView
from .create_prompt_views import CreatePromptView

urlpatterns = [
    path('', MarketAgentView.post, name='market-agent'),
    path('create-prompt', CreatePromptView.post, name='create-prompt'),
]
