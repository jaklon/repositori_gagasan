import io
from PIL import Image

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import formset_factory

# Import model dari Users app
from users.models import CustomUser

# Import model dan form dari Repository app
# Pastikan file ini berada di dalam folder aplikasi repository
# Gunakan nama aplikasi 'repository' secara eksplisit
from repository.models import Produk, Kategori, Tag, DokumenProyek
from repository.forms import ProdukForm, DokumenProyekForm, DokumenProyekFormSet

class ProdukFormWhiteBoxTest(TestCase):

    def setUp(self):
        # 1. Setup User & Kategori
        self.user_mhs = CustomUser.objects.create_user(
            username='mahasiswa_test', 
            password='password123', 
            peran='mahasiswa', 
            program_studi='TI' 
        )
        self.user_dosen = CustomUser.objects.create_user(
            username='dosen_test', 
            password='password123', 
            peran='dosen', 
            program_studi='TI'
        )
        self.kategori_web = Kategori.objects.create(nama="Web Development", slug="web-dev")
        
        # 2. GENERATE GAMBAR VALID (Penting agar ImageField tidak error)
        # Kita membuat gambar 100x100 pixel berwarna merah secara memori
        img_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        
        self.valid_image = SimpleUploadedFile(
            name='poster_valid.jpg',
            content=img_io.read(),
            content_type='image/jpeg'
        )

    def test_tc01_save_logic_mahasiswa_update_prodi_and_tags(self):
        """[WHITE BOX] Tes logika update user & tags"""
        
        # Ambil salah satu pilihan valid dari CustomUser secara dinamis
        pilihan_prodi = dict(CustomUser.PROGRAM_STUDI_CHOICES)
        # Ambil key pertama yang BUKAN 'TI' (untuk tes perubahan), atau pakai 'TI' jika cuma itu yang ada
        # Logic: Ambil list keys, filter yg bukan 'TI', kalau kosong ambil 'TI'
        keys = list(pilihan_prodi.keys())
        valid_prodi_code = next((k for k in keys if k != 'TI'), keys[0])

        form_data = {
            'title': 'Sistem Informasi Skripsi',
            'description': 'Deskripsi Lengkap',
            'source_code_link': 'https://github.com/test',
            'demo_link': 'https://demo.com',
            'program_studi': valid_prodi_code, # Gunakan kode yang PASTI valid
            'tags_input': 'Python,  Django Framework ', 
            'kategori': [self.kategori_web.id]
        }
        
        # Gunakan gambar valid yang dibuat di setUp
        file_data = {'poster_image': self.valid_image}

        form = ProdukForm(data=form_data, files=file_data)
        
        # Debugging: Jika masih error, print errornya agar tahu kenapa
        if not form.is_valid():
            print(f"\n[DEBUG TC01 ERROR]: {form.errors}\n")
            
        self.assertTrue(form.is_valid())

        # Action: Save
        produk = form.save(owner=self.user_mhs)

        # Assertion
        self.user_mhs.refresh_from_db()
        # Cek apakah prodi berubah sesuai input form
        self.assertEqual(self.user_mhs.program_studi, valid_prodi_code)
        
        tags = produk.tags.all()
        self.assertEqual(tags.count(), 2)

    def test_tc02_save_logic_dosen_no_update(self):
        """[WHITE BOX] Tes dosen tidak terupdate prodinya"""
        
        pilihan_prodi = dict(CustomUser.PROGRAM_STUDI_CHOICES)
        keys = list(pilihan_prodi.keys())
        valid_prodi_code = next((k for k in keys if k != 'TI'), keys[0])

        form_data = {
            'title': 'Penelitian AI',
            'description': 'Deskripsi',
            'source_code_link': 'https://github.com',
            'demo_link': 'https://demo.com',
            'program_studi': valid_prodi_code, 
            'tags_input': 'AI',
            'kategori': [self.kategori_web.id]
        }
        file_data = {'poster_image': self.valid_image} # Gunakan gambar valid

        form = ProdukForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid())

        # Action: Save owner Dosen
        form.save(owner=self.user_dosen)

        # Assertion
        self.user_dosen.refresh_from_db()
        # Prodi dosen HARUS TETAP 'TI' (sesuai setup awal), JANGAN berubah jadi valid_prodi_code
        self.assertEqual(self.user_dosen.program_studi, 'TI')
        
    def test_tc03_validation_logic_kategori(self):
        # Tes validasi kategori (Kode ini tidak perlu gambar karena error diharapkan muncul duluan)
        pilihan_prodi = dict(CustomUser.PROGRAM_STUDI_CHOICES)
        valid_prodi_code = list(pilihan_prodi.keys())[0]

        form_data = {
            'title': 'Test',
            'description': 'Desc',
            'program_studi': valid_prodi_code,
            'tags_input': 'Tag',
            'kategori': [] 
        }
        form = ProdukForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('kategori', form.errors)


class DokumenProyekFormWhiteBoxTest(TestCase):
    """
    Fokus pada logika XOR di method clean():
    (File Ada OR Keterangan Ada) == True
    """

    def test_tc04_logic_xor_file_only(self):
        # Jalur A: File ada, Keterangan kosong -> Valid
        file_doc = SimpleUploadedFile("laporan.pdf", b"content")
        form_data = {
            'tipe_dokumen': 'Laporan Akhir', 
            'keterangan': ''
        }
        file_data = {'file_dokumen': file_doc}
        
        form = DokumenProyekForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), f"Errors: {form.errors}")

    def test_tc05_logic_xor_keterangan_only(self):
        # Jalur B: File kosong, Keterangan ada -> Valid
        form_data = {
            'tipe_dokumen': 'Lainnya', 
            'keterangan': 'Link Google Drive'
        }
        form = DokumenProyekForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_tc06_logic_xor_fail(self):
        # Jalur C: File kosong DAN Keterangan kosong -> Error
        form_data = {
            'tipe_dokumen': 'Laporan Akhir', 
            'keterangan': ''
        }
        form = DokumenProyekForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        # Pastikan pesan error custom muncul
        self.assertIn("Wajib diisi: Berikan keterangan/link ATAU unggah file.", 
                      form.errors.get('keterangan', []))


class DokumenFormSetWhiteBoxTest(TestCase):
    """
    Fokus pada RequiredDokumenFormSet method clean():
    Looping formset dan menghitung total_valid_entries.
    """

    def test_tc07_formset_aggregation_fail(self):
        """
        [WHITE BOX] Loop berjalan, tapi variable total_valid_entries tetap 0.
        Output: ValidationError pada non_form_errors.
        """
        # Data Management Form (Wajib untuk formset)
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '5',
            
            # Form ke-0: Diisi tapi tidak lengkap (Tipe ada, File/Ket kosong)
            'form-0-tipe_dokumen': 'Laporan Akhir', 
            'form-0-file_dokumen': '',
            'form-0-keterangan': '', 
        }
        
        formset = DokumenProyekFormSet(data=data, queryset=DokumenProyek.objects.none())
        
        # Validasi Formset
        self.assertFalse(formset.is_valid())
        
        # Cek Error Global Formset (bukan error per form)
        non_form_errors = formset.non_form_errors()
        self.assertIn("Anda wajib mengunggah minimal satu Dokumen Pendukung", str(non_form_errors))

    def test_tc08_formset_aggregation_success(self):
        """
        [WHITE BOX] Loop berjalan, total_valid_entries >= 1.
        Output: Valid.
        """
        data = {
            'form-TOTAL_FORMS': '2', # Submit 2 form
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '5',
            
            # Form 0: Valid (Pakai Keterangan)
            'form-0-tipe_dokumen': 'Manual Book', 
            'form-0-keterangan': 'Link Docs',
            
            # Form 1: Kosong (Harusnya diabaikan oleh loop logic)
            'form-1-tipe_dokumen': '', 
            'form-1-keterangan': '',
        }
        
        formset = DokumenProyekFormSet(data=data, queryset=DokumenProyek.objects.none())
        self.assertTrue(formset.is_valid(), f"Formset Error: {formset.errors}")