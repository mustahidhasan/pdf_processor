import os
import requests
from django.shortcuts import render, get_object_or_404, redirect
from user.models import UploadedFile
from pdf2image import convert_from_path
from django.contrib import messages
from django.conf import settings
from .models import ProcessedImage, ProcessedPDF

from PyPDF2 import PdfWriter, PdfReader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from user.models import UploadedFile
from itertools import groupby
from operator import attrgetter
from django.contrib.auth.models import User
import time
import uuid


def process(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    file_path = uploaded_file.file.path
    image_dir = os.path.join(settings.MEDIA_ROOT, "processed_files", str(uploaded_file.id))
    os.makedirs(image_dir, exist_ok=True)

    processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)
    if not processed_pages.exists():
        try:
            images = convert_from_path(file_path, 300)
            for page_num, image in enumerate(images):
                image_filename = f"page_{page_num + 1}.png"
                image_path = os.path.join(image_dir, image_filename)
                image.save(image_path, "PNG")

                ProcessedImage.objects.create(
                    uploaded_file=uploaded_file,
                    page_num=page_num + 1,
                    image=f"processed_files/{uploaded_file.id}/{image_filename}",
                    is_split=False
                )
            processed_pages = ProcessedImage.objects.filter(uploaded_file=uploaded_file)
        except Exception as e:
            messages.error(request, f"Error processing PDF: {str(e)}")
            return redirect("home")

    extracted_pages = []
    for page in processed_pages:
        extracted_pages.append({
            "page_num": page.page_num,
            "image_url": os.path.join("media", page.image.name),
            "is_split": page.is_split,
        })

    return render(request, "process.html", {
        "uploaded_file": uploaded_file,
        "extracted_pages": extracted_pages,
    })


@csrf_exempt
def process_pages(request, file_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    # Retrieve JWT data from session
    token = request.session.get("jwt_token")
    payload = request.session.get("jwt_payload")
    expiration = request.session.get("jwt_expiration")

    if not token or not payload:
        messages.error(request, "No valid session found. Please log in again.")
        return redirect("login")

    user_email = payload.get("sub")  # Extract email from JWT payload
    if not user_email:
        return JsonResponse(
            {"error": "JWT payload missing 'sub' (user email)."}, status=400
        )

    print(f"Token: {token}")
    print(f"Payload: {payload}")
    print(f"Expiration: {expiration}")

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

    # Directory for processed PDFs
    processed_dir = os.path.join(settings.MEDIA_ROOT, "processed_img_pdf")
    os.makedirs(processed_dir, exist_ok=True)

    webhook_url = (
        "https://backend-webhooks.azurewebsites.net/api/gmail_backend_webhook2"
    )

    try:
        pdf_reader = PdfReader(original_pdf_path)
        pdf_writer = PdfWriter()

        for group in selected_groups:
            try:
                pages = parse_page_group(group)
                for page_num in pages:
                    pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            except ValueError:
                return JsonResponse(
                    {"error": f"Invalid page group: {group}"}, status=400
                )

        # Generate a unique filename
        unique_filename = (
            f"processed_{file_id}_{request.user.id}_{uuid.uuid4().hex}.pdf"
        )
        combined_pdf_path = os.path.join(processed_dir, unique_filename)

        with open(combined_pdf_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)

        # Save processed PDF to database
        processed_pdf = ProcessedPDF.objects.create(
            user=request.user,
            uploaded_file=uploaded_file,
            file_path=f"processed_img_pdf/{unique_filename}",
        )

        # Mark pages as split
        for group in selected_groups:
            pages = parse_page_group(group)
            ProcessedImage.objects.filter(uploaded_file=uploaded_file, page_num__in=pages).update(is_split=True)

        # Prepare the headers to include sender_name and user_email
        headers = {
            "sender_name": sender_email,
        }

        try:
            with open(combined_pdf_path, "rb") as new_pdf:
                files = {"file": new_pdf}
                
                print("line 161", headers)
                response = requests.post(webhook_url, headers=headers, files=files)

            if response.status_code != 200:
                return JsonResponse(
                    {
                        "error": f"Failed to send PDF: {response.status_code} {response.text}"
                    },
                    status=500,
                )

        except Exception as e:
            return JsonResponse({"error": f"Failed to send PDF: {e}"}, status=500)

        return JsonResponse(
            {
                "message": "PDF processed successfully.",
                "processed_pdf_url": f"/media/processed_img_pdf/{unique_filename}",
                "continue_selection": True,
            }
        )

    except Exception as e:
        return JsonResponse({"error": f"Failed to process PDF: {e}"}, status=500)

def parse_page_group(group):
    pages = []
    parts = group.split(",")
    for part in parts:
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages


# later will add
@login_required
def processed_doc(request):
    """View to handle both new and processed documents for the logged-in user."""
    user = request.user

    # Fetch unprocessed files (files not linked to ProcessedImage)
    unprocessed_files = (
        UploadedFile.objects.filter(user=user, is_archieved=False)
        .exclude(
            id__in=ProcessedImage.objects.values_list("uploaded_file_id", flat=True)
        )
        .order_by("-uploaded_at")
    )

    # Group processed files by uploaded_file and filter by user
    grouped_processed_files = ProcessedPDF.objects.filter(user=user).order_by(
        "-processed_at"
    )

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

    if request.method == "POST":
        print("line 192", file_id)
        get_processed_file = ProcessedPDF.objects.filter(id=file_id).first()
        if get_processed_file:
            get_processed_file.delete()
            messages.success(request, "Document deleted successfully.")
            return redirect("processed_doc")  # Redirects to the home page
        else:
            # Handle the case where the file doesn't exist (e.g., raise a 404 or log the error)
            print("Processed file not found.")
            messages.error(request, "Document deleted Error.")
            return redirect("processed_doc")  # Redirects to the home page

    return redirect("processed_doc")


@csrf_exempt
def upload_pdfs(request):
    if request.method == "POST":
        sender_email = request.POST.get("sender_email_address")
        files = request.FILES.getlist("files")

        if not sender_email or not files:
            return JsonResponse(
                {"error": "Email address and files are required."}, status=400
            )

        # Check if the sender_email exists in the User model
        try:
            user = User.objects.get(email=sender_email)
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "Email address not associated with any user."}, status=400
            )

        # Save each uploaded file associated with the user
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
