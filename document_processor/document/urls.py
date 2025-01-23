from django.urls import path
from . import views

urlpatterns = [
    path("<int:file_id>/", views.process, name="process"),
    path("process_pages/<int:file_id>/", views.process_pages, name="process_pages"),
    path("processed_doc/", views.processed_doc, name="processed_doc")
]
