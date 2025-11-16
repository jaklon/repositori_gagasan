# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # --- Pilihan untuk field ---
    PERAN_CHOICES = [
        ('mahasiswa', 'Mahasiswa'),
        ('dosen', 'Dosen'),
        ('mitra', 'Mitra'),
        ('unit_bisnis', 'Unit Bisnis'),
    ]

    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]
    
    PROGRAM_STUDI_CHOICES = [
        ('D4 TI', 'D4 Teknik Informatika'),
        ('D4 TMDJ', 'D4 Teknik Multimedia dan Jaringan'),
        ('D4 TMD', 'D4 Tenik Multimedia Digital'),
    ]
    
    # --- Field Utama ---
    peran = models.CharField(max_length=20, choices=PERAN_CHOICES, default='mahasiswa')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    is_approved = models.BooleanField(default=False, verbose_name='Disetujui')

    # --- Field Mahasiswa ---
    nim = models.CharField(max_length=20, blank=True, null=True, unique=True)
    program_studi = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        choices=PROGRAM_STUDI_CHOICES
    )
    
    # --- Field Dosen ---
    id_dosen = models.CharField(max_length=30, blank=True, null=True, unique=True)
    jurusan = models.CharField(max_length=100, blank=True, null=True)
    
    # --- Field Mitra ---
    id_mitra = models.CharField(max_length=30, blank=True, null=True, unique=True)
    organisasi = models.CharField(max_length=100, blank=True, null=True)
    
    # --- Field Dosen & Mitra ---
    bidang_keahlian = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username