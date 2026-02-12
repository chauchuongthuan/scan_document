from django.urls import path

from .views import OHLCDataKCDailyView, OHLCDataRCDailyView, ImpliedVolatilityView, OpenGapView

urlpatterns = [
    path('kc/', OHLCDataKCDailyView.list_data_kc, name='daily-ohlc-kc-list'),
    path('kc/create/', OHLCDataKCDailyView.create_data_kc, name='daily-ohlc-kc-create'),
    path('kc/import-excel/', OHLCDataKCDailyView.import_excel_kc, name='daily-ohlc-kc-import-excel'),
    path('kc/export-excel/', OHLCDataKCDailyView.export_excel, name='daily-ohlc-kc-export-excel'),
    path('<pk>/kc/delete/', OHLCDataKCDailyView.delete_data_kc, name='daily-ohlc-kc-delete'),

    path('rc/', OHLCDataRCDailyView.list_data_rc, name='daily-ohlc-rc-list'),
    path('rc/create/', OHLCDataRCDailyView.create_data_rc, name='daily-ohlc-rc-create'),
    path('rc/import-excel/', OHLCDataRCDailyView.import_excel_rc, name='daily-ohlc-rc-import-excel'),
    path('rc/export-excel/', OHLCDataRCDailyView.export_excel, name='daily-ohlc-rc-export-excel'),
    path('<pk>/rc/delete/', OHLCDataRCDailyView.delete_data_rc, name='daily-ohlc-rc-delete'),

    path('iv/', ImpliedVolatilityView.list_data_iv, name='daily-iv-list'),
    path('iv/create/', ImpliedVolatilityView.create_data_iv, name='daily-iv-create'),
    path('iv/import-excel/', ImpliedVolatilityView.import_excel_iv, name='daily-iv-import-excel'),
    path('iv/export-excel/', ImpliedVolatilityView.export_excel, name='daily-iv-export-excel'),
    path('<pk>/iv/delete/', ImpliedVolatilityView.delete_data_iv, name='daily-iv-delete'),

    path('open-gap/', OpenGapView.calculate_open_gap, name='open-gap'),
]
