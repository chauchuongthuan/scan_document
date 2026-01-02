from django.urls import path

from documents.views import DocumentListView

urlpatterns = [
    path('', DocumentListView.list_documents, name='document-list'),
    path('create/', DocumentListView.create_document, name='document-create'),
    path('import-excel/', DocumentListView.import_excel, name='document-import-excel'),
    path('export-excel/', DocumentListView.export_excel, name='document-export-excel'),
]
