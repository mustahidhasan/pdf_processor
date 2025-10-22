from django.db import models
from django.contrib.auth.models import User
from user.models import UploadedFile  # Original uploaded PDFs


# 🔹 Helper functions for organized Azure Blob storage paths
def processed_image_path(instance, filename):
    """
    Store images under:
    processed_files/<username>/<uploaded_file_id>/<filename>
    """
    return f"processed_files/{instance.uploaded_file.user.username}/{instance.uploaded_file.id}/{filename}"


def processed_pdf_path(instance, filename):
    """
    Store processed PDFs under:
    processed_img_pdf/<username>/<filename>
    """
    return f"processed_img_pdf/{instance.user.username}/{filename}"


# 🔹 Model for each extracted page as an image
class ProcessedImage(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedFile,
        related_name="processed_images",
        on_delete=models.CASCADE
    )
    page_num = models.PositiveIntegerField()
    image = models.ImageField(upload_to=processed_image_path)
    is_split = models.BooleanField(default=False)  # Tracks if page has been split
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Page {self.page_num} - {'Split' if self.is_split else 'Unsplit'}"


# 🔹 Model for re-combined / processed PDF files
class ProcessedPDF(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    file_path = models.FileField(upload_to=processed_pdf_path)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Processed PDF {self.id} for {self.user.username}"
