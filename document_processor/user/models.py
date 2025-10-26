# user/models.py
from django.db import models
from django.contrib.auth.models import User
from document_processor.storages_backends import AzureMediaStorage

class UploadedFile(models.Model):
    file = models.FileField(
        upload_to="uploads/",
        storage=AzureMediaStorage()  # Force Azure storage for testing
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name
