Repositori Gagasan - Sistem Informasi Kurasi Produk Inovasi
📋 Deskripsi Proyek
Repositori Gagasan adalah platform berbasis web yang dirancang untuk Fakultas Ilmu Komputer PNJ. Sistem ini berfungsi sebagai wadah digital untuk mengumpulkan, mengurasi, dan mempublikasikan karya inovasi (produk) mahasiswa. Sistem ini memfasilitasi kolaborasi antara Mahasiswa, Dosen, dan Mitra Industri melalui alur kerja kurasi yang terstruktur.

🚀 Fitur Utama
Multi-Role User: Mendukung 4 peran pengguna dengan dashboard khusus:
1. Mahasiswa: Mengunggah proyek, memantau status, dan melihat portofolio.
2. Dosen: Bertindak sebagai Kurator Akademik untuk menilai aspek teknis/ilmiah.
3. Mitra Industri: Bertindak sebagai Kurator Industri untuk menilai kelayakan bisnis.
4. Unit Bisnis: Administrator yang mengelola alur kurasi, pengguna, dan publikasi.

Alur Kurasi Terintegrasi:
1. Seleksi: Unit Bisnis memilih proyek potensial dari Repositori.
2. Penugasan: Penunjukan kurator Dosen dan Mitra.
3. Penilaian: Sistem penilaian (skoring) online oleh kurator.
4. Review & Keputusan: Penetapan status akhir (Layak, Revisi, Ditolak).
5. Publikasi: Penayangan produk di Katalog Publik.

Manajemen Akses Source Code: Fitur permintaan izin untuk mengakses kode sumber proyek.

Katalog Publik: Halaman pencarian dan filter untuk menelusuri karya mahasiswa.

🛠️ Teknologi yang Digunakan
- Backend: Python (Django 5.2.7)
- Database: PostgreSQL
- Frontend: Django Templates + Tailwind CSS (via CDN) + JavaScript (Vanilla & Alpine.js)
- Styling: Custom CSS & Font Awesome

⚙️ Prasyarat Instalasi
Pastikan Anda telah menginstal:

- Python 3.10+
- PostgreSQL
- Virtual Environment (disarankan)

📦 Cara Instalasi & Menjalankan
1. Clone Repository

git clone [https://github.com/jaklon/repositori_gagasan]
cd repositori_gagasan

2. Buat dan Aktifkan Virtual Environment

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

3. Instal Dependencies
pip install django psycopg2-binary

# Jika ada file requirements.txt: pip install -r requirements.txt
Konfigurasi Database Buat database PostgreSQL bernama gagasan_db (atau sesuaikan di gagasan_backend/settings.py). Pastikan user/password database sesuai dengan konfigurasi di settings.py:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gagasan_db',
        'USER': 'postgres',
        'PASSWORD': 'password_anda',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

4. Migrasi Database
python manage.py makemigrations
python manage.py migrate
Buat Superuser (Opsional)

python manage.py createsuperuser

5. Jalankan Server
python manage.py runserver
Akses aplikasi di http://127.0.0.1:8000/

📂 Struktur Folder
1. gagasan_backend/: Konfigurasi utama proyek (settings, urls, wsgi).
2. repository/: App utama untuk logika produk, kurasi, dan katalog.
3. users/: App untuk manajemen pengguna, autentikasi, dan profil.
4. templates/: File HTML (Dashboard, Katalog, Form).
5. static/: File CSS, JavaScript, dan Gambar statis.
6. poster_images/: Direktori media untuk upload gambar proyek.

📝 Catatan Penting
* Sistem menggunakan mekanisme Approval User. Pendaftar baru tidak bisa langsung login sebelum disetujui oleh Unit Bisnis melalui menu "Manajemen User".
* Pastikan koneksi internet tersedia saat pengembangan karena Tailwind CSS dan Font Awesome dimuat melalui CDN.

Dibuat untuk Proyek PBL Kelompok TI CCIT 5A - Politeknik Negeri Jakarta














