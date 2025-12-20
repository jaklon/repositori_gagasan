"""
Django settings for gagasan_backend project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Saat deploy, sebaiknya set SECRET_KEY di Environment Variables Vercel.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-*meh%6-kk*t0a5*emop4zo+1$15-pp)!p3)!v_2mbf1yn+h5&p')

# SECURITY WARNING: don't run with debug turned on in production!
# Otomatis False jika di Production (Vercel), True jika di Lokal
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['.vercel.app', '.now.sh', '127.0.0.1', 'localhost']

# PENTING: Agar form Login/Register bisa jalan di Vercel (HTTPS)
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',       # App Users Anda
    'repository',  # App Repository Anda
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Wajib untuk CSS di Vercel
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


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Logika Database:
# 1. Cek apakah ada DATABASE_URL (Environment Variable dari Vercel/Neon)
# 2. Jika ADA -> Gunakan Neon Postgres.
# 3. Jika TIDAK ADA -> Gunakan Postgres Lokal (Laptop).

database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Konfigurasi Production (Neon)
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Konfigurasi Development (Lokal Laptop)
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


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # Kosongkan saat dev agar mudah buat password simple (misal: '123')
    # Uncomment baris di bawah ini saat production sebenarnya
    # { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    # { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    # { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    # { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'id-id' # Ubah ke Indonesia agar pesan error bahasa Indo (Opsional)

TIME_ZONE = 'Asia/Jakarta' # Ubah ke WIB

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Folder static buatan kita sendiri (selain bawaan Django Admin)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Folder tujuan saat collectstatic dijalankan (wajib untuk WhiteNoise)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Engine penyimpanan static file (menggunakan WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.CustomUser'

# Pengaturan untuk file yang di-upload (Media)
# Note: Di Vercel (Free Tier), file media yang diupload user akan HILANG setelah beberapa saat
# karena Vercel bersifat Ephemeral (Serverless).
# Untuk solusi permanen, biasanya menggunakan AWS S3 atau Cloudinary.
# Tapi untuk project kuliah/skripsi, setting ini cukup (file tersimpan sementara).
MEDIA_URL = '/poster_images/'
MEDIA_ROOT = BASE_DIR / 'poster_images'