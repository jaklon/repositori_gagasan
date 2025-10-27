# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
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

    # Menambahkan field baru sesuai ERD
    peran = models.CharField(max_length=20, choices=PERAN_CHOICES, default='mahasiswa')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    def __str__(self):
        return self.username