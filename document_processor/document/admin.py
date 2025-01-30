from django.contrib import admin
from .models import ProcessedImage, ProcessedPDF

# Register your models here.
admin.site.register(ProcessedImage)
admin.site.register(ProcessedPDF)
