# repository/admin.py

from django.contrib import admin
# Pastikan DokumenProyek di-import di sini
from .models import Produk, Kurasi, AspekPenilaian, RequestSourceCode, Kategori, Tag, DokumenProyek 

# ==========================================================
# 1. DEFINISI INLINE UNTUK MODEL DOKUMENPROYEK (MODEL ANAK)
# ==========================================================
class DokumenProyekInline(admin.TabularInline):
    """
    Menampilkan Dokumen Proyek sebagai tabel di halaman edit Produk.
    """
    model = DokumenProyek 
    extra = 1  # Jumlah formulir kosong yang ditampilkan secara default

# ==========================================================
# 2. DEFINISI MODEL ADMIN UNTUK PRODUK (MODEL INDUK)
# ==========================================================

# Gunakan decorator @admin.register untuk mendaftarkan model Produk
@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    """
    ModelAdmin untuk Produk yang menyertakan Dokumen Proyek sebagai inline.
    """
    # ... Anda bisa menambahkan list_display, search_fields, dll. di sini jika perlu

    # Tambahkan inline yang telah dibuat
    inlines = [
        DokumenProyekInline,
    ]

# ==========================================================
# 3. PENDAFTARAN MODEL LAINNYA
# ==========================================================

# Model-model ini tidak memerlukan kustomisasi Inline, jadi daftarkan seperti biasa.
admin.site.register(Kurasi)
admin.site.register(AspekPenilaian)
admin.site.register(RequestSourceCode)
admin.site.register(Kategori)
admin.site.register(Tag)

# Hapus baris 'admin.site.register(Produk)' lama karena sudah digantikan oleh @admin.register(Produk)
# Hapus baris 'admin.site.register(Kategori)' dan 'admin.site.register(Tag)' jika Anda ingin menggunakan decorator
# tetapi dalam kasus ini, kita pertahankan admin.site.register untuk mereka.