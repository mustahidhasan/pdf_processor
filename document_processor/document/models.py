from django.db import models
from django.contrib.auth.models import User
from user.models import UploadedFile  # Assuming you already have this model


class ProcessedImage(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedFile, related_name="processed_images", on_delete=models.CASCADE
    )
    page_num = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to="processed_files/"
    )  # Save images in the 'processed_files' directory under MEDIA_ROOT
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Page {self.page_num}"
