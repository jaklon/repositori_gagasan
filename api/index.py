import os
from django.core.wsgi import get_wsgi_application

# Arahkan ke settings project Anda
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gagasan_backend.settings')

# PENTING: Vercel mencari variabel bernama 'app', bukan 'application'
app = get_wsgi_application()