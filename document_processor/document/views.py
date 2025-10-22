import os
import uuid
import requests
from io import BytesIO
from itertools import groupby
from operator import attrgetter

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from PyPDF2 import PdfWriter, PdfReader
from pdf2image import convert_from_path

from user.models import UploadedFile
from .models import ProcessedImage, ProcessedPDF


@login_required
def process(request, file_id):
    """Convert uploaded PDF to images and save to Azure Blob."""
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    file_path = uploaded_file.file.path  # Django downloads it from Azure if needed

    processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)

    if not processed_pages.exists():
        try:
            images = convert_from_path(file_path, 300)

            for page_num, image in enumerate(images):
                # Save image to Azure Blob using ContentFile
                img_buffer = BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                processed_img = ProcessedImage(
                    uploaded_file=uploaded_file,
                    page_num=page_num + 1,
                    is_split=False,
                )
                processed_img.image.save(
                    f"processed_files/{uploaded_file.id}/page_{page_num + 1}.png",
                    ContentFile(img_buffer.read()),
                    save=True
                )

            processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)

        except Exception as e:
            messages.error(request, f"Error processing PDF: {str(e)}")
            return redirect("home")

    extracted_pages = [
        {
            "page_num": page.page_num,
            "image_url": page.image.url,  # ✅ Correct Azure URL
            "is_split": page.is_split,
        }
        for page in processed_pages
    ]

    return render(request, "process.html", {
        "uploaded_file": uploaded_file,
        "extracted_pages": extracted_pages,
    })


@csrf_exempt
def process_pages(request, file_id):
    """Split, combine, and upload processed PDFs to Azure Blob."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    # Retrieve JWT session data
    token = request.session.get("jwt_token")
    payload = request.session.get("jwt_payload")
    expiration = request.session.get("jwt_expiration")

    if not token or not payload:
        messages.error(request, "No valid session found. Please log in again.")
        return redirect("login")

    user_email = payload.get("sub")
    if not user_email:
        return JsonResponse({"error": "JWT payload missing 'sub' (user email)."}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "User is not authenticated."}, status=401)

    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    selected_groups = request.POST.getlist("selected_groups")
    sender_email = request.user.email

    if not selected_groups:
        return JsonResponse({"error": "No page groups selected."}, status=400)
    if not sender_email:
        return JsonResponse({"error": "Sender email is required."}, status=400)

    original_pdf_path = uploaded_file.file.path
    webhook_url = "https://backend-webhooks.azurewebsites.net/api/gmail_backend_webhook2"

    try:
        pdf_reader = PdfReader(original_pdf_path)
        pdf_writer = PdfWriter()

        for group in selected_groups:
            try:
                pages = parse_page_group(group)
                for page_num in pages:
                    pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            except ValueError:
                return JsonResponse({"error": f"Invalid page group: {group}"}, status=400)

        # Generate PDF and upload to Azure Blob
        pdf_buffer = BytesIO()
        pdf_writer.write(pdf_buffer)
        pdf_buffer.seek(0)

        unique_filename = f"processed_{file_id}_{request.user.id}_{uuid.uuid4().hex}.pdf"

        processed_pdf = ProcessedPDF.objects.create(
            user=request.user,
            uploaded_file=uploaded_file,
        )

        processed_pdf.file_path.save(
            f"processed_img_pdf/{unique_filename}",
            ContentFile(pdf_buffer.read()),
            save=True
        )

        # Mark pages as split
        for group in selected_groups:
            pages = parse_page_group(group)
            ProcessedImage.objects.filter(uploaded_file=uploaded_file, page_num__in=pages).update(is_split=True)

        # Send the processed PDF via webhook
        headers = {"sender_name": sender_email}
        try:
            with default_storage.open(processed_pdf.file_path.name, "rb") as new_pdf:
                files = {"file": new_pdf}
                response = requests.post(webhook_url, headers=headers, files=files)

            if response.status_code != 200:
                return JsonResponse(
                    {"error": f"Failed to send PDF: {response.status_code} {response.text}"},
                    status=500,
                )

        except Exception as e:
            return JsonResponse({"error": f"Failed to send PDF: {e}"}, status=500)

        return JsonResponse({
            "message": "PDF processed successfully.",
            "processed_pdf_url": processed_pdf.file_path.url,  # ✅ Azure Blob URL
            "continue_selection": True,
        })

    except Exception as e:
        return JsonResponse({"error": f"Failed to process PDF: {e}"}, status=500)


def parse_page_group(group):
    """Parse page group input like '1-3,5' → [1,2,3,5]."""
    pages = []
    parts = group.split(",")
    for part in parts:
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages


@login_required
def processed_doc(request):
    """Show processed and unprocessed documents for the logged-in user."""
    user = request.user

    unprocessed_files = (
        UploadedFile.objects.filter(user=user, is_archieved=False)
        .exclude(id__in=ProcessedImage.objects.values_list("uploaded_file_id", flat=True))
        .order_by("-uploaded_at")
    )

    grouped_processed_files = ProcessedPDF.objects.filter(user=user).order_by("-processed_at")

    return render(
        request,
        "processed_document.html",
        {
            "unprocessed_files": unprocessed_files,
            "grouped_processed_files": grouped_processed_files,
        },
    )


@login_required
def delete_document(request, file_id):
    """Delete processed document (and its Azure blob file)."""
    if request.method == "POST":
        get_processed_file = ProcessedPDF.objects.filter(id=file_id).first()
        if get_processed_file:
            get_processed_file.delete()
            messages.success(request, "Document deleted successfully.")
        else:
            messages.error(request, "Document not found.")
        return redirect("processed_doc")

    return redirect("processed_doc")


@csrf_exempt
def upload_pdfs(request):
    """Handle webhook uploads from external service."""
    if request.method == "POST":
        sender_email = request.POST.get("sender_email_address")
        files = request.FILES.getlist("files")

        if not sender_email or not files:
            return JsonResponse(
                {"error": "Email address and files are required."}, status=400
            )

        try:
            user = User.objects.get(email=sender_email)
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "Email address not associated with any user."}, status=400
            )

        for file in files:
            UploadedFile.objects.create(file=file, user=user)

        return JsonResponse(
            {
                "message": "Files uploaded successfully.",
                "uploaded_files": [{"file_name": file.name} for file in files],
            },
            status=201,
        )

    return JsonResponse({"error": "Invalid request method."}, status=405)
