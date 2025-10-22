from pathlib import Path
from storages.backends.azure_storage import AzureStorage

# -------------------- Basic Django Settings --------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-61_9kog@l7f^1t)26j-vg&pa#7wgj69a_4c--6*^)fywzw5&22"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'jazzmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "user",
    "document",
    "corsheaders",
    "storages",
]

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
        "DIRS": [BASE_DIR / "templates"],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Etc/GMT-3"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.auth_backend.EmailOrUsernameBackend",
]

CSRF_TRUSTED_ORIGINS = ["https://splitter.kabuta.biz"]

# -------------------- Azure Blob Storage --------------------
AZURE_ACCOUNT_NAME = "splitterstorage"
AZURE_ACCOUNT_KEY = "UiI3HzkXvAud0u/JzCn+CsLa24zNfcyM9xlqAvt7X2bhM1aa6OpVBXxgtc4qgRvbznnlBloLpM+J+ASt3LxSOA=="
AZURE_CONTAINER = "comax-images-db"
AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"

class AzureMediaStorage(AzureStorage):
    account_name = AZURE_ACCOUNT_NAME
    account_key = AZURE_ACCOUNT_KEY
    azure_container = AZURE_CONTAINER
    expiration_secs = None

DEFAULT_FILE_STORAGE = "document_processor.settings.AzureMediaStorage"

MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/"
