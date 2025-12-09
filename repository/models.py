from django.db import models
from users.models import CustomUser
# --- Tambahkan Q untuk limit_choices ---
from django.db.models import Q
import os

# --- Model Baru: Kategori ---
class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, help_text="Versi URL-friendly dari nama, contoh: web-development")

    class Meta:
        verbose_name_plural = "Kategori" # Nama yang lebih baik di admin

    def __str__(self):
        return self.nama

# --- Model Baru: Tag ---
class Tag(models.Model):
    nama = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nama

# --- Tabel Produk (Diperbarui) ---
class Produk(models.Model):
    id_pemilik = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='produk_dimiliki')
    title = models.CharField(max_length=255)
    description = models.TextField()
    source_code_link = models.URLField(max_length=255, blank=True, null=True, help_text="Link ke source code (GitHub, Drive, dll.)")
    demo_link = models.URLField(max_length=255, blank=True, null=True)
    poster_image = models.ImageField(upload_to='poster_images/', blank=True, null=True) # Diberi path untuk upload media

    # Relasi ManyToMany (jika satu produk bisa >1 kategori)
    kategori = models.ManyToManyField(Kategori, blank=True, related_name='produk')
    tags = models.ManyToManyField(Tag, blank=True, related_name='produk')

    # Status alur kurasi
    curation_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[ # Menambahkan choices agar lebih jelas
            ('pending', 'Menunggu Seleksi'),
            ('selected', 'Terpilih untuk Kurasi'),
            ('curators-assigned', 'Menunggu Penilaian'),
            ('assessment-dosen-done', 'Penilaian Dosen Selesai'),
            ('assessment-mitra-done', 'Penilaian Mitra Selesai'),
            ('assessment-complete', 'Menunggu Review'),
            ('ready-for-publication', 'Layak'),
            ('revision-minor', 'Revisi Minor'),
            ('needs-coaching', 'Perlu Pembinaan'),
            ('rejected', 'Tidak Layak'),
            ('published', 'Dipublikasikan'),
        ]
    )
    final_decision = models.CharField(max_length=50, blank=True, null=True) # Keputusan dari Unit Bisnis
    dipublikasikan = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Berguna untuk cek kapan status berubah

    def __str__(self):
        return self.title

# --- Tabel Kurasi (DIMODIFIKASI & Duplikasi Dihilangkan) ---
class Kurasi(models.Model):
    id_produk = models.OneToOneField(Produk, on_delete=models.CASCADE, related_name='kurasi')
    # Pisahkan kurator dosen dan mitra
    id_kurator_dosen = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='kurasi_dosen', limit_choices_to={'peran': 'dosen'}
    )
    id_kurator_mitra = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='kurasi_mitra', limit_choices_to={'peran': 'mitra'}
    ) 
    tanggal_penugasan = models.DateTimeField(null=True, blank=True)
    # Pisahkan tanggal selesai
    tanggal_selesai_dosen = models.DateTimeField(null=True, blank=True) 
    tanggal_selesai_mitra = models.DateTimeField(null=True, blank=True) 

    # Status penilaian
    STATUS_PENILAIAN = [
        ('Menunggu Penugasan', 'Menunggu Penugasan'),
        ('Penilaian Berlangsung', 'Penilaian Berlangsung'),
        ('Penilaian Dosen Selesai', 'Penilaian Dosen Selesai'),
        ('Penilaian Mitra Selesai', 'Penilaian Mitra Selesai'),
        ('Penilaian Lengkap', 'Penilaian Lengkap'),
    ]
    status = models.CharField(max_length=50, default='Menunggu Penugasan', choices=STATUS_PENILAIAN)

    # Pisahkan nilai akhir
    nilai_akhir_dosen = models.FloatField(null=True, blank=True) 
    nilai_akhir_mitra = models.FloatField(null=True, blank=True) 
    nilai_akhir_final = models.FloatField(null=True, blank=True) 

    # Catatan (hanya satu instance dari masing-masing)
    catatan_dosen = models.TextField(blank=True, null=True) 
    catatan_mitra = models.TextField(blank=True, null=True) 
    catatan_unit_bisnis = models.TextField(blank=True, null=True, help_text="Catatan final dari Unit Bisnis saat review")

    def __str__(self):
        return f"Kurasi untuk: {self.id_produk.title}"

# --- Tabel Aspek_Penilaian (DIMODIFIKASI) ---
class AspekPenilaian(models.Model):
    id_kurasi = models.ForeignKey(Kurasi, on_delete=models.CASCADE, related_name='aspek_penilaian')
    aspek = models.CharField(max_length=100) # Nama aspek dari dokumen
    # Skor bisa null, dan punya choices
    skor = models.IntegerField(
        null=True, blank=True,
        choices=[(1, '1 - Kurang'), (2, '2 - Cukup'), (3, '3 - Baik'), (4, '4 - Sangat Baik')]
    ) 
    tipe_kurator = models.CharField(max_length=10, choices=[('dosen', 'Dosen'), ('mitra', 'Mitra')])

    class Meta:
        # Membuat kombinasi kurasi, aspek, dan tipe_kurator unik agar tidak duplikat
        unique_together = ('id_kurasi', 'aspek', 'tipe_kurator')

    def __str__(self):
        # Tampilkan 'Belum dinilai' jika skor masih null
        return f"{self.aspek} ({self.tipe_kurator}) - {self.get_skor_display() or 'Belum dinilai'}"

# --- Tabel Request_Source_Code ---
class RequestSourceCode(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id_produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='request_source_code')
    id_pemohon = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='request_diajukan')
    # Pastikan peninjau bisa dosen atau admin (sesuaikan limit_choices jika perlu)
    id_peninjau = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='request_ditinjau'
       
    )
    alasan_request = models.TextField(blank=True, null=True, help_text="Alasan mengapa user meminta akses")
    tanggal_request = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Request untuk {self.id_produk.title} oleh {self.id_pemohon.username}"
    

# ---------------------------------------------------------------------
# --- Model DokumenProyek (Sudah dikoreksi indentasi) ---
# ---------------------------------------------------------------------
class DokumenProyek(models.Model):
    """
    Model untuk menyimpan dokumen pendukung yang diunggah untuk sebuah proyek.
    """
    # Relasi ke model Produk
    produk = models.ForeignKey(
        Produk, 
        on_delete=models.CASCADE, 
        related_name='dokumen', 
        verbose_name='Proyek'
    )
    
    # Field untuk menyimpan file (blank=True agar bisa diisi link di keterangan)
    file_dokumen = models.FileField(
        upload_to='project_documents/', 
        verbose_name='File Dokumen',
        blank=True, 
        null=True
    )
    
    # Keterangan dokumen (bisa berupa link jika file_dokumen kosong)
    keterangan = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Keterangan File (Atau Link)'
    )
    
    # Pilihan Tipe Dokumen
    TIPE_CHOICES = [
        ('Laporan Akhir', 'Laporan Akhir'),
        ('Manual Book', 'Manual Book'),
        ('Diagram Desain', 'Diagram Desain'),
        ('Lainnya', 'Lainnya'),
    ]
    tipe_dokumen = models.CharField(
        max_length=50, 
        choices=TIPE_CHOICES,
        default='Lainnya', 
        verbose_name='Jenis Dokumen'
    )

    class Meta:
        verbose_name_plural = "Dokumen Proyek"

    def __str__(self):
        return f"{self.produk.title} - {self.tipe_dokumen}"

    def get_file_name(self):
        """Mendapatkan nama file tanpa path"""
        return os.path.basename(self.file_dokumen.name) if self.file_dokumen else 'Tidak Ada File'