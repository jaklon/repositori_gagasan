from django.db import models
from users.models import CustomUser
# --- Tambahkan Q untuk limit_choices ---
from django.db.models import Q

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
    poster_image = models.ImageField(upload_to='', blank=True, null=True)
    # TODO: Pertimbangkan menambahkan field source_code_link, program_studi di sini jika ingin disimpan permanen
    # source_code_link = models.URLField(max_length=255, blank=True, null=True)
    # program_studi = models.CharField(max_length=50, blank=True, null=True)

    # Relasi ManyToMany (jika satu produk bisa >1 kategori)
    kategori = models.ManyToManyField(Kategori, blank=True, related_name='produk')
    # Atau ForeignKey (jika satu produk hanya 1 kategori)
    # kategori_single = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True, related_name='produk')

    tags = models.ManyToManyField(Tag, blank=True, related_name='produk')

    # Status alur kurasi
    curation_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[ # Menambahkan choices agar lebih jelas
            ('pending', 'Pending (Menunggu Seleksi)'),
            ('selected', 'Selected (Terpilih untuk Kurasi)'),
            ('curators-assigned', 'Curators Assigned (Menunggu Penilaian)'),
            ('assessment-dosen-done', 'Assessment Dosen Done'),
            ('assessment-mitra-done', 'Assessment Mitra Done'),
            ('assessment-complete', 'Assessment Complete (Menunggu Review)'),
            ('ready-for-publication', 'Ready for Publication (Layak)'),
            ('revision-minor', 'Revision Minor (Revisi Minor)'),
            ('needs-coaching', 'Needs Coaching (Perlu Pembinaan)'),
            ('rejected', 'Rejected (Tidak Layak)'),
            ('published', 'Published (Dipublikasikan)'),
        ]
    )
    final_decision = models.CharField(max_length=50, blank=True, null=True) # Keputusan dari Unit Bisnis
    dipublikasikan = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Berguna untuk cek kapan status berubah

    def __str__(self):
        return self.title

# --- Tabel Kurasi (DIMODIFIKASI) ---
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
    ) # Field baru untuk Mitra
    tanggal_penugasan = models.DateTimeField(null=True, blank=True)
    # Pisahkan tanggal selesai
    tanggal_selesai_dosen = models.DateTimeField(null=True, blank=True) # Field baru
    tanggal_selesai_mitra = models.DateTimeField(null=True, blank=True) # Field baru

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
    nilai_akhir_dosen = models.FloatField(null=True, blank=True) # Field baru
    nilai_akhir_mitra = models.FloatField(null=True, blank=True) # Field baru
    nilai_akhir_final = models.FloatField(null=True, blank=True) # Field baru (Nilai gabungan)

    # Pisahkan catatan
    catatan_dosen = models.TextField(blank=True, null=True) # Field baru
    catatan_mitra = models.TextField(blank=True, null=True) # Field baru

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
    ) # Skor 1-4, bisa null awalnya
    # --- FIELD BARU ---
    # Tipe kurator yang memberi skor
    tipe_kurator = models.CharField(max_length=10, choices=[('dosen', 'Dosen'), ('mitra', 'Mitra')])

    class Meta:
        # Membuat kombinasi kurasi, aspek, dan tipe_kurator unik agar tidak duplikat
        unique_together = ('id_kurasi', 'aspek', 'tipe_kurator')

    def __str__(self):
        # Tampilkan 'Belum dinilai' jika skor masih null
        return f"{self.aspek} ({self.tipe_kurator}) - {self.get_skor_display() or 'Belum dinilai'}"

# --- Tabel Request_Source_Code (Tidak ada perubahan signifikan) ---
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
        # Contoh limit_choices jika hanya dosen/admin:
        # limit_choices_to=Q(peran='dosen') | Q(is_superuser=True)
    )
    alasan_request = models.TextField(blank=True, null=True)
    tanggal_request = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    alasan_request = models.TextField(blank=True, null=True, help_text="Alasan mengapa user meminta akses")

    def __str__(self):
        return f"Request untuk {self.id_produk.title} oleh {self.id_pemohon.username}"
