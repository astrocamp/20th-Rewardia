from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-rjptsy-s2@ssc(j4jj0=8+tykyt^^r&dfxx^z#%%1t_psw++=!"

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Cloud Vision API Key
GOOGLE_CLOUD_VISION_API_KEY = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")

# 信用卡號碼加密金鑰
FERNET_KEY = os.getenv("FERNET_KEY")

# BIN API Key (用於信用卡銀行辨識)
BIN_API_KEY = os.getenv("BIN_API_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true")

ALLOWED_HOSTS = [
    "rewardia.net",
    "www.rewardia.net",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://rewardia.net",
    "https://www.rewardia.net",
    "http://rewardia.net",
    "http://www.rewardia.net",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# 安全設定：在開發環境中關閉，生產環境中啟用
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# 反向代理設定
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True


LOGIN_URL = "/sessions/login"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # OAuth 必要
    "storages",  # AWS S3 支援
    # ------------------------------
    "django_celery_results",
    "django_celery_beat",
    # ------------------------------
    "debug_toolbar",
    # ------------------------------
    "apps.pages",
    "apps.users",
    "apps.cards",
    "apps.rewards",
    "apps.sessions",
    "apps.admins",
    "apps.chatbot",  # Gemini AI robot
    "apps.ext_api",  # chrome extension api
    # ------------------------------
    "apps.nlp_validation",
    "apps.card_crawler",
    # ------------------------------
    # OAuth 相關套件
    "allauth",  # OAuth 核心套件
    "allauth.account",  # OAuth 必要：Email 管理和帳號功能
    "allauth.socialaccount",  # OAuth 必要：社交帳號登入核心
    "allauth.socialaccount.providers.google",  # OAuth 必要：Google OAuth 提供者
    # ------------------------------
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # OAuth 必要：處理 allauth 的帳號相關請求
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "Rewardia.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.pages.context_processors.version",
            ],
        },
    },
]

WSGI_APPLICATION = "Rewardia.wsgi.application"

# OAuth 必要：認證後端設定
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Django 預設認證（用戶名/密碼）
    "allauth.account.auth_backends.AuthenticationBackend",  # OAuth 必要：allauth 社交登入認證
]


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "service": "rewardia_service",
            "passfile": ".pg_db_pass",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-hant"

TIME_ZONE = "Asia/Taipei"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "assets/"

STATICFILES_DIRS = [
    BASE_DIR / "public",
]

# Static files will be collected here for production
STATIC_ROOT = BASE_DIR / "build"


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]


MESSAGE_TAGS = {
    messages.DEBUG: "tw-toast tw-info",
    messages.INFO: "tw-toast tw-info",
    messages.SUCCESS: "tw-toast tw-success",
    messages.WARNING: "tw-toast tw-warn",
    messages.ERROR: "tw-toast tw-error",
}

# ================================
# OAuth 設定區塊
# ================================

# OAuth 必要：站點 ID 設定
SITE_ID = 1  # 對應 Django Admin 中的 Sites 設定

# OAuth 必要：登入/登出重導向 URL
LOGIN_REDIRECT_URL = "/users/member/"  # OAuth 登入成功後重導向到會員專區
LOGOUT_REDIRECT_URL = "/"  # 登出後重導向到首頁

# OAuth 設定：帳號行為配置
ACCOUNT_UNIQUE_EMAIL = True  # 強制 Email 唯一性

# OAuth 設定：社交帳號行為配置
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"  # 不需要額外 Email 驗證（Google 已驗證）
SOCIALACCOUNT_AUTO_SIGNUP = True  # 自動註冊新用戶（無需手動註冊流程）
SOCIALACCOUNT_STORE_TOKENS = False  # 不儲存 OAuth tokens（節省資料庫空間）
SOCIALACCOUNT_LOGIN_ON_GET = True  # 允許 GET 請求直接觸發 OAuth 登入（簡化流程）

# OAuth 核心：Google OAuth 提供者設定
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),  # 從 .env 讀取 Google Client ID
            "secret": os.getenv(
                "GOOGLE_CLIENT_SECRET"
            ),  # 從 .env 讀取 Google Client Secret
            "key": "",  # Google OAuth 2.0 不需要 key
        },
        "SCOPE": [
            "profile",  # 取得用戶基本資料（姓名、頭像）
            "email",  # 取得用戶 Email 地址
        ],
        "AUTH_PARAMS": {
            "access_type": "online",  # 線上存取模式（不需要 refresh token）
        },
        "OAUTH_PKCE_ENABLED": True,  # 啟用 PKCE 安全機制（防止授權碼攔截）
    }
}

# -----------Celery------------

CELERY_BROKER_URL = "redis://rewardia-redis:6379/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Taipei"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# 給插件使用的
CORS_ALLOWED_ORIGINS = [
    "chrome-extension://odiagekokpobofjdlbmfobkbohcljnoe",
    "https://rewardia.net",
    "https://www.rewardia.net",
]


CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    # 設定回傳資料一頁有多少筆
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}


# -----------AWS相關------------
# Media files (User uploaded files)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 檔案上傳設定
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# AWS S3 設定
USE_S3 = os.getenv("USE_S3", "False").lower() == "true"

if USE_S3:
    # AWS 設定
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "ap-southeast-2")
    AWS_S3_CUSTOM_DOMAIN = (
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    )

    # S3 設定 - 移除 ACL 設定
    AWS_DEFAULT_ACL = None  # 不使用 ACL
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_VERIFY = True

    # 媒體檔案設定（只有圖片上傳到 S3）
    DEFAULT_FILE_STORAGE = "apps.cards.storage.MediaStorage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
