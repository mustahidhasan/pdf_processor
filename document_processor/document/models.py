from django.db import models
from django.contrib.auth.models import User
from user.models import UploadedFile
from document_processor.storages_backends import AzureMediaStorage

class ProcessedImage(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedFile, related_name="processed_images", on_delete=models.CASCADE
    )
    page_num = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to="processed_files/",
        storage=AzureMediaStorage()  # Force Azure storage
    )
    is_split = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Page {self.page_num} - {'Split' if self.is_split else 'Unsplit'}"


class ProcessedPDF(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    file_path = models.FileField(
        upload_to="processed_img_pdf/",
        storage=AzureMediaStorage()  # Force Azure storage
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Processed PDF {self.id} for {self.user.username}"
