from django.db import models
from users.models import CustomUser

# --- Model Baru: Kategori ---
# Kita buat model terpisah agar kategori bisa dikelola di admin
class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, help_text="Versi URL-friendly dari nama, contoh: web-development")

    class Meta:
        verbose_name_plural = "Kategori" # Nama yang lebih baik di admin

    def __str__(self):
        return self.nama

# --- Model Baru: Tag ---
# Kita buat model terpisah agar tags bisa dikelola dan digunakan ulang
class Tag(models.Model):
    nama = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nama

# --- Tabel Produk (Diperbarui) ---
class Produk(models.Model):
    id_pemilik = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='produk_dimiliki')
    title = models.CharField(max_length=255)
    description = models.TextField()
    demo_link = models.URLField(max_length=255, blank=True, null=True)
    poster_image = models.ImageField(upload_to='', blank=True, null=True) 
    
    # --- TAMBAHAN 1: Relasi ke Kategori ---
    # ManyToManyField karena satu produk bisa punya >1 kategori (opsional)
    # Jika hanya 1 kategori per produk, gunakan ForeignKey
    kategori = models.ManyToManyField(Kategori, blank=True, related_name='produk')
    
    # --- TAMBAHAN 2: Relasi ke Tags ---
    tags = models.ManyToManyField(Tag, blank=True, related_name='produk')

    curation_status = models.CharField(max_length=50, default='pending')
    final_decision = models.CharField(max_length=50, blank=True, null=True)
    
    # --- TAMBAHAN 3: Field Publikasi ---
    dipublikasikan = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# --- Tabel Kurasi (Tidak ada perubahan) ---
class Kurasi(models.Model):
    id_produk = models.OneToOneField(Produk, on_delete=models.CASCADE, related_name='kurasi')
    id_kurator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='kurasi_ditugaskan')
    tanggal_penugasan = models.DateTimeField(null=True, blank=True)
    tanggal_selesai = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Belum Dinilai')
    nilai_akhir = models.FloatField(null=True, blank=True)
    catatan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Kurasi untuk: {self.id_produk.title}"

# --- Tabel Aspek_Penilaian (Tidak ada perubahan) ---
class AspekPenilaian(models.Model):
    id_kurasi = models.ForeignKey(Kurasi, on_delete=models.CASCADE, related_name='aspek_penilaian')
    aspek = models.CharField(max_length=100)
    skor = models.IntegerField()

    def __str__(self):
        return f"{self.aspek} - {self.skor}"

# --- Tabel Request_Source_Code (Tidak ada perubahan) ---
class RequestSourceCode(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id_produk = models.ForeignKey(Produk, on_delete=models.CASCADE, related_name='request_source_code')
    id_pemohon = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='request_diajukan')
    id_peninjau = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='request_ditinjau')
    tanggal_request = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Request untuk {self.id_produk.title} oleh {self.id_pemohon.username}"