from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from users.models import CustomUser
from repository.models import Produk, Kurasi, AspekPenilaian, Kategori

class UserModelTest(TestCase):
    def test_default_values(self):
        # White Box: Memeriksa baris 'default='mahasiswa''
        user = CustomUser.objects.create_user(username="mhs_baru", password="123")
        self.assertEqual(user.peran, 'mahasiswa')
        self.assertFalse(user.is_approved) # Default harus False

    def test_unique_nim(self):
        # White Box: Memeriksa baris 'unique=True' pada field nim
        CustomUser.objects.create_user(username="u1", nim="12345", password="123")
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username="u2", nim="12345", password="123")