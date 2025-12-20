from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from users.forms import UserRegistrationForm 

User = get_user_model()

class UserViewsWhiteBoxTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # 1. User Normal (Approved & Active)
        self.user_mahasiswa = User.objects.create_user(
            username='mhs_valid', email='mhs@test.com', password='password123',
            peran='mahasiswa', is_approved=True, status='aktif'
        )
        
        # 2. User Belum Approved
        self.user_pending = User.objects.create_user(
            username='mhs_pending', email='pending@test.com', password='password123',
            peran='mahasiswa', is_approved=False, status='nonaktif'
        )
        
        # 3. User Approved tapi Nonaktif (Banned)
        self.user_banned = User.objects.create_user(
            username='mhs_banned', email='banned@test.com', password='password123',
            peran='mahasiswa', is_approved=True, status='nonaktif'
        )

        # 4. User Unit Bisnis
        self.user_ub = User.objects.create_user(
            username='ub_admin', email='ub@test.com', password='password123',
            peran='unit_bisnis', is_approved=True, status='aktif'
        )

    def get_valid_choice(self, field_name):
        """Helper: Mengambil opsi valid pertama agar registrasi tidak gagal validasi"""
        form = UserRegistrationForm()
        choices = form.fields[field_name].choices
        for key, value in choices:
            if key: return key
        return None

    # ==========================================
    # 1. TEST LOGIN VIEW
    # ==========================================
    
    def test_tc_log_01_login_success_mahasiswa(self):
        """[Happy Path] Login berhasil redirect ke dashboard mahasiswa"""
        response = self.client.post(reverse('login'), {
            'username': 'mhs@test.com',
            'password': 'password123'
        }, follow=True)
        
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('dashboard_mahasiswa'))

    def test_tc_log_02_login_success_unit_bisnis(self):
        """[Happy Path] Login UB redirect ke dashboard UB"""
        response = self.client.post(reverse('login'), {
            'username': 'ub@test.com',
            'password': 'password123'
        }, follow=True) # Tambahkan follow=True agar aman
        self.assertRedirects(response, reverse('dashboard_unit_bisnis'))

    def test_tc_log_03_login_failed_wrong_password(self):
        """[Negative Path] Password salah"""
        # PERBAIKAN: Tambahkan follow=True
        response = self.client.post(reverse('login'), {
            'username': 'mhs@test.com',
            'password': 'WRONG_PASSWORD'
        }, follow=True)
        
        # Setelah follow, kita ada di halaman login lagi, user harusnya anonymous
        self.assertFalse(response.context['user'].is_authenticated)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Email atau Password salah" in str(m) for m in messages))

    def test_tc_log_04_login_failed_not_approved(self):
        """[Negative Path] Akun belum disetujui (is_approved=False)"""
        # PERBAIKAN: Tambahkan follow=True
        response = self.client.post(reverse('login'), {
            'username': 'pending@test.com',
            'password': 'password123'
        }, follow=True)
        
        self.assertFalse(response.context['user'].is_authenticated)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("belum disetujui" in str(m) for m in messages))

    def test_tc_log_05_login_failed_nonaktif(self):
        """[Negative Path] Akun dinonaktifkan (status='nonaktif')"""
        # PERBAIKAN: Tambahkan follow=True
        response = self.client.post(reverse('login'), {
            'username': 'banned@test.com',
            'password': 'password123'
        }, follow=True)
        
        self.assertFalse(response.context['user'].is_authenticated)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("tidak aktif" in str(m) for m in messages))
        
    def test_tc_log_06_login_empty_input(self):
        """[Negative Path] Input kosong"""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': ''
        }, follow=True) # Follow agar bisa cek pesan error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("harus diisi" in str(m) for m in messages))

    # ==========================================
    # 2. TEST REGISTER VIEW
    # ==========================================
    
    def test_tc_reg_01_register_success(self):
        """[Happy Path] Registrasi user baru"""
        # PERBAIKAN: Ambil prodi valid secara dinamis
        valid_prodi = self.get_valid_choice('program_studi')
        if not valid_prodi:
            self.skipTest("Tidak ada pilihan Program Studi valid di Model.")

        data = {
            'username': 'new_user',
            'email': 'new@test.com',
            'password': 'password123',
            'password2': 'password123',
            'peran': 'mahasiswa',
            'nim': '12345678',
            'program_studi': valid_prodi # Gunakan variabel dinamis
        }
        
        response = self.client.post(reverse('register'), data, follow=True)
        
        # Harapannya redirect ke login
        self.assertRedirects(response, reverse('login'))
        
        # Cek user terbentuk di database
        new_user = User.objects.get(email='new@test.com')
        self.assertFalse(new_user.is_approved)

    def test_tc_reg_02_register_fail_invalid_data(self):
        """[Negative Path] Registrasi gagal (password mismatch)"""
        data = {
            'username': 'fail_user',
            'password': 'passA',
            'password2': 'passB',
            'peran': 'mahasiswa'
        }
        response = self.client.post(reverse('register'), data, follow=True)
        
        # Harapannya redirect kembali ke register (tetap di halaman register)
        # Note: Biasanya view me-render ulang template register, bukan redirect 302 ke register.
        # Tapi berdasarkan kode view Anda: `return redirect('register')` -> 302
        self.assertRedirects(response, reverse('register'))
        
        # Pastikan user TIDAK terbentuk
        self.assertFalse(User.objects.filter(username='fail_user').exists())

    # ==========================================
    # 3. TEST PROFILE VIEW
    # ==========================================
    
    def test_tc_prof_01_access_profile(self):
        """[Happy Path] Akses halaman profil"""
        self.client.login(username='mhs_valid', password='password123')
        response = self.client.get(reverse('profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertEqual(response.context['user'], self.user_mahasiswa)

    def test_tc_prof_02_update_profile(self):
        """[Happy Path] Update profil (Nama Depan)"""
        self.client.login(username='mhs_valid', password='password123')
        
        response = self.client.post(reverse('profile'), {
            'first_name': 'Update',
            'last_name': 'Name'
        }, follow=True)
        
        self.user_mahasiswa.refresh_from_db()
        self.assertEqual(self.user_mahasiswa.first_name, 'Update')
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil diperbarui" in str(m) for m in messages))

    # ==========================================
    # 4. TEST LOGOUT VIEW
    # ==========================================
    
    def test_tc_logout(self):
        self.client.login(username='mhs_valid', password='password123')
        # PERBAIKAN: Tambahkan follow=True
        response = self.client.get(reverse('logout'), follow=True)
        
        # Cek session sudah hilang
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('login'))