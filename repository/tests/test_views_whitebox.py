from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import CustomUser
from repository.models import Produk, Kategori, Kurasi, RequestSourceCode, AspekPenilaian, Tag
from django.utils import timezone
from repository.views import AssessmentForm
import io
from PIL import Image

class BaseSetup(TestCase):
    """
    Setup dasar untuk membuat User, Kategori, dan Helper function
    yang akan digunakan di semua class test.
    """
    def setUp(self):
        self.client = Client()

        # 1. Setup Kategori
        self.kategori = Kategori.objects.create(nama="Web Development", slug="web-dev")

        # 2. Setup Users dengan berbagai peran
        # Mahasiswa
        self.user_mhs = CustomUser.objects.create_user(
            username='mhs_test', password='password123', email='mhs@test.com',
            peran='mahasiswa', status='aktif', is_approved=True, program_studi='D4 TI'
        )
        # Dosen
        self.user_dosen = CustomUser.objects.create_user(
            username='dosen_test', password='password123', email='dosen@test.com',
            peran='dosen', status='aktif', is_approved=True, jurusan='TIK'
        )
        # Mitra
        self.user_mitra = CustomUser.objects.create_user(
            username='mitra_test', password='password123', email='mitra@test.com',
            peran='mitra', status='aktif', is_approved=True, organisasi='PT Tech'
        )
        # Unit Bisnis
        self.user_ub = CustomUser.objects.create_user(
            username='ub_test', password='password123', email='ub@test.com',
            peran='unit_bisnis', status='aktif', is_approved=True
        )

        # 3. Helper untuk membuat gambar dummy (valid image)
        self.poster_image = self.generate_image()

    def generate_image(self):
        """Membuat file gambar dummy valid untuk upload"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile("test_poster.jpg", file.read(), content_type="image/jpeg")


class PublicViewTests(BaseSetup):
    """Pengujian untuk halaman yang bisa diakses publik atau tanpa login khusus"""

    def setUp(self):
        super().setUp()
        # Buat produk yang sudah dipublikasikan
        self.produk_pub = Produk.objects.create(
            id_pemilik=self.user_mhs,
            title="Proyek Publik",
            description="Deskripsi",
            curation_status="published",
            dipublikasikan=True,
            poster_image=self.poster_image
        )
        self.produk_pub.kategori.add(self.kategori)

    def test_catalog_view(self):
        """Test halaman katalog bisa diakses dan menampilkan produk"""
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog.html')
        self.assertContains(response, "Proyek Publik")

    def test_project_detail_view(self):
        """Test detail proyek"""
        response = self.client.get(reverse('project_detail', args=[self.produk_pub.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project_detail.html')
        self.assertEqual(response.context['project'], self.produk_pub)


class DashboardAccessTests(BaseSetup):
    """Pengujian keamanan akses dashboard berdasarkan peran (Role-Based Access)"""

    def test_mahasiswa_dashboard_access(self):
        self.client.login(username='mhs_test', password='password123')
        response = self.client.get(reverse('dashboard_mahasiswa'))
        self.assertEqual(response.status_code, 200)

        # Mahasiswa coba akses dashboard dosen -> Harus redirect atau error
        response = self.client.get(reverse('dashboard_dosen'))
        self.assertNotEqual(response.status_code, 200) # Biasanya 302 redirect

    def test_unit_bisnis_dashboard_access(self):
        self.client.login(username='ub_test', password='password123')
        response = self.client.get(reverse('dashboard_unit_bisnis'))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_access_manage_users(self):
        """User biasa tidak boleh akses manajemen user"""
        self.client.login(username='mhs_test', password='password123')
        response = self.client.get(reverse('manage_users'))
        # Karena menggunakan @user_passes_test, biasanya redirect ke login_url ('catalog')
        self.assertEqual(response.status_code, 302) 


class ProjectWorkflowTests(BaseSetup):
    """
    Pengujian alur lengkap:
    Upload -> Seleksi -> Penugasan -> Penilaian -> Publikasi
    """

    def test_01_upload_project(self):
        """Test Mahasiswa upload proyek"""
        self.client.login(username='mhs_test', password='password123')
        
        # Data Form Produk
        form_data = {
            'title': 'Aplikasi Skripsi Keren',
            'description': 'Deskripsi lengkap...',
            'kategori': self.kategori.id,
            'program_studi': 'D4 TI',
            'source_code_link': 'https://github.com/mhs/repo',
            'demo_link': 'https://demo.vercel.app',
            'tags_input': 'Python, Django',
            'poster_image': self.poster_image,
            
            # Data FormSet Dokumen (Wajib ada management form keys)
            'dokumen-TOTAL_FORMS': '1',
            'dokumen-INITIAL_FORMS': '0',
            'dokumen-MIN_NUM_FORMS': '0',
            'dokumen-MAX_NUM_FORMS': '1000',
            
            # Data dokumen ke-0 (opsional di view, tapi kita isi dummy biar valid)
            'dokumen-0-tipe_dokumen': 'Laporan Akhir',
            'dokumen-0-keterangan': 'Link Drive Laporan',
        }

        response = self.client.post(reverse('upload_project'), data=form_data, follow=True)
        
        # Cek sukses upload
        self.assertEqual(response.status_code, 200) # Redirect ke my_projects (200 setelah follow)
        self.assertTrue(Produk.objects.filter(title='Aplikasi Skripsi Keren').exists())
        
        # Simpan ID produk untuk step selanjutnya
        self.product = Produk.objects.get(title='Aplikasi Skripsi Keren')
        self.assertEqual(self.product.curation_status, 'pending')

    def test_02_selection_by_unit_bisnis(self):
        """Test Unit Bisnis menyeleksi proyek (Pending -> Selected)"""
        # Buat produk pending manual (bypass upload test di atas agar independen)
        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Pending", 
            curation_status='pending', poster_image=self.poster_image
        )
        product.kategori.add(self.kategori)

        self.client.login(username='ub_test', password='password123')
        response = self.client.post(reverse('select_for_curation', args=[product.id]), follow=True)
        
        product.refresh_from_db()
        self.assertEqual(product.curation_status, 'selected')

    def test_03_assign_curator(self):
        """Test Unit Bisnis menugaskan Dosen dan Mitra"""
        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Selected", 
            curation_status='selected', poster_image=self.poster_image
        )
        product.kategori.add(self.kategori)

        self.client.login(username='ub_test', password='password123')
        data = {
            'kurator_dosen': self.user_dosen.id,
            'kurator_mitra': self.user_mitra.id
        }
        response = self.client.post(reverse('handle_assign_curator', args=[product.id]), data=data, follow=True)
        
        product.refresh_from_db()
        self.assertEqual(product.curation_status, 'curators-assigned')
        
        # Cek objek Kurasi terbentuk
        self.assertTrue(Kurasi.objects.filter(id_produk=product).exists())
        kurasi = Kurasi.objects.get(id_produk=product)
        self.assertEqual(kurasi.id_kurator_dosen, self.user_dosen)

    def test_04_assessment_by_dosen(self):
        """Test Dosen melakukan penilaian"""
        # PERBAIKAN: Import dari views, bukan forms
        from repository.views import AssessmentForm 

        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Dinilai", 
            curation_status='curators-assigned', poster_image=self.poster_image
        )
        # Buat objek Kurasi manual
        kurasi = Kurasi.objects.create(
            id_produk=product, id_kurator_dosen=self.user_dosen, id_kurator_mitra=self.user_mitra,
            status='Penilaian Berlangsung', tanggal_penugasan=timezone.now()
        )
        
        # Buat SEMUA AspekPenilaian (Looping keys dari AssessmentForm)
        aspek_records = []
        for aspek_nama in AssessmentForm.ASPEK_CHOICES.keys():
            # Buat untuk dosen
            aspek_records.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='dosen'))
            # Buat untuk mitra
            aspek_records.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='mitra'))
        
        AspekPenilaian.objects.bulk_create(aspek_records)

        self.client.login(username='dosen_test', password='password123')
        
        # Data Nilai
        data = {
            'aspek_orisinalitas_inovasi': 4,
            'aspek_fungsionalitas_produk': 3,
            'aspek_desain_ui_ux_aksesibilitas': 4,
            'aspek_teknologi_kesesuaian_tren': 3,
            'aspek_kelayakan_bisnis_potensi_pasar': 4,
            'aspek_dokumentasi_teknis_panduan_pengguna': 3,
            'catatan': 'Bagus, lanjutkan!'
        }
        
        response = self.client.post(reverse('assess_project', args=[kurasi.id]), data=data, follow=True)
        
        kurasi.refresh_from_db()
        
        # Debugging
        if kurasi.nilai_akhir_dosen is None:
            print("\n[DEBUG] Gagal update nilai. Cek pesan error form/view.")
            
        self.assertIsNotNone(kurasi.nilai_akhir_dosen)
        self.assertEqual(kurasi.catatan_dosen, 'Bagus, lanjutkan!')
        self.assertEqual(kurasi.status, 'Penilaian Dosen Selesai')

    def test_05_final_decision_and_publish(self):
        """Test Unit Bisnis membuat keputusan final dan mempublikasikan"""
        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Final", 
            curation_status='assessment-complete', poster_image=self.poster_image
        )
        kurasi = Kurasi.objects.create(
            id_produk=product, id_kurator_dosen=self.user_dosen, id_kurator_mitra=self.user_mitra,
            status='Penilaian Lengkap', nilai_akhir_final=3.8
        )

        self.client.login(username='ub_test', password='password123')
        
        # 1. Buat Keputusan (Ready for Publication)
        decision_data = {
            'decision': 'ready-for-publication',
            'catatan_unit_bisnis': 'OK Siap.'
        }
        self.client.post(reverse('handle_project_decision', args=[kurasi.id]), data=decision_data)
        
        product.refresh_from_db()
        self.assertEqual(product.curation_status, 'ready-for-publication')
        self.assertEqual(product.final_decision, '🏆 Layak - Siap Publikasi') # Sesuai label form

        # 2. Publikasi ke Katalog
        publish_data = {'confirm_publish': True}
        self.client.post(reverse('handle_publish_project', args=[product.id]), data=publish_data)
        
        product.refresh_from_db()
        self.assertTrue(product.dipublikasikan)
        self.assertEqual(product.curation_status, 'published')


class UserManagementTests(BaseSetup):
    """Pengujian manajemen user oleh Unit Bisnis"""

    def test_approve_user(self):
        """Test Unit Bisnis menyetujui user baru"""
        # User baru status pending
        new_user = CustomUser.objects.create_user(
            username='new_mhs', password='p', peran='mahasiswa', is_approved=False, status='nonaktif'
        )

        self.client.login(username='ub_test', password='password123')
        response = self.client.post(reverse('approve_user', args=[new_user.id]), follow=True)
        
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_approved)
        self.assertEqual(new_user.status, 'aktif')

    def test_toggle_user_status(self):
        """Test Unit Bisnis menonaktifkan user"""
        self.client.login(username='ub_test', password='password123')
        
        # Nonaktifkan mahasiswa (setup di BaseSetup sudah aktif)
        self.client.post(reverse('toggle_active_user', args=[self.user_mhs.id]), data={'current_tab': 'all'})
        
        self.user_mhs.refresh_from_db()
        self.assertEqual(self.user_mhs.status, 'nonaktif')


class RequestSourceCodeTests(BaseSetup):
    """Pengujian fitur Request Source Code"""

    def setUp(self):
        super().setUp()
        self.product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Source", 
            poster_image=self.poster_image, dipublikasikan=True
        )

    def test_request_access(self):
        """User lain meminta akses source code"""
        # Login sebagai user lain (misal dosen)
        self.client.login(username='dosen_test', password='password123')
        
        data = {'alasan_request': 'Untuk penelitian'}
        response = self.client.post(reverse('request_source_code', args=[self.product.id]), data=data, follow=True)
        
        self.assertTrue(RequestSourceCode.objects.filter(id_produk=self.product, id_pemohon=self.user_dosen).exists())

    def test_owner_approve_request(self):
        """Pemilik menyetujui request"""
        # Buat request pending
        req = RequestSourceCode.objects.create(
            id_produk=self.product, id_pemohon=self.user_dosen, alasan_request='Tes', status='pending'
        )
        
        # Login sebagai pemilik (mahasiswa)
        self.client.login(username='mhs_test', password='password123')
        
        response = self.client.post(reverse('handle_access_request', args=[req.id, 'approve']), follow=True)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')
        self.assertEqual(req.id_peninjau, self.user_mhs)

    def test_delete_product_by_owner(self):
        """Test pemilik menghapus produk sendiri (status pending)"""
        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Hapus", 
            curation_status='pending', poster_image=self.poster_image
        )
        
        self.client.login(username='mhs_test', password='password123')
        response = self.client.post(reverse('delete_own_project', args=[product.id]), follow=True)
        
        self.assertFalse(Produk.objects.filter(id=product.id).exists())

    def test_fail_delete_product_in_curation(self):
        """Gagal hapus jika sudah masuk kurasi"""
        product = Produk.objects.create(
            id_pemilik=self.user_mhs, title="Proyek Kurasi", 
            curation_status='selected', poster_image=self.poster_image
        )
        
        self.client.login(username='mhs_test', password='password123')
        response = self.client.post(reverse('delete_own_project', args=[product.id]), follow=True)
        
        # Produk masih harus ada
        self.assertTrue(Produk.objects.filter(id=product.id).exists())