import PyPDF2
from django.shortcuts import render, get_object_or_404, redirect
from user.models import UploadedFile
import os
from django.conf import settings
from django.contrib import messages

def process(request, file_id):
    # Get the file from the database
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Path to the PDF file
    file_path = uploaded_file.file.path

    # Extract the pages from the PDF
    extracted_pages = []
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                extracted_pages.append({
                    'page_num': page_num + 1,
                    'page_content': page.extract_text(),
                    'file_path': file_path,  # Can also be used to generate page images if required
                })
    except Exception as e:
        messages.error(request, f"Error processing PDF: {str(e)}")
        return redirect("home")

    # Send the extracted pages to the template
    return render(request, "process.html", {"uploaded_file": uploaded_file, "extracted_pages": extracted_pages})

def process_pages(request, file_id):
    # Ensure the file is retrieved only for the logged-in user
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Process the selected pages
    selected_pages = request.POST.getlist("selected_pages")

    if selected_pages:
        # Here you can process the selected pages, for example, combining them or saving images, etc.
        messages.success(request, f"Successfully processed pages: {', '.join(selected_pages)}")
    else:
        messages.error(request, "No pages selected for processing.")
    
    # Redirect to the home page or another appropriate page
    return redirect("home")

