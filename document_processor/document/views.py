import os
from django.shortcuts import render, get_object_or_404, redirect
from user.models import UploadedFile
from pdf2image import convert_from_path
from django.contrib import messages
from django.conf import settings

def process(request, file_id):
    # Get the file from the database
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Path to the PDF file
    file_path = uploaded_file.file.path

    # Directory to save the generated images under MEDIA_ROOT
    image_dir = os.path.join(settings.MEDIA_ROOT, "processed_files", str(uploaded_file.id))
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Convert PDF to images
    extracted_pages = []
    try:
        images = convert_from_path(file_path, 300)  # 300 DPI for better quality images
        for page_num, image in enumerate(images):
            # Save each page as an image file in the processed_files directory
            image_filename = f"page_{page_num + 1}.png"
            image_path = os.path.join(image_dir, image_filename)
            image.save(image_path, "PNG")
            
            # Generate the relative URL for the image to use in the template
            image_url = os.path.join("media", "processed_files", str(uploaded_file.id), image_filename)
            
            extracted_pages.append({
                'page_num': page_num + 1,
                'image_url': image_url,  # URL to display the image
            })
    except Exception as e:
        messages.error(request, f"Error processing PDF: {str(e)}")
        return redirect("home")

    # Send the extracted pages (images) to the template
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
