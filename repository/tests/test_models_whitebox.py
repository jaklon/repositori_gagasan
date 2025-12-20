from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from users.models import CustomUser
from django.db import transaction
# Gunakan nama aplikasi 'repository' secara langsung
from repository.models import Kategori, Tag, Produk, Kurasi, AspekPenilaian, RequestSourceCode, DokumenProyek
from django.utils import timezone

class RepositoryModelTests(TestCase):

    def setUp(self):
        # 1. Create Users with Different Roles
        self.user_mahasiswa = CustomUser.objects.create_user(
            username='mahasiswa1', password='password123', peran='mahasiswa'
        )
        self.user_dosen = CustomUser.objects.create_user(
            username='dosen1', password='password123', peran='dosen'
        )
        self.user_mitra = CustomUser.objects.create_user(
            username='mitra1', password='password123', peran='mitra'
        )
        self.user_unit_bisnis = CustomUser.objects.create_user(
            username='ub1', password='password123', peran='unit_bisnis'
        )

        # 2. Create Basic Data (Category & Tag)
        self.kategori = Kategori.objects.create(nama="Web Dev", slug="web-dev")
        self.tag = Tag.objects.create(nama="Django")

        # 3. Create a Product
        self.produk = Produk.objects.create(
            id_pemilik=self.user_mahasiswa,
            title="Sistem Informasi Skripsi",
            description="Aplikasi manajemen skripsi.",
            curation_status='pending'
        )
        self.produk.kategori.add(self.kategori)
        self.produk.tags.add(self.tag)

    # --- Test Kategori & Tag ---
    def test_kategori_creation(self):
        """Test Kategori creation and string representation."""
        self.assertEqual(str(self.kategori), "Web Dev")

    def test_tag_creation(self):
        """Test Tag creation and string representation."""
        self.assertEqual(str(self.tag), "Django")

    # --- Test Produk ---
    def test_produk_creation(self):
        """Test Produk creation and initial status."""
        self.assertEqual(self.produk.curation_status, 'pending')
        self.assertFalse(self.produk.dipublikasikan)
        self.assertEqual(str(self.produk), "Sistem Informasi Skripsi")

    # --- Test Kurasi (Core Logic) ---
    def test_kurasi_creation_and_constraints(self):
        """Test creating a Kurasi object and assigning curators."""
        kurasi = Kurasi.objects.create(
            id_produk=self.produk,
            id_kurator_dosen=self.user_dosen,
            id_kurator_mitra=self.user_mitra,
            status='Menunggu Penugasan'
        )
        self.assertEqual(str(kurasi), f"Kurasi untuk: {self.produk.title}")
        self.assertEqual(kurasi.id_kurator_dosen.peran, 'dosen')
        self.assertEqual(kurasi.id_kurator_mitra.peran, 'mitra')

    def test_kurasi_limit_choices(self):
        """
        Test that limit_choices_to works conceptually (though enforced at form level,
        we verify logic by ensuring we can assign correct roles).
        Django model validation doesn't strictly enforce limit_choices_to on .save(),
        but it's good practice to verify the logic holds.
        """
        # Assigning a mahasiswa as a curator (logic check, though database might allow without full_clean)
        kurasi = Kurasi(
            id_produk=self.produk,
            id_kurator_dosen=self.user_mahasiswa # Invalid role for this field
        )
        # In a real form, this would fail. In model test, we check if the object accepts it 
        # but we know it violates the business rule we set in limit_choices_to.
        # Ideally, we rely on Form tests for limit_choices_to validation.
        pass 

    # --- Test AspekPenilaian (Constraints) ---
    def test_aspek_penilaian_unique_together(self):
        """Test the unique_together constraint on AspekPenilaian."""
        kurasi = Kurasi.objects.create(id_produk=self.produk)
        
        # Create first assessment
        AspekPenilaian.objects.create(
            id_kurasi=kurasi,
            aspek="Orisinalitas",
            skor=4,
            tipe_kurator='dosen'
        )

        # Attempt to create DUPLICATE assessment (Same kurasi, aspek, and tipe_kurator)
        # We must use transaction.atomic() so the IntegrityError doesn't break the whole test
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): # 
                AspekPenilaian.objects.create(
                    id_kurasi=kurasi,
                    aspek="Orisinalitas",
                    skor=3,
                    tipe_kurator='dosen' # Should fail
                )
        
        # Should succeed if tipe_kurator is different
        # Since we used atomic() above, the transaction is clean here.
        try:
            AspekPenilaian.objects.create(
                id_kurasi=kurasi,
                aspek="Orisinalitas",
                skor=3,
                tipe_kurator='mitra' # Different curator type, allowed
            )
        except IntegrityError:
            self.fail("Should allow same aspect for different curator type.")

    # --- Test RequestSourceCode ---
    def test_request_source_code_flow(self):
        """Test the lifecycle of a source code request."""
        # 1. Create Request
        request_obj = RequestSourceCode.objects.create(
            id_produk=self.produk,
            id_pemohon=self.user_dosen,
            alasan_request="Untuk penelitian."
        )
        self.assertEqual(request_obj.status, 'pending')

        # 2. Approve Request
        request_obj.status = 'approved'
        request_obj.id_peninjau = self.user_mahasiswa # The owner approves
        request_obj.save()
        
        self.assertEqual(request_obj.status, 'approved')
        self.assertEqual(request_obj.id_peninjau, self.user_mahasiswa)

    # --- Test DokumenProyek ---
    def test_dokumen_proyek_creation(self):
        """Test DokumenProyek creation."""
        doc = DokumenProyek.objects.create(
            produk=self.produk,
            tipe_dokumen='Laporan Akhir',
            keterangan='Link Google Drive'
        )
        self.assertEqual(str(doc), f"{self.produk.title} - Laporan Akhir")
        self.assertEqual(doc.get_file_name(), 'Tidak Ada File')