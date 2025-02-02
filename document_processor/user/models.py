from django.db import models
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    file = models.FileField(
        upload_to="uploads/"
    )  # Files will be stored in the "uploads/" directory
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )  # Auto timestamp for when the file was uploaded
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # Associate each file with a specific user
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name
