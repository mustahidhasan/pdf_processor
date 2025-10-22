# user/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.conf import settings
import jwt
import datetime

from .models import UploadedFile
from user.auth_backend import EmailOrUsernameBackend
from document_processor.storages_backends import AzureMediaStorage


def home(request):
    # -----------------------------
    # JWT login handling
    # -----------------------------
    if "token" in request.GET:
        token = request.GET["token"]
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            exp = datetime.datetime.utcfromtimestamp(payload["exp"])
            if exp < datetime.datetime.utcnow():
                messages.error(request, "Token has expired. Please log in again.")
                return redirect("home")

            user_email = payload["sub"]
            user = EmailOrUsernameBackend.authenticate(self=None, request=None, username=user_email)
            if user:
                user.backend = "user.auth_backend.EmailOrUsernameBackend"
                login(request, user)
                request.session["jwt_token"] = token
                request.session["jwt_expiration"] = exp.strftime("%Y-%m-%d %H:%M:%S")
                request.session["jwt_payload"] = payload
                return redirect("home")
            else:
                messages.error(request, "User not found!")
        except Exception as e:
            messages.error(request, f"Error processing token: {str(e)}")
        return redirect("home")

    # -----------------------------
    # Handle POST requests
    # -----------------------------
    if request.method == "POST":
        # Traditional login
        if "username" in request.POST and "password" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                payload = {
                    "sub": user.email,
                    "user_id": user.id,
                    "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp(),
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                request.session["jwt_token"] = token
                request.session["jwt_expiration"] = datetime.datetime.utcfromtimestamp(payload["exp"]).strftime("%Y-%m-%d %H:%M:%S")
                request.session["jwt_payload"] = payload
                return redirect("home")
            else:
                messages.error(request, "Invalid login credentials. Please try again.")
                return redirect("home")

        # File upload directly to Azure
        if "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]

            # Validate file type
            if uploaded_file.content_type != "application/pdf":
                messages.error(request, "Only PDF files are allowed!")
                return redirect("home")

            # Validate file size (200 MB max)
            MAX_SIZE = 200 * 1024 * 1024
            if uploaded_file.size > MAX_SIZE:
                messages.error(request, "The file is too large. Maximum size allowed is 200 MB.")
                return redirect("home")

            # Save file using Azure storage backend
            new_file = UploadedFile(file=uploaded_file, user=request.user)
            new_file.save()  # This triggers AzureMediaStorage._save
            print(f"✅ File saved to Azure Blob Storage: {new_file.file.name}")
            messages.success(request, f"File '{uploaded_file.name}' uploaded successfully to Azure!")
            return redirect("home")

        # File deletion (actual removal from Azure)
        if "delete_file" in request.POST:
            file_id = request.POST.get("delete_file")
            try:
                file_to_delete = UploadedFile.objects.get(id=file_id, user=request.user)

                # Delete the file from Azure Blob Storage
                if file_to_delete.file:
                    file_name = file_to_delete.file.name  # save name before deletion
                    file_to_delete.file.delete(save=False)  # deletes from Azure
                    print(f"🗑️ File deleted from Azure Blob Storage: {file_name}")

                # Remove DB record
                file_to_delete.delete()
                messages.success(request, "File deleted successfully from Azure!")
            except UploadedFile.DoesNotExist:
                messages.error(request, "The file does not exist or you do not have permission to delete it!")
            return redirect("home")

    # -----------------------------
    # Prepare uploaded files for display
    # -----------------------------
    if request.user.is_authenticated:
        uploaded_files = UploadedFile.objects.filter(user=request.user).annotate(
            total_pages=Count("processed_images"),
            unsplit_pages=Count("processed_images", filter=Q(processed_images__is_split=False))
        ).filter(
            Q(total_pages=0) | Q(unsplit_pages__gt=0)
        )

        # Azure URLs
        for f in uploaded_files:
            if f.file:
                f.url = f.file.url  # Will return Azure Blob URL

        context = {"uploaded_files": uploaded_files}
    else:
        context = {}

    return render(request, "home.html", context)


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request):
    return redirect("home")
