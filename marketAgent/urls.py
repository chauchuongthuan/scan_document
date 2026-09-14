from django.urls import path

from .views import KCDataStockJsonToExcel, RCDataStockView
from .create_prompt_views import CreatePromptView, GetCalculateMomentumView
from .create_prompt_chunk_views import CreatePromptView2
from .create_prompt_IG_views import InformationGeometryAnalyzerView
from .create_prompt_header_views import CreatePromptForEachHeaderView
from .create_prompt_HB_views import CreatePromptHBView, GetEffectiveMomentumPromptHBView
from .tvdatafeed_views import TVGetDatafeedView, TVUnfilledGapView, GapKCDataView, GapRCDataView

from .icedata_api import IceDataViewSet, ExportIceDataView
from .icedata_rc_api import ImportLocalIceRCDataView, ExportIceRCDataView

urlpatterns = [
    # path('', MarketAgentView.post, name='market-agent'),
    path('create-prompt', CreatePromptView.post, name='create-prompt'),
    path('create-prompt-2', CreatePromptView2.post, name='create-prompt-2'),
    path('create-prompt-3', InformationGeometryAnalyzerView.post, name='create-prompt-3'),
    path('create-prompt-4', CreatePromptForEachHeaderView.post, name='create-prompt-4'),
    path('get-calculated-momentum', GetCalculateMomentumView.post, name='get-calculated-momentum'),

    path('create-prompt-HB', CreatePromptHBView.post, name='create-prompt-HB'),
    path('get-effective-momentum-HB', GetEffectiveMomentumPromptHBView.post, name='get-effective-momentum-HB'),

    path('get-datafeed', TVGetDatafeedView.post, name='get-datafeed'),
    path('get-datafeed-gap', TVUnfilledGapView.post, name='get-datafeed-gap'),

    path('get-ice-data', IceDataViewSet.as_view(), name='get-ice-data'),
    path('export-ice-data', ExportIceDataView.as_view(), name='export-ice-data'),

    path('get-ice-rc-data', ImportLocalIceRCDataView.as_view(), name='get-ice-rc-data'),
    path('export-ice-rc-data', ExportIceRCDataView.as_view(), name='export-ice-rc-data'),

    path('export-kc-stock-data', KCDataStockJsonToExcel.post, name='export-kc-stock-data'),

    path('export-rc-stock-data', RCDataStockView.post, name='export-rc-stock-data'),

    path('gap-kc', GapKCDataView.list_gap_kc, name='gap-kc-list'),
    path('export-gap-kc', GapKCDataView.export_excel, name='export-gap-kc-data'),

    path('gap-rc', GapRCDataView.list_gap_rc, name='gap-rc-list'),
    path('export-gap-rc', GapRCDataView.export_excel, name='export-gap-rc-data'),

]
