from django.urls import path
from . import views

urlpatterns = [
    path("<int:file_id>/", views.process, name="process"),
    path("process_pages/<int:file_id>/", views.process_pages, name="process_pages"),
    path("processed_doc/", views.processed_doc, name="processed_doc"),
    path("delete/<int:file_id>/", views.delete_document, name="delete_document"),
    path("api/upload_pdfs/", views.upload_pdfs, name="upload_pdfs"),
]
