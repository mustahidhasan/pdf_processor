from django.contrib import admin
from .models import ProcessedImage, ProcessedPDF

# Register your models here.
# admin.site.register(ProcessedImage)


class ProcessedPDFAdmin(admin.ModelAdmin):
    # Display fields in the list view
    list_display = ('id', 'user', 'uploaded_file', 'file_path', 'processed_at')
    
    # Add user-wise filtering option
    list_filter = ('user',)

    # Optionally, you can also allow search functionality on user or file
    search_fields = ('user__username', 'uploaded_file__file_name')

    # Optionally, allow the admin to display extra fields or modify the view further
    ordering = ('-processed_at',)  # Orders by processed_at field in descending order

# Register the custom admin class
admin.site.register(ProcessedPDF, ProcessedPDFAdmin)

