from django.test import TestCase
from django.db.utils import IntegrityError
from users.models import CustomUser

class UserModelTest(TestCase):

    def setUp(self):
        # Setup data dasar jika diperlukan
        pass

    # ==========================================
    # 1. TEST PEMBUATAN USER BERDASARKAN PERAN
    # ==========================================

    def test_tc_mod_01_create_mahasiswa(self):
        """[Happy Path] Membuat user Mahasiswa dengan field spesifik"""
        user = CustomUser.objects.create_user(
            username='mhs_test',
            password='password123',
            peran='mahasiswa',
            nim='12345678',
            program_studi='D4 TI'
        )
        self.assertEqual(user.peran, 'mahasiswa')
        self.assertEqual(user.nim, '12345678')
        self.assertEqual(user.program_studi, 'D4 TI')
        # Cek default values
        self.assertEqual(user.status, 'aktif')
        self.assertFalse(user.is_approved)

    def test_tc_mod_02_create_dosen(self):
        """[Happy Path] Membuat user Dosen dengan field spesifik"""
        user = CustomUser.objects.create_user(
            username='dosen_test',
            password='password123',
            peran='dosen',
            id_dosen='DSN001',
            jurusan='TIK',
            bidang_keahlian='AI'
        )
        self.assertEqual(user.peran, 'dosen')
        self.assertEqual(user.id_dosen, 'DSN001')
        self.assertEqual(user.jurusan, 'TIK')

    def test_tc_mod_03_create_mitra(self):
        """[Happy Path] Membuat user Mitra dengan field spesifik"""
        user = CustomUser.objects.create_user(
            username='mitra_test',
            password='password123',
            peran='mitra',
            id_mitra='MTR001',
            organisasi='PT Tech Indo',
            bidang_keahlian='Software House'
        )
        self.assertEqual(user.peran, 'mitra')
        self.assertEqual(user.id_mitra, 'MTR001')
        self.assertEqual(user.organisasi, 'PT Tech Indo')

    def test_tc_mod_04_create_unit_bisnis(self):
        """[Happy Path] Membuat user Unit Bisnis"""
        user = CustomUser.objects.create_user(
            username='ub_admin',
            password='password123',
            peran='unit_bisnis'
        )
        self.assertEqual(user.peran, 'unit_bisnis')

    # ==========================================
    # 2. TEST STRING REPRESENTATION
    # ==========================================

    def test_tc_mod_05_str_method(self):
        """[Method Coverage] Test method __str__"""
        user = CustomUser.objects.create_user(username='test_user_str', password='p')
        self.assertEqual(str(user), 'test_user_str')

    # ==========================================
    # 3. TEST INTEGRITY & CONSTRAINTS (Unique)
    # ==========================================

    def test_tc_mod_06_unique_nim(self):
        """[Constraint] NIM harus unik"""
        # User 1
        CustomUser.objects.create_user(username='u1', password='p', peran='mahasiswa', nim='NIM_UNIK')
        
        # User 2 dengan NIM sama -> Harus Error
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username='u2', password='p', peran='mahasiswa', nim='NIM_UNIK')

    def test_tc_mod_07_unique_id_dosen(self):
        """[Constraint] ID Dosen harus unik"""
        CustomUser.objects.create_user(username='u1', password='p', peran='dosen', id_dosen='DSN_UNIK')
        
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username='u2', password='p', peran='dosen', id_dosen='DSN_UNIK')

    def test_tc_mod_08_unique_id_mitra(self):
        """[Constraint] ID Mitra harus unik"""
        CustomUser.objects.create_user(username='u1', password='p', peran='mitra', id_mitra='MTR_UNIK')
        
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(username='u2', password='p', peran='mitra', id_mitra='MTR_UNIK')