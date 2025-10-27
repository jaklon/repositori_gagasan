# gagasan_backend/urls.py

from django.contrib import admin
from django.urls import path, include

# --- TAMBAHKAN 2 BARIS IMPORT INI ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')), 
    path('', include('repository.urls')), 
]

# --- TAMBAHKAN BLOK 'if' INI DI BAGIAN PALING BAWAH FILE ---
# Ini adalah kode yang memberitahu Django cara menyajikan file media
if settings.DEBUG:
    # Sajikan file dari /poster_images/
    urlpatterns += static('/poster_images/', document_root=settings.MEDIA_ROOT)