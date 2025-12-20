from django.test import TestCase
from users.forms import UserUpdateForm, UserRegistrationForm
from users.models import CustomUser

class UserUpdateFormTest(TestCase):
    """
    [WHITE BOX] Menguji UserUpdateForm
    Fokus: Validasi field dasar dan widget.
    """
    
    def test_tc_upd_01_valid_update(self):
        form_data = {
            'first_name': 'Budi',
            'last_name': 'Santoso',
        }
        form = UserUpdateForm(data=form_data)
        self.assertTrue(form.is_valid())


class UserRegistrationFormTest(TestCase):
    """
    [WHITE BOX] Menguji UserRegistrationForm
    Fokus: 
    1. Validasi Password Matching (clean_password2)
    2. Validasi Kondisional berdasarkan Peran (clean)
    """

    def get_base_data(self):
        """Helper untuk data dasar yang selalu dibutuhkan"""
        return {
            'username': 'testuser',
            'email': 'test@pnj.ac.id',
            'password': 'password123',
            'password2': 'password123',
            'peran': 'mahasiswa', # Default
            # Field optional dikosongkan dulu
            'nim': '', 'program_studi': '',
            'id_dosen': '', 'jurusan': '', 'bidang_keahlian': '',
            'id_mitra': '', 'organisasi': ''
        }

    def get_valid_choice(self, field_name):
        """
        Helper Cerdas: Mengambil opsi valid pertama dari field form secara dinamis.
        Ini mencegah error 'Select a valid choice' jika pilihan di model berubah-ubah.
        """
        form = UserRegistrationForm()
        # Ambil list choices dari field
        choices = form.fields[field_name].choices
        # Cari key pertama yang tidak kosong (bukan '---------')
        for key, value in choices:
            if key: 
                return key
        return None

    # --- 1. Test Logic Password Matching ---
    def test_tc_reg_01_password_mismatch(self):
        """Menguji jika password dan konfirmasi tidak sama"""
        data = self.get_base_data()
        data['password'] = 'passA'
        data['password2'] = 'passB' # BEDA
        
        form = UserRegistrationForm(data=data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("Password tidak cocok.", form.errors.get('__all__', []) + form.errors.get('password2', []))

    # --- 2. Test Logic Peran: MAHASISWA ---
    def test_tc_reg_02_mahasiswa_valid(self):
        """Jalur Mahasiswa: Data lengkap -> Valid"""
        data = self.get_base_data()
        data['peran'] = 'mahasiswa'
        data['nim'] = '12345678'
        
        # PERBAIKAN: Ambil kode prodi yang valid secara dinamis
        valid_prodi = self.get_valid_choice('program_studi')
        if not valid_prodi:
            self.skipTest("Tidak ada pilihan Program Studi di Model CustomUser")
            
        data['program_studi'] = valid_prodi 
        
        form = UserRegistrationForm(data=data)
        # Debugging message jika masih gagal
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_tc_reg_03_mahasiswa_invalid_missing_fields(self):
        """Jalur Mahasiswa: NIM/Prodi kosong -> Error"""
        data = self.get_base_data()
        data['peran'] = 'mahasiswa'
        data['nim'] = '' # KOSONG
        data['program_studi'] = '' # KOSONG
        
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nim', form.errors)
        # Error program studi mungkin muncul atau tidak tergantung cleaning order, 
        # tapi NIM pasti error karena logika clean() kita.
        self.assertIn('NIM wajib diisi untuk Mahasiswa.', form.errors.get('nim', []))

    # --- 3. Test Logic Peran: DOSEN ---
    def test_tc_reg_04_dosen_valid(self):
        """Jalur Dosen: Data lengkap -> Valid"""
        data = self.get_base_data()
        data['peran'] = 'dosen'
        data['id_dosen'] = 'DSN001'
        data['bidang_keahlian'] = 'AI'
        
        form = UserRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_tc_reg_05_dosen_invalid_missing_fields(self):
        """Jalur Dosen: ID Dosen kosong -> Error"""
        data = self.get_base_data()
        data['peran'] = 'dosen'
        data['id_dosen'] = '' # KOSONG
        data['bidang_keahlian'] = 'AI'
        
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('id_dosen', form.errors)

    # --- 4. Test Logic Peran: MITRA ---
    def test_tc_reg_06_mitra_valid(self):
        """Jalur Mitra: Data lengkap -> Valid"""
        data = self.get_base_data()
        data['peran'] = 'mitra'
        data['id_mitra'] = 'MTR001'
        data['organisasi'] = 'PT Maju'
        data['bidang_keahlian'] = 'Industri'
        
        form = UserRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_tc_reg_07_mitra_invalid_missing_fields(self):
        """Jalur Mitra: Organisasi kosong -> Error"""
        data = self.get_base_data()
        data['peran'] = 'mitra'
        data['id_mitra'] = 'MTR001'
        data['organisasi'] = '' # KOSONG
        
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('organisasi', form.errors)