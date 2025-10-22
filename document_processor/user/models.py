from django.db import models
from django.contrib.auth.models import User

def user_upload_path(instance, filename):
    return f"uploaded_files/{instance.user.id}/{filename}"  # store per user ID

class UploadedFile(models.Model):
    file = models.FileField(upload_to=user_upload_path)  # this will use Azure
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name
