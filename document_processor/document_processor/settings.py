from pathlib import Path
import os

# -----------------------------
# Django Base Settings
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-61_9kog@l7f^1t)26j-vg&pa#7wgj69a_4c--6*^)fywzw5&22"
DEBUG = True
ALLOWED_HOSTS = ["*"]

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
    "storages",
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
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-info",
    "accent": "accent-info",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": False,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": False,
    "theme": "spacelab",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
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
TIME_ZONE = 'Etc/GMT-3'
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "user.auth_backend.EmailOrUsernameBackend",
]

CSRF_TRUSTED_ORIGINS = ["https://splitter.kabuta.biz"]

# -----------------------------
# Azure Blob Storage Settings
# -----------------------------
AZURE_STORAGE_ACCOUNT_NAME = "splitterstorage"
AZURE_STORAGE_ACCOUNT_KEY = "UiI3HzkXvAud0u/JzCn+CsLa24zNfcyM9xlqAvt7X2bhM1aa6OpVBXxgtc4qgRvbznnlBloLpM+J+ASt3LxSOA=="
AZURE_BLOB_CONTAINER_NAME = "comax-images-db"

DEFAULT_FILE_STORAGE = "document_processor.storage_backend.AzureMediaStorage"
