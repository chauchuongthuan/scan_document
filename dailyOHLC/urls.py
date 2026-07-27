from django.urls import path

from .views import OHLCDataKCDailyView, OHLCDataRCDailyView, ImpliedVolatilityView, OpenGapView
from .views_may import OHLCDataKCKDailyView, OHLCDataRCKDailyView
from .views_july import OHLCDataKCNDailyView, OHLCDataRCNDailyView
from .views_sep import OHLCDataKCUDailyView, OHLCDataRCUDailyView
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

    path('kck/', OHLCDataKCKDailyView.list_data_kck, name='daily-ohlc-kck-list'),
    path('kck/create/', OHLCDataKCKDailyView.create_data_kck, name='daily-ohlc-kck-create'),
    path('kck/import-excel/', OHLCDataKCKDailyView.import_excel_kck, name='daily-ohlc-kck-import-excel'),
    path('kck/export-excel/', OHLCDataKCKDailyView.export_excel, name='daily-ohlc-kck-export-excel'),
    path('<pk>/kck/delete/', OHLCDataKCKDailyView.delete_data_kck, name='daily-ohlc-kck-delete'),

    path('rck/', OHLCDataRCKDailyView.list_data_rck, name='daily-ohlc-rck-list'),
    path('rck/create/', OHLCDataRCKDailyView.create_data_rck, name='daily-ohlc-rck-create'),
    path('rck/import-excel/', OHLCDataRCKDailyView.import_excel_rck, name='daily-ohlc-rck-import-excel'),
    path('rck/export-excel/', OHLCDataRCKDailyView.export_excel, name='daily-ohlc-rck-export-excel'),
    path('<pk>/rck/delete/', OHLCDataRCKDailyView.delete_data_rck, name='daily-ohlc-rck-delete'),

    path('kcn/', OHLCDataKCNDailyView.list_data_kcn, name='daily-ohlc-kcn-list'),
    path('kcn/create/', OHLCDataKCNDailyView.create_data_kcn, name='daily-ohlc-kcn-create'),
    path('kcn/import-excel/', OHLCDataKCNDailyView.import_excel_kcn, name='daily-ohlc-kcn-import-excel'),
    path('kcn/export-excel/', OHLCDataKCNDailyView.export_excel, name='daily-ohlc-kcn-export-excel'),
    path('<pk>/kcn/delete/', OHLCDataKCNDailyView.delete_data_kcn, name='daily-ohlc-kcn-delete'),

    path('rcn/', OHLCDataRCNDailyView.list_data_rcn, name='daily-ohlc-rcn-list'),
    path('rcn/create/', OHLCDataRCNDailyView.create_data_rcn, name='daily-ohlc-rcn-create'),
    path('rcn/import-excel/', OHLCDataRCNDailyView.import_excel_rcn, name='daily-ohlc-rcn-import-excel'),
    path('rcn/export-excel/', OHLCDataRCNDailyView.export_excel, name='daily-ohlc-rcn-export-excel'),
    path('<pk>/rcn/delete/', OHLCDataRCNDailyView.delete_data_rcn, name='daily-ohlc-rcn-delete'),

    path('kcu/', OHLCDataKCUDailyView.list_data_kcu, name='daily-ohlc-kcu-list'),
    path('kcu/create/', OHLCDataKCUDailyView.create_data_kcu, name='daily-ohlc-kcu-create'),
    path('kcu/import-excel/', OHLCDataKCUDailyView.import_excel_kcu, name='daily-ohlc-kcu-import-excel'),
    path('kcu/export-excel/', OHLCDataKCUDailyView.export_excel, name='daily-ohlc-kcu-export-excel'),
    path('<pk>/kcu/delete/', OHLCDataKCUDailyView.delete_data_kcu, name='daily-ohlc-kcu-delete'),

    path('rcu/', OHLCDataRCUDailyView.list_data_rcu, name='daily-ohlc-rcu-list'),
    path('rcu/create/', OHLCDataRCUDailyView.create_data_rcu, name='daily-ohlc-rcu-create'),
    path('rcu/import-excel/', OHLCDataRCUDailyView.import_excel_rcu, name='daily-ohlc-rcu-import-excel'),
    path('rcu/export-excel/', OHLCDataRCUDailyView.export_excel, name='daily-ohlc-rcu-export-excel'),
    path('<pk>/rcu/delete/', OHLCDataRCUDailyView.delete_data_rcu, name='daily-ohlc-rcu-delete'),

    path('iv/', ImpliedVolatilityView.list_data_iv, name='daily-iv-list'),
    path('iv/create/', ImpliedVolatilityView.create_data_iv, name='daily-iv-create'),
    path('iv/import-excel/', ImpliedVolatilityView.import_excel_iv, name='daily-iv-import-excel'),
    path('iv/export-excel/', ImpliedVolatilityView.export_excel, name='daily-iv-export-excel'),
    path('<pk>/iv/delete/', ImpliedVolatilityView.delete_data_iv, name='daily-iv-delete'),

    path('open-gap/', OpenGapView.calculate_open_gap, name='open-gap'),
]
