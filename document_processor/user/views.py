import os
import uuid
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

import jwt
import datetime

from user.models import UploadedFile
from user.auth_backend import EmailOrUsernameBackend
from .forms import SignUpForm


# ------------------- HOME / DASHBOARD -------------------

def home(request):
    """Dashboard: JWT login, manual login, upload, delete — Azure Blob storage."""

    # ----- JWT login via URL -----
    if "token" in request.GET:
        token = request.GET["token"]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False})
            exp = datetime.datetime.utcfromtimestamp(payload["exp"])
            if exp < datetime.datetime.utcnow():
                messages.error(request, "Token expired. Please log in again.")
                return redirect("home")

            user_email = payload.get("sub")
            user = EmailOrUsernameBackend.authenticate(None, request=None, username=user_email)
            if user:
                user.backend = "user.auth_backend.EmailOrUsernameBackend"
                login(request, user)
                messages.success(request, "Logged in via JWT successfully!")
                request.session["jwt_token"] = token
                request.session["jwt_payload"] = payload
                request.session["jwt_expiration"] = exp.strftime("%Y-%m-%d %H:%M:%S")
                return redirect("home")
            else:
                messages.error(request, "User not found.")
                return redirect("home")

        except Exception as e:
            messages.error(request, f"JWT processing error: {str(e)}")
            return redirect("home")

    # ----- POST actions -----
    if request.method == "POST":
        # ---------- Manual login ----------
        if "username" in request.POST and "password" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "You have been logged in.")

                payload = {
                    "sub": user.email,
                    "user_id": user.id,
                    "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp(),
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                request.session["jwt_token"] = token
                request.session["jwt_payload"] = payload
                request.session["jwt_expiration"] = datetime.datetime.utcfromtimestamp(payload["exp"]).strftime("%Y-%m-%d %H:%M:%S")
                return redirect("home")
            else:
                messages.error(request, "Invalid credentials.")
                return redirect("home")

        # ---------- File upload (Azure) ----------
        if request.user.is_authenticated and "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]

            if uploaded_file.content_type != "application/pdf":
                messages.error(request, "Only PDF files are allowed.")
                return redirect("home")

            MAX_SIZE = 200 * 1024 * 1024  # 200 MB
            if uploaded_file.size > MAX_SIZE:
                messages.error(request, "File too large (max 200 MB).")
                return redirect("home")

            # Save PDF to Azure
            file_name = f"uploaded_files/{request.user.id}/{uploaded_file.name}"
            default_storage.save(file_name, ContentFile(uploaded_file.read()))

            # Save DB record
            UploadedFile.objects.create(file=file_name, user=request.user)
            messages.success(request, f"File '{uploaded_file.name}' uploaded successfully!")
            return redirect("home")

        # ---------- File deletion (soft delete) ----------
        if request.user.is_authenticated and "delete_file" in request.POST:
            file_id = request.POST.get("delete_file")
            try:
                file_to_delete = UploadedFile.objects.get(id=file_id, user=request.user)
                file_to_delete.is_archieved = True
                file_to_delete.save()
                messages.success(request, f"File '{file_to_delete.file.name}' deleted successfully.")
            except UploadedFile.DoesNotExist:
                messages.error(request, "File not found or access denied.")
            return redirect("home")

    # ----- Display uploaded files -----
    context = {}
    if request.user.is_authenticated:
        uploaded_files = (
            UploadedFile.objects.filter(user=request.user, is_archieved=False)
            .annotate(
                total_pages=Count("processed_images"),
                unsplit_pages=Count("processed_images", filter=Q(processed_images__is_split=False)),
            )
            .filter(Q(total_pages=0) | Q(unsplit_pages__gt=0))
        )

        # Convert to Azure URLs
        for f in uploaded_files:
            f.file_url = default_storage.url(f.file.name if hasattr(f.file, "name") else f.file)
        context["uploaded_files"] = uploaded_files

    return render(request, "home.html", context)


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


def register_user(request):
    """Registration disabled."""
    return redirect("home")
