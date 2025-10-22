from django.db import models
from django.contrib.auth.models import User


# 🔹 Helper to organize uploaded PDFs per user
def user_upload_path(instance, filename):
    """
    Save uploaded PDFs under:
    uploaded_files/<username>/<filename>
    """
    return f"uploaded_files/{instance.user.username}/{filename}"


class UploadedFile(models.Model):
    file = models.FileField(upload_to=user_upload_path)  # dynamic path per user
    uploaded_at = models.DateTimeField(auto_now_add=True)  # timestamp when uploaded
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # owner of the file
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)  # soft delete / archive flag

    def __str__(self):
        return self.file.name
