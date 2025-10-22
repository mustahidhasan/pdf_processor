import os
import uuid
from io import BytesIO

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth.models import User

from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_bytes

from user.models import UploadedFile
from .models import ProcessedImage, ProcessedPDF


# ------------------- PROCESS PDF → IMAGES -------------------

@login_required
def process(request, file_id):
    """Convert PDF to images and save to Azure Blob."""
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)

    if not processed_pages.exists():
        try:
            with default_storage.open(uploaded_file.file.name, "rb") as f:
                pdf_bytes = f.read()

            images = convert_from_bytes(pdf_bytes, 300)
            for page_num, image in enumerate(images):
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                img_obj = ProcessedImage(uploaded_file=uploaded_file, page_num=page_num+1, is_split=False)
                img_obj.image.save(f"processed_files/{uploaded_file.id}/page_{page_num+1}.png", ContentFile(buffer.read()), save=True)

            processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)
        except Exception as e:
            messages.error(request, f"Error processing PDF: {str(e)}")
            return redirect("home")

    pages = [{"page_num": p.page_num, "image_url": p.image.url, "is_split": p.is_split} for p in processed_pages]
    return render(request, "process.html", {"uploaded_file": uploaded_file, "extracted_pages": pages})


# ------------------- SPLIT / COMBINE PDF -------------------

@csrf_exempt
def process_pages(request, file_id):
    """Combine selected pages into PDF and save to Azure Blob."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    selected_groups = request.POST.getlist("selected_groups")
    if not selected_groups:
        return JsonResponse({"error": "No pages selected"}, status=400)

    try:
        with default_storage.open(uploaded_file.file.name, "rb") as f:
            pdf_bytes = f.read()
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        pdf_writer = PdfWriter()

        for group in selected_groups:
            pages = parse_page_group(group)
            for p in pages:
                pdf_writer.add_page(pdf_reader.pages[p-1])

        buffer = BytesIO()
        pdf_writer.write(buffer)
        buffer.seek(0)

        unique_name = f"processed_{file_id}_{request.user.id}_{uuid.uuid4().hex}.pdf"
        processed_pdf = ProcessedPDF.objects.create(user=request.user, uploaded_file=uploaded_file)
        processed_pdf.file_path.save(f"processed_img_pdf/{unique_name}", ContentFile(buffer.read()), save=True)

        # Mark pages as split
        for group in selected_groups:
            pages = parse_page_group(group)
            ProcessedImage.objects.filter(uploaded_file=uploaded_file, page_num__in=pages).update(is_split=True)

        return JsonResponse({
            "message": "PDF processed successfully.",
            "processed_pdf_url": processed_pdf.file_path.url
        })

    except Exception as e:
        return JsonResponse({"error": f"Failed to process PDF: {e}"}, status=500)


def parse_page_group(group):
    """Convert '1-3,5' → [1,2,3,5]."""
    pages = []
    for part in group.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end+1))
        else:
            pages.append(int(part))
    return pages


# ------------------- PROCESSED DOCUMENTS -------------------

@login_required
def processed_doc(request):
    """List processed/unprocessed documents."""
    user = request.user
    unprocessed_files = UploadedFile.objects.filter(user=user, is_archieved=False)\
        .exclude(id__in=ProcessedImage.objects.values_list("uploaded_file_id", flat=True))\
        .order_by("-uploaded_at")
    processed_files = ProcessedPDF.objects.filter(user=user).order_by("-processed_at")
    return render(request, "processed_document.html", {"unprocessed_files": unprocessed_files, "grouped_processed_files": processed_files})


@login_required
def delete_document(request, file_id):
    """Delete processed PDF."""
    if request.method == "POST":
        processed_pdf = ProcessedPDF.objects.filter(id=file_id).first()
        if processed_pdf:
            processed_pdf.delete()
            messages.success(request, "Document deleted successfully.")
        else:
            messages.error(request, "Document not found.")
        return redirect("processed_doc")
    return redirect("processed_doc")


@csrf_exempt
def upload_pdfs(request):
    """Upload PDFs via external webhook."""
    if request.method == "POST":
        sender_email = request.POST.get("sender_email_address")
        files = request.FILES.getlist("files")
        if not sender_email or not files:
            return JsonResponse({"error": "Email and files required"}, status=400)

        try:
            user = User.objects.get(email=sender_email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Email not associated with any user."}, status=400)

        for file in files:
            UploadedFile.objects.create(file=file, user=user)

        return JsonResponse({"message": "Files uploaded successfully.",
                             "uploaded_files": [{"file_name": f.name} for f in files]}, status=201)

    return JsonResponse({"error": "Invalid request method."}, status=405)
