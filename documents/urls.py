from django.urls import path

from documents.views import DocumentListView

urlpatterns = [
    path('', DocumentListView.list_documents, name='document-list'),
    path('create/', DocumentListView.create_document, name='document-create'),
    path('<uuid:pk>/', DocumentListView.document_detail, name='document-detail'),
    path('<uuid:pk>/update/', DocumentListView.update_document, name='document-update'),
    path('<uuid:pk>/delete/', DocumentListView.delete_document, name='document-delete'),
    path('import-excel/', DocumentListView.import_excel, name='document-import-excel'),
    path('scan-pdf/', DocumentListView.scan_pdf, name='document-scan-pdf'),
    path('export-excel/', DocumentListView.export_excel, name='document-export-excel'),
]
