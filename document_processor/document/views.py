import io
import uuid
import threading
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from user.models import UploadedFile
from .models import ProcessedImage, ProcessedPDF


# --------------------------
# PDF-to-image processing
# --------------------------
def process(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Read PDF from Azure
    with uploaded_file.file.open("rb") as f:
        pdf_bytes = f.read()

    # Check if images were already processed
    processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)
    if not processed_pages.exists():
        try:
            images = convert_from_bytes(pdf_bytes, 300)
            for page_num, image in enumerate(images):
                img_io = io.BytesIO()
                image.save(img_io, format="PNG")

                img_content = ContentFile(
                    img_io.getvalue(),
                    name=f"processed_files/{uploaded_file.id}/page_{page_num + 1}.png",
                )

                processed_image = ProcessedImage.objects.create(
                    uploaded_file=uploaded_file,
                    page_num=page_num + 1,
                    image=img_content,
                    is_split=False,
                )
                print(f"Saved image URL: {processed_image.image.url}")

            processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)

        except Exception as e:
            messages.error(request, f"Error processing PDF: {str(e)}")
            return redirect("home")

    extracted_pages = [
        {
            "page_num": page.page_num,
            "image_url": page.image.url,
            "is_split": page.is_split,
        }
        for page in processed_pages
    ]

    return render(
        request,
        "process.html",
        {"uploaded_file": uploaded_file, "extracted_pages": extracted_pages},
    )


# --------------------------
# Helper to parse page groups
# --------------------------
def parse_page_group(group):
    pages = []
    for part in group.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages


# --------------------------
# Background PDF processing
# --------------------------
def process_pdf_task(user_id, file_id, selected_groups, sender_email):
    from django.contrib.auth.models import User
    from .models import ProcessedPDF, ProcessedImage
    from user.models import UploadedFile

    user = User.objects.get(id=user_id)
    uploaded_file = UploadedFile.objects.get(id=file_id)

    with uploaded_file.file.open("rb") as f:
        pdf_bytes = f.read()

    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = PdfWriter()

    try:
        all_pages = []

        # Collect and add selected pages
        for group in selected_groups:
            pages = parse_page_group(group)
            all_pages.extend(pages)
            for page_num in pages:
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])

        # Save processed PDF
        pdf_io = io.BytesIO()
        pdf_writer.write(pdf_io)

        unique_filename = f"processed_{file_id}_{user_id}_{uuid.uuid4().hex}.pdf"
        pdf_content = ContentFile(pdf_io.getvalue(), name=f"processed_img_pdf/{unique_filename}")

        processed_pdf = ProcessedPDF.objects.create(
            user=user,
            uploaded_file=uploaded_file,
            file_path=pdf_content,
        )

        # Send to webhook
        webhook_url = "https://backend-webhooks.azurewebsites.net/api/gmail_backend_webhook2"
        with processed_pdf.file_path.open("rb") as f:
            files = {"file": f}
            headers = {"sender_name": sender_email}
            response = requests.post(webhook_url, headers=headers, files=files)

        if response.status_code == 200:
            # Mark pages as split only if webhook succeeded
            ProcessedImage.objects.filter(
                uploaded_file=uploaded_file, page_num__in=all_pages
            ).update(is_split=True)
        else:
            print(f"[Webhook error] Status: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"[PDF processing failed] file_id={file_id}, error={str(e)}")
        # Do not mark pages as processed if failed


# --------------------------
# Async view for page processing
# --------------------------
@login_required
@csrf_exempt
def process_pages(request, file_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    selected_groups = request.POST.getlist("selected_groups")
    sender_email = request.user.email

    if not selected_groups:
        return JsonResponse({"error": "Missing required data."}, status=400)

    # Launch background thread
    thread = threading.Thread(
        target=process_pdf_task,
        args=(request.user.id, file_id, selected_groups, sender_email),
    )
    thread.start()

    # Immediate response
    return JsonResponse(
        {"message": "PDF processing started in background.", "continue_selection": True}
    )


# --------------------------
# View for listing processed/unprocessed docs
# --------------------------
@login_required
def processed_doc(request):
    user = request.user
    unprocessed_files = UploadedFile.objects.filter(user=user, is_archieved=False).exclude(
        id__in=ProcessedImage.objects.values_list("uploaded_file_id", flat=True)
    ).order_by("-uploaded_at")

    grouped_processed_files = ProcessedPDF.objects.filter(user=user).order_by("-processed_at")

    return render(
        request,
        "processed_document.html",
        {"unprocessed_files": unprocessed_files, "grouped_processed_files": grouped_processed_files},
    )


# --------------------------
# Delete processed PDF
# --------------------------
@login_required
def delete_document(request, file_id):
    if request.method == "POST":
        processed_file = ProcessedPDF.objects.filter(id=file_id).first()
        if processed_file:
            if processed_file.file_path:
                file_name = processed_file.file_path.name
                processed_file.file_path.delete(save=False)
                print(f"🗑️ Deleted processed PDF from Azure: {file_name}")
            processed_file.delete()
            messages.success(request, "Document deleted successfully.")
        else:
            messages.error(request, "Document not found.")
    return redirect("processed_doc")


# --------------------------
# Upload PDFs
# --------------------------
@csrf_exempt
def upload_pdfs(request):
    if request.method == "POST":
        sender_email = request.POST.get("sender_email_address")
        files = request.FILES.getlist("files")

        if not sender_email or not files:
            return JsonResponse({"error": "Email and files are required."}, status=400)

        try:
            user = User.objects.get(email=sender_email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Email not associated with any user."}, status=400)

        for file in files:
            UploadedFile.objects.create(file=file, user=user)

        return JsonResponse(
            {"message": "Files uploaded successfully.", "uploaded_files": [{"file_name": file.name} for file in files]},
            status=201,
        )

    return JsonResponse({"error": "Invalid request method."}, status=405)
