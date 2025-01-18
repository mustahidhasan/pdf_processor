from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.shortcuts import render, redirect
import os
from .forms import SignUpForm


UPLOAD_DIR = "uploaded_files/"  # Directory to save uploaded files


def home(request):
    if request.method == "POST":
        # Handle Login
        if "username" in request.POST and "password" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "You have been logged in")
                return redirect("home")
            else:
                messages.error(request, "Invalid login credentials. Please try again.")
                return redirect("home")

        # Handle File Upload
        if "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]
            if uploaded_file.content_type == "application/pdf":  # Allow PDFs only
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                fs = FileSystemStorage(location=UPLOAD_DIR)
                filename = fs.save(uploaded_file.name, uploaded_file)
                messages.success(request, f"File '{uploaded_file.name}' uploaded successfully!")
            else:
                messages.error(request, "Only PDF files are allowed!")
            return redirect("home")

        # Handle File Deletion
        if "delete_file" in request.POST:
            file_to_delete = request.POST["delete_file"]
            file_path = os.path.join(UPLOAD_DIR, file_to_delete)
            if os.path.exists(file_path):
                os.remove(file_path)
                messages.success(request, f"File '{file_to_delete}' deleted successfully!")
            else:
                messages.error(request, f"File '{file_to_delete}' does not exist!")
            return redirect("home")

    # Fetch the list of uploaded files for display
    uploaded_files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []

    context = {
        "uploaded_files": uploaded_files,
    }
    return render(request, "home.html", context)



def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # authenticate and login
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have successfully Registered")
            return redirect("home")
    else:
        form = SignUpForm()
        return render(request, "register.html", {"form": form})
    return render(request, "register.html", {"form": form})
