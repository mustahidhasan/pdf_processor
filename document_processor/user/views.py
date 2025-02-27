UPLOAD_DIR = "uploaded_files/"  # Directory to save uploaded files


import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from .models import UploadedFile
from .forms import SignUpForm
from django.core.exceptions import ValidationError
import jwt
import datetime
from document_processor.settings import SECRET_KEY


def home(request):
    # Handle Login with JWT Token
    if "token" in request.GET:
        token = request.GET["token"]
        print("JWT Token received:", token)

        try:
            # Decode JWT token using SECRET_KEY from settings.py
            payload = jwt.decode(
                token, SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False}
            )
            print("Decoded payload:", payload)

            # Check if token has expired
            exp = datetime.datetime.utcfromtimestamp(payload["exp"])
            current_time = datetime.datetime.utcnow()
            print(f"Token expiration time: {exp}")
            print(f"Current time: {current_time}")

            if exp < current_time:
                messages.error(request, "Token has expired. Please log in again.")
                return redirect("home")

            user_email = payload["sub"]
            user_id = payload["user_id"]

            # Authenticate user using either email or username
            user = authenticate(request, username=user_email, password=user_id)

            if user:
                login(request, user)
                messages.success(request, "You have been logged in")

                # **Store token and expiration time in session**
                request.session["jwt_token"] = token
                request.session["jwt_expiration"] = exp.strftime("%Y-%m-%d %H:%M:%S")
                request.session["jwt_payload"] = (
                    payload  # Store entire payload if needed
                )

                return redirect("home")
            else:
                messages.error(request, "User not found!")

        except jwt.ExpiredSignatureError:
            messages.error(request, "Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token. Please try again.")
        except jwt.InvalidAudienceError:
            messages.error(request, "Invalid audience in token.")

        return redirect("home")

    if request.method == "POST":

        # Handle traditional username and password login (if no JWT token is provided)
        if "username" in request.POST and "password" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "You have been logged in")

                # **Generate JWT token and store email in payload**
                payload = {
                    "sub": user.email,  # Store email as the subject
                    "user_id": user.id,
                    "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp(),
                }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

                # Store token and payload in session
                request.session["jwt_token"] = token
                request.session["jwt_expiration"] = datetime.datetime.utcfromtimestamp(payload["exp"]).strftime("%Y-%m-%d %H:%M:%S")
                request.session["jwt_payload"] = payload

                return redirect("home")
            else:
                messages.error(request, "Invalid login credentials. Please try again.")
                return redirect("home")

        # Handle File Upload
        if "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]

            # Check if the file is a PDF
            if uploaded_file.content_type == "application/pdf":

                # Check if the file size is less than or equal to 200 MB
                MAX_SIZE = 200 * 1024 * 1024  # 200 MB in bytes
                if uploaded_file.size > MAX_SIZE:
                    messages.error(
                        request,
                        "The file is too large. Maximum size allowed is 200 MB.",
                    )
                else:
                    new_file = UploadedFile(
                        file=uploaded_file, user=request.user
                    )  # Link file with logged-in user
                    new_file.save()
                    messages.success(
                        request, f"File '{uploaded_file.name}' uploaded successfully!"
                    )
            else:
                messages.error(request, "Only PDF files are allowed!")

            return redirect("home")

        # Handle File Deletion
        if "delete_file" in request.POST:
            file_id = request.POST.get("delete_file")
            try:
                file_to_delete = UploadedFile.objects.get(
                    id=file_id, user=request.user
                )  # Ensure the file belongs to the logged-in user
                file_to_delete.is_archieved = True
                file_to_delete.save()
                messages.success(
                    request, f"File '{file_to_delete.file.name}' deleted successfully!"
                )
            except UploadedFile.DoesNotExist:
                messages.error(
                    request,
                    "The file does not exist or you do not have permission to delete it!",
                )
            return redirect("home")

    # Conditionally add uploaded files to context if user is logged in
    if request.user.is_authenticated:
        uploaded_files = UploadedFile.objects.filter(
            user=request.user, is_archieved=False
        )  # Fetch files only if user is logged in
        context = {"uploaded_files": uploaded_files}
    else:
        context = {}  # No context for anonymous users

    return render(request, "home.html", context)


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request):
    return redirect("home")
    # if request.method == "POST":
    #     form = SignUpForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         # authenticate and login
    #         username = form.cleaned_data["username"]
    #         password = form.cleaned_data["password1"]
    #         # user = authenticate(username=username, password=password)
    #         # login(request, user)
    #         messages.success(request, "You have successfully Registered")
    #         return redirect("home")
    # else:
    #     # form = SignUpForm()
    #     # return render(request, "register.html", {"form": form})
    # return render(request, "register.html", {"form": form})
