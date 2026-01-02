from django.urls import path

from .views import SearchGGView, KCDataStockJsonToExcel, RCDataStockView
from .create_prompt_views import CreatePromptView
from .ft_search_views import FTSearchView
from .afr_search_views import AfrSearchView
from .tvdatafeed_views import TVGetDatafeedView, TVUnfilledGapView

from .icedata_api import IceDataViewSet, ExportIceDataView
from .icedata_rc_api import ImportLocalIceRCDataView, ExportIceRCDataView

urlpatterns = [
    # path('', MarketAgentView.post, name='market-agent'),
    path('create-prompt', CreatePromptView.post, name='create-prompt'),
    path('ft-search', FTSearchView.post, name='ft-search'),
    path('afr-search', AfrSearchView.post, name='afr-search'),
    path('gg-search', SearchGGView.get, name='gg-search'),
    path('get-datafeed', TVGetDatafeedView.post, name='get-datafeed'),
    path('get-datafeed-gap', TVUnfilledGapView.post, name='get-datafeed-gap'),

    path('get-ice-data', IceDataViewSet.as_view(), name='get-ice-data'),
    path('export-ice-data', ExportIceDataView.as_view(), name='export-ice-data'),

    path('get-ice-rc-data', ImportLocalIceRCDataView.as_view(), name='get-ice-rc-data'),
    path('export-ice-rc-data', ExportIceRCDataView.as_view(), name='export-ice-rc-data'),

    path('export-kc-stock-data', KCDataStockJsonToExcel.post, name='export-kc-stock-data'),

    path('export-rc-stock-data', RCDataStockView.post, name='export-rc-stock-data'),
]
