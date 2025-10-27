# repository/admin.py

from django.contrib import admin
# --- TAMBAHKAN Kategori dan Tag di sini ---
from .models import Produk, Kurasi, AspekPenilaian, RequestSourceCode, Kategori, Tag 

# Daftarkan semua model Anda di sini agar muncul di admin

admin.site.register(Produk)
admin.site.register(Kurasi)
admin.site.register(AspekPenilaian)
admin.site.register(RequestSourceCode)

# --- TAMBAHKAN 2 BARIS INI ---
admin.site.register(Kategori)
admin.site.register(Tag)