import os
import requests
from django.shortcuts import render, get_object_or_404, redirect
from user.models import UploadedFile
from pdf2image import convert_from_path
from django.contrib import messages
from django.conf import settings
from .models import ProcessedImage  # Import the ProcessedImage model

from PyPDF2 import PdfWriter, PdfReader
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt


def process(request, file_id):
    # Get the file from the database for the current user
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Path to the PDF file (access the 'file' attribute for the actual file path)
    file_path = uploaded_file.file.path

    # Directory to save the generated images under MEDIA_ROOT
    image_dir = os.path.join(
        settings.MEDIA_ROOT, "processed_files", str(uploaded_file.id)
    )
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Convert PDF to images
    extracted_pages = []
    try:
        images = convert_from_path(file_path, 300)  # 300 DPI for better quality images
        for page_num, image in enumerate(images):
            # Save each page as an image file in the 'processed_files' folder under MEDIA_ROOT
            image_filename = f"page_{page_num + 1}.png"
            image_path = os.path.join(image_dir, image_filename)

            # Save the image to the filesystem
            image.save(image_path, "PNG")

            # Create a ProcessedImage entry in the database
            processed_image = ProcessedImage.objects.create(
                uploaded_file=uploaded_file,
                page_num=page_num + 1,
                image=f"processed_files/{uploaded_file.id}/{image_filename}",  # Store relative path in the database
            )

            # Generate the relative URL for the image to use in the template
            image_url = os.path.join("media", processed_image.image.name)
            print("line 43", image_url)
            extracted_pages.append(
                {
                    "page_num": page_num + 1,
                    "image_url": image_url,  # URL to display the image
                }
            )
    except Exception as e:
        messages.error(request, f"Error processing PDF: {str(e)}")
        return redirect("home")

    # Send the extracted pages (images) to the template
    return render(
        request,
        "process.html",
        {"uploaded_file": uploaded_file, "extracted_pages": extracted_pages},
    )


@csrf_exempt
def process_pages(request, file_id):
    if request.method == "POST":
        # Get the uploaded file and selected pages
        uploaded_file = get_object_or_404(
            UploadedFile, id=file_id
        )  # Assuming you have an UploadedFile model
        selected_pages = request.POST.getlist(
            "selected_pages"
        )  # List of selected page numbers as strings

        if not selected_pages:
            return JsonResponse({"error": "No pages selected."}, status=400)

        # Read the original PDF and extract the selected pages
        original_pdf_path = (
            uploaded_file.file.path
        )  # Assuming UploadedFile model has a `file` field

        # Define the directory and file path for the new PDF
        new_pdf_dir = os.path.join(settings.MEDIA_ROOT, "processed_img_pdf")
        new_pdf_path = os.path.join(new_pdf_dir, "new_file.pdf")

        # Ensure the directory exists
        if not os.path.exists(new_pdf_dir):
            os.makedirs(new_pdf_dir)

        try:
            pdf_reader = PdfReader(original_pdf_path)
            pdf_writer = PdfWriter()

            # Add selected pages to the new PDF
            for page_num in selected_pages:
                pdf_writer.add_page(
                    pdf_reader.pages[int(page_num) - 1]
                )  # Pages are zero-indexed

            # Save the new PDF
            with open(new_pdf_path, "wb") as output_pdf:
                pdf_writer.write(output_pdf)
        except Exception as e:
            return JsonResponse({"error": f"Failed to process PDF: {e}"}, status=500)

        # Send the new PDF to the webhook
        webhook_url = (
            "https://backend-webhooks.azurewebsites.net/api/gmail_backend_webhook2"
        )
        headers = {"sender_name": "info+yedaya@kabuta.biz"}

        try:
            with open(new_pdf_path, "rb") as new_pdf:
                response = requests.post(
                    webhook_url, headers=headers, files={"file": new_pdf}
                )

            # Check response from the webhook
            if response.status_code == 200:
                messages.success(request, "PDF processed and sent successfully.")
                return redirect("home")
            else:
                messages.error(
                    request, f"Webhook response: {response.status_code} {response.text}"
                )
                return redirect("home")
        except Exception as e:
            messages.error(request, f"Failed to send PDF: {e}")
            return redirect("home")
    return redirect("home")

def processed_doc(request):
    return render(request, "processed_document.html")