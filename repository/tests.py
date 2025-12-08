from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from users.models import CustomUser
from repository.models import Produk, Kurasi, AspekPenilaian, Kategori
from .views import ProjectForm, is_unit_bisnis

# Tambahan library untuk membuat gambar valid
import io
from PIL import Image

class ProjectFormLogicTest(TestCase):
    def setUp(self):
        file_obj = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file_obj, format='JPEG')
        file_obj.seek(0) # Kembali ke awal file

        self.dummy_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=file_obj.read(),
            content_type='image/jpeg'
        )

        self.kategori = Kategori.objects.create(nama="Web", slug="web")
        self.user = CustomUser.objects.create_user(username="mhs_test", peran="mahasiswa")

    def test_source_code_link_validation_invalid(self):
        """
        White Box: Menguji jalur 'else' pada validasi link (Link salah).
        """
        form_data = {
            'title': 'Proyek Invalid',
            'description': 'Deskripsi',
            'demo_link': 'https://demo.com',
            'program_studi': 'D4 TI',
            'kategori': self.kategori.id,
            'source_code_link': 'https://evil-website.com', 
            'tags_input': 'tag1, tag2'
        }
        file_data = {'poster_image': self.dummy_image}
        
        form = ProjectForm(data=form_data, files=file_data)
        
        self.assertFalse(form.is_valid()) 
        self.assertIn('Link harus berasal dari github.com atau drive.google.com.', form.errors['source_code_link'])

    def test_source_code_link_validation_valid(self):
        """
        White Box: Menguji jalur 'if' yang benar pada validasi link (Link benar).
        """
        form_data = {
            'title': 'Proyek Valid',
            'description': 'Deskripsi',
            'demo_link': 'https://demo.com',
            'program_studi': 'D4 TI',
            'kategori': self.kategori.id,
            'source_code_link': 'https://github.com/user/repo',
            'tags_input': 'python, django'
        }
        file_data = {'poster_image': self.dummy_image}
        
        form = ProjectForm(data=form_data, files=file_data)
        
        self.assertTrue(form.is_valid(), form.errors)

    def test_tags_parsing_logic(self):
        """
        White Box: Menguji logika looping split string tags di method save() form.
        """
        form_data = {
            'title': 'Proyek Tags',
            'description': 'Deskripsi',
            'demo_link': 'https://demo.com',
            'program_studi': 'D4 TI',
            'kategori': self.kategori.id,
            'source_code_link': 'https://github.com/repo',
            'tags_input': 'Python, Django Framework,  Backend ',
        }
        file_data = {'poster_image': self.dummy_image}
        
        form = ProjectForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), form.errors)
        
        # Simpan form
        produk = form.save(commit=True, owner=self.user)
        
        # Cek apakah tags tersimpan benar (harus ada 3 tag)
        self.assertEqual(produk.tags.count(), 3)
        self.assertTrue(produk.tags.filter(nama="backend").exists())

class HelperFunctionTest(TestCase):
    def test_is_unit_bisnis_check(self):
        """
        White Box: Menguji fungsi helper is_unit_bisnis
        """
        ub_user = CustomUser.objects.create_user(username="ub", peran="unit_bisnis")
        self.assertTrue(is_unit_bisnis(ub_user))

        dosen_user = CustomUser.objects.create_user(username="dosen", peran="dosen")
        self.assertFalse(is_unit_bisnis(dosen_user))

class AspekPenilaianTest(TestCase):
    def setUp(self):
        self.pemilik = CustomUser.objects.create_user(username="mahasiswa1", password="password123", peran="mahasiswa")
        self.dosen = CustomUser.objects.create_user(username="dosen1", password="password123", peran="dosen")
        self.produk = Produk.objects.create(id_pemilik=self.pemilik, title="Aplikasi Skripsi")
        self.kurasi = Kurasi.objects.create(id_produk=self.produk, id_kurator_dosen=self.dosen)

    def test_unique_together_constraint(self):
        AspekPenilaian.objects.create(
            id_kurasi=self.kurasi, 
            aspek="Keamanan", 
            tipe_kurator="dosen", 
            skor=3
        )
        with self.assertRaises(IntegrityError):
            AspekPenilaian.objects.create(
                id_kurasi=self.kurasi, 
                aspek="Keamanan", 
                tipe_kurator="dosen", 
                skor=4
            )

    def test_str_method_logic(self):
        aspek_null = AspekPenilaian.objects.create(
            id_kurasi=self.kurasi, aspek="UI/UX", tipe_kurator="dosen", skor=None
        )
        self.assertIn("Belum dinilai", str(aspek_null))

        aspek_isi = AspekPenilaian.objects.create(
            id_kurasi=self.kurasi, aspek="Fitur", tipe_kurator="dosen", skor=4
        )
        self.assertIn("Sangat Baik", str(aspek_isi))