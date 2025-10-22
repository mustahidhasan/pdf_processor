from pathlib import Path
import os
from dotenv import load_dotenv

# -------------------- Load environment variables --------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, '.env')  # Adjust if your .env is elsewhere
load_dotenv(ENV_PATH)

# -------------------- Django basic settings --------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# -------------------- Installed apps --------------------
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "user",
    "document",
    "corsheaders",
    "storages",  # ✅ For Azure Blob Storage
]
JAZZMIN_SETTINGS = {
    "site_title": "Document Processor Admin",
    "site_header": "Document Processor",
    "site_brand": "Document Processor",
    "welcome_sign": "Welcome to Document Processor Admin",
    "topmenu_links": [
        {"name": "Home", "url": "/", "icon": "fa fa-home"},
        {"name": "Logout", "url": "/logout", "icon": "fa fa-sign-out-alt"},
    ],
    "show_ui_builder": False,  # Set to True to enable the UI builder
    "default_icon_parents": "fa fa-folder",
    "default_icon_children": "fa fa-file",
}
# -------------------- Middleware --------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "document_processor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "document_processor.wsgi.application"

# -------------------- Database --------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # Local dev
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------- Password validation --------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------- Internationalization --------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Etc/GMT-3"
USE_I18N = True
USE_TZ = True

# -------------------- Static files --------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------- Authentication --------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.auth_backend.EmailOrUsernameBackend",
]

CSRF_TRUSTED_ORIGINS = [
    "https://splitter.kabuta.biz",
]

# -------------------- Azure Blob Storage --------------------
AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER")
AZURE_CUSTOM_DOMAIN = os.getenv("AZURE_CUSTOM_DOMAIN", f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net")

# Custom Azure Storage backend
from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    account_name = AZURE_ACCOUNT_NAME
    account_key = AZURE_ACCOUNT_KEY
    azure_container = AZURE_CONTAINER
    expiration_secs = None

# Use Azure in production, fallback to local storage in DEBUG mode
if DEBUG:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
else:
    DEFAULT_FILE_STORAGE = "document_processor.settings.AzureMediaStorage"
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/"
