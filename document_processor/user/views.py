from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

from .models import UploadedFile
from .forms import SignUpForm
from user.auth_backend import EmailOrUsernameBackend
from django.core.exceptions import ValidationError

import jwt
import datetime


def home(request):
    """Main dashboard view — handles JWT login, manual login, upload, delete."""
    # ✅ Handle JWT Token from URL
    if "token" in request.GET:
        token = request.GET["token"]
        print("JWT Token received:", token)

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            print("Decoded payload:", payload)

            # Expiration validation
            exp = datetime.datetime.utcfromtimestamp(payload["exp"])
            if exp < datetime.datetime.utcnow():
                messages.error(request, "Token has expired. Please log in again.")
                return redirect("home")

            # Try to authenticate user by email
            user_email = payload.get("sub")
            user = EmailOrUsernameBackend.authenticate(None, request=None, username=user_email)

            if user:
                user.backend = "user.auth_backend.EmailOrUsernameBackend"
                login(request, user)
                messages.success(request, "Logged in with JWT token successfully!")

                # Store token/session data
                request.session["jwt_token"] = token
                request.session["jwt_payload"] = payload
                request.session["jwt_expiration"] = exp.strftime("%Y-%m-%d %H:%M:%S")

                return redirect("home")
            else:
                messages.error(request, "User not found.")
                return redirect("home")

        except jwt.ExpiredSignatureError:
            messages.error(request, "Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token. Please try again.")
        except Exception as e:
            messages.error(request, f"Error processing token: {str(e)}")

        return redirect("home")

    # ✅ Handle POST actions
    if request.method == "POST":
        # Handle manual login
        if "username" in request.POST and "password" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "You have been logged in.")

                # Create short-lived JWT
                payload = {
                    "sub": user.email,
                    "user_id": user.id,
                    "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp(),
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

                # Save session info
                request.session["jwt_token"] = token
                request.session["jwt_payload"] = payload
                request.session["jwt_expiration"] = datetime.datetime.utcfromtimestamp(
                    payload["exp"]
                ).strftime("%Y-%m-%d %H:%M:%S")

                return redirect("home")
            else:
                messages.error(request, "Invalid credentials.")
                return redirect("home")

        # ✅ File upload (authenticated users only)
        if request.user.is_authenticated and "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]

            if uploaded_file.content_type != "application/pdf":
                messages.error(request, "Only PDF files are allowed.")
                return redirect("home")

            MAX_SIZE = 200 * 1024 * 1024  # 200 MB
            if uploaded_file.size > MAX_SIZE:
                messages.error(request, "File too large (max 200 MB).")
                return redirect("home")

            # Create entry in DB (file will be stored in Azure Blob)
            UploadedFile.objects.create(file=uploaded_file, user=request.user)
            messages.success(request, f"File '{uploaded_file.name}' uploaded successfully!")
            return redirect("home")

        # ✅ File delete (soft delete)
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

    # ✅ Fetch uploaded files for the current user
    context = {}
    if request.user.is_authenticated:
        uploaded_files = (
            UploadedFile.objects.filter(user=request.user, is_archieved=False)
            .annotate(
                total_pages=Count("processed_images"),
                unsplit_pages=Count(
                    "processed_images", filter=Q(processed_images__is_split=False)
                ),
            )
            .filter(Q(total_pages=0) | Q(unsplit_pages__gt=0))
        )
        context["uploaded_files"] = uploaded_files

    return render(request, "home.html", context)


def logout_user(request):
    """Logout the current user."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


def register_user(request):
    """Disabled manual registration (optional)."""
    return redirect("home")
