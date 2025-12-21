"""
Django settings for gagasan_backend project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Load environment variables dari file .env (untuk lokal)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================
# SECURITY & CONFIGURATION
# ==============================================

# Ambil SECRET_KEY dari .env, atau gunakan key dummy jika tidak ada (HANYA UNTUK DEV)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-change-me-in-production')

# Debug harus False di Production. Set 'True' hanya di .env lokal
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Izinkan host dari Vercel dan Localhost
ALLOWED_HOSTS = ['*'] # Bisa diperketat nanti menjadi ['.vercel.app', 'localhost', '127.0.0.1']

# Penting untuk Vercel agar form POST (Login/Upload) berfungsi
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://repositori-gagasan.vercel.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]


# ==============================================
# APPLICATION DEFINITION
# ==============================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'whitenoise.runserver_nostatic', # Opsional: untuk test static di local
    # Local apps
    'users',
    'repository',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Wajib untuk Vercel
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gagasan_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gagasan_backend.wsgi.application'


# ==============================================
# DATABASE CONFIGURATION (AUTO SWITCH)
# ==============================================

# Logic:
# 1. Cek apakah ada DATABASE_URL atau POSTGRES_URL (dari Neon/Vercel).
# 2. Jika ada, gunakan itu.
# 3. Jika tidak ada, gunakan SQLite lokal (lebih aman untuk default dev).

DATABASES = {}

# Cek URL database dari environment (Vercel biasanya pakai POSTGRES_URL atau DATABASE_URL)
database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if database_url:
    # Konfigurasi Production (Neon / Vercel Postgres)
    DATABASES['default'] = dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=True
    )
else:
    # Konfigurasi Lokal (SQLite atau Postgres Lokal)
    # Saya set ke SQLite agar Anda bisa run tanpa error koneksi saat awal.
    # Jika ingin pakai Postgres lokal, Anda harus set DATABASE_URL di file .env Anda.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'gagasan_db',
            'USER': 'postgres',
            'PASSWORD': '1613',  # Password lokal Anda
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }


# ==============================================
# PASSWORD VALIDATION
# ==============================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # Bisa di-comment jika ingin password sederhana saat development
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# ==============================================
# INTERNATIONALIZATION
# ==============================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC' # Bisa diganti 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True


# ==============================================
# STATIC & MEDIA FILES
# ==============================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Kompresi dan Caching Static Files untuk Production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files (Upload User)
# PENTING: Di Vercel (gratis), file media akan HILANG setelah beberapa saat.
# Untuk production serius, Anda perlu menggunakan AWS S3 atau Cloudinary.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'