# document/models.py
from django.db import models
from django.contrib.auth.models import User
from user.models import UploadedFile

def processed_image_path(instance, filename):
    return f"processed_files/{instance.uploaded_file.user.id}/{instance.uploaded_file.id}/{filename}"

def processed_pdf_path(instance, filename):
    return f"processed_img_pdf/{instance.user.id}/{filename}"

class ProcessedImage(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, related_name="processed_images", on_delete=models.CASCADE)
    page_num = models.PositiveIntegerField()
    image = models.ImageField(upload_to=processed_image_path)
    is_split = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ProcessedPDF(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    file_path = models.FileField(upload_to=processed_pdf_path)
    processed_at = models.DateTimeField(auto_now_add=True)
