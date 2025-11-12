# repository/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages


# --- Models ---
from .models import Produk, Kategori, Kurasi, Tag, AspekPenilaian, RequestSourceCode
from users.models import CustomUser # Import CustomUser

# --- Utils ---
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required, user_passes_test # Tambahkan user_passes_test
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone # Import timezone
from django.http import JsonResponse
from django.urls import reverse # Import reverse jika digunakan untuk redirect


# --- PINDAHKAN FUNGSI HELPER INI KE ATAS ---
# Helper function untuk mengecek apakah user adalah Unit Bisnis
def is_unit_bisnis(user):
    # Pastikan user sudah login sebelum cek peran
    return user.is_authenticated and user.peran == 'unit_bisnis'
# --- AKHIR PEMINDAHAN ---


# === FORMS ===

# --- FORM UNGGAH PROYEK ---
class ProjectForm(forms.ModelForm):
    PROGRAM_STUDI_CHOICES = [
        ('', '---------'),
        ('D4 TI', 'D4 Teknik Informatika'),
        ('D4 TMD', 'D4 Teknik Multimedia Digital'),
        ('D3 TI', 'D3 Teknik Informatika'),
    ]
    program_studi = forms.ChoiceField(
        choices=PROGRAM_STUDI_CHOICES,
        required=True,
        label="Program Studi",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )

    kategori = forms.ModelMultipleChoiceField(
        queryset=Kategori.objects.all(),
        required=True, # Jadikan wajib
        label="Kategori Proyek (Pilih satu atau lebih)",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'category-checkbox-list'}) # Gunakan checkbox jika ingin multiple
    )

    source_code_link = forms.URLField(
        required=True,
        label="Link Source Code/Asset",
        help_text="Harus berupa URL valid dari github.com atau drive.google.com",
        widget=forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent', 'placeholder': 'https://github.com/user/repo atau https://drive.google.com/...'})
    )

    tags_input = forms.CharField(
        label="Technologies & Tags (Pisahkan dengan koma)",
        required=False,
        help_text="Contoh: React, Python, UI/UX",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )

    class Meta:
        model = Produk
        fields = [
            'title', 'description', 'poster_image', 'source_code_link', 
            'demo_link', 
            'kategori', 'tags_input',
        ]
        labels = {
            'title': 'Judul Proyek', 'description': 'Deskripsi Proyek',
            'poster_image': 'Gambar Overview Proyek', 'demo_link': 'Link Demo',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'}),
            'poster_image': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100 border border-gray-300 rounded-md p-1'}),
            'demo_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent', 'placeholder': 'https://proyek-anda.vercel.app atau https://youtube.com/...'}),
        }
        help_texts = {
             'poster_image': 'Wajib diisi. Max 5MB.',
             'demo_link': 'Wajib diisi. Link ke demo live atau video.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['poster_image'].required = True
        self.fields['source_code_link'].required = True 
        self.fields['demo_link'].required = True
        self.fields['program_studi'].required = True 
        self.fields['kategori'].required = True

        if self.instance and self.instance.pk:
            self.initial['tags_input'] = ', '.join(t.nama for t in self.instance.tags.all())

    def clean_poster_image(self):
        image = self.cleaned_data.get('poster_image', False)
        if not image and (not self.instance or not self.instance.pk):
             raise ValidationError("Gambar overview proyek wajib diisi.")
        if image:
            if image.size > 5 * 1024 * 1024: # 5MB limit
                raise ValidationError("Ukuran gambar tidak boleh melebihi 5MB.")
        return image

    def clean_source_code_link(self):
        link = self.cleaned_data.get('source_code_link')
        if link:
            validate = URLValidator()
            try:
                validate(link)
            except ValidationError:
                 raise ValidationError("URL Source Code tidak valid.")
            if not ('github.com' in link or 'drive.google.com' in link):
                raise ValidationError("Link harus berasal dari github.com atau drive.google.com.")
        return link

    def clean_tags_input(self):
        tags_string = self.cleaned_data.get('tags_input', '')
        tag_names = [name.strip().lower() for name in tags_string.split(',') if name.strip()]
        tags_list = []
        if tag_names:
            for name in tag_names:
                if name: 
                    tag, created = Tag.objects.get_or_create(nama=name)
                    tags_list.append(tag)
        return tags_list 

    def save(self, commit=True, owner=None):
        instance = super().save(commit=False) 
        if owner:
            instance.id_pemilik = owner
        if not instance.pk:
            instance.curation_status = 'pending'
            instance.dipublikasikan = False

        # Simpan field dari form yang ada di model Produk
        instance.source_code_link = self.cleaned_data.get('source_code_link')

        if commit:
            instance.save() 
            kategori_list = self.cleaned_data.get('kategori')
            if kategori_list is not None:
                instance.kategori.set(kategori_list) 

            tags_list = self.cleaned_data.get('tags_input') 
            if tags_list is not None:
                instance.tags.set(tags_list) 

        return instance
# --- AKHIR FORM UNGGAH ---


# --- FORM PENUGASAN KURATOR ---
class AssignCuratorForm(forms.Form):
    kurator_dosen = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(peran='dosen', is_active=True, status='aktif'), 
        required=True, label="Kurator Dosen", empty_label="Pilih Dosen",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
    kurator_mitra = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(peran='mitra', is_active=True, status='aktif'), 
        required=True, label="Kurator Mitra Industri", empty_label="Pilih Mitra",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
# --- AKHIR FORM PENUGASAN ---


# --- FORM PENILAIAN ASPEK ---
class AssessmentForm(forms.Form):
    ASPEK_CHOICES = {
        'Orisinalitas & Inovasi': 15,
        'Fungsionalitas Produk': 20,
        'Desain UI/UX & Aksesibilitas': 15,
        'Teknologi & Kesesuaian Tren': 15,
        'Kelayakan Bisnis & Potensi Pasar': 20,
        'Dokumentasi Teknis & Panduan Pengguna': 15,
    }
    skor_choices_from_model = list(AspekPenilaian._meta.get_field('skor').choices or [])
    SCORE_CHOICES = [('', 'Pilih Skor')] + skor_choices_from_model

    def __init__(self, *args, **kwargs):
        initial_scores = kwargs.pop('initial_scores', {}) 
        super().__init__(*args, **kwargs)
        for aspek_nama in self.ASPEK_CHOICES.keys():
            field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
            self.fields[field_name] = forms.ChoiceField(
                label=aspek_nama,
                choices=self.SCORE_CHOICES,
                widget=forms.RadioSelect(attrs={'class': 'assessment-radio'}),
                required=True, 
                initial=initial_scores.get(aspek_nama) 
            )
    catatan = forms.CharField(
        label="Catatan Keseluruhan (Opsional)",
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
# --- AKHIR FORM PENILAIAN ---


# --- FORM KEPUTUSAN UNIT BISNIS ---
class DecisionForm(forms.Form):
    DECISION_CHOICES = [
        ('', 'Pilih keputusan final...'), 
        ('ready-for-publication', '泙 Layak - Siap Publikasi'),
        ('revision-minor', '鳩 Revisi Minor - Publikasi Setelah Perbaikan'),
        ('needs-coaching', '泯 Perlu Pembinaan - Tidak Dipublikasi'),
        ('rejected', '閥 Tidak Layak - Ditolak'),
    ]
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        required=True,
        label="Tetapkan Keputusan",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white appearance-none', 'id':'id_decision_modal'})
    )
    catatan_unit_bisnis = forms.CharField(
        label="Catatan Tambahan Unit Bisnis (Opsional)",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent', 'id':'id_catatan_unit_bisnis_modal'})
    )
# --- AKHIR FORM KEPUTUSAN ---


# --- FORM KONFIRMASI PUBLIKASI ---
class PublishConfirmationForm(forms.Form):
    confirm_publish = forms.BooleanField(
        required=True,
        label="Saya konfirmasi untuk mempublikasikan produk ini.",
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500', 'id': 'id_confirm_publish'})
    )
# --- AKHIR FORM KONFIRMASI ---


# === VIEWS ===

# --- CATALOG VIEW ---
def catalog_view(request):
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    projects = Produk.objects.filter(dipublikasikan=True).select_related('id_pemilik').prefetch_related('kategori', 'tags').order_by('-updated_at')

    if query:
        projects = projects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__nama__icontains=query) |
            Q(id_pemilik__username__icontains=query)
        ).distinct()

    if category_slug:
        projects = projects.filter(kategori__slug=category_slug)

    categories = Kategori.objects.all().order_by('nama')

    context = {
        'projects': projects,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': query,
    }
    return render(request, 'catalog.html', context)
# --- AKHIR CATALOG VIEW ---


# --- DASHBOARD VIEWS ---
@login_required
def dashboard_mahasiswa(request):
    if request.user.peran != 'mahasiswa':
        messages.error(request, "Akses dashboard tidak sesuai.")
        return redirect('catalog')
    
    # Ambil semua proyek milik user
    my_projects = Produk.objects.filter(id_pemilik=request.user).order_by('-created_at')
    
    # Hitung Statistik
    total_count = my_projects.count()
    published_count = my_projects.filter(dipublikasikan=True).count()
    
    # Status "Under Review" (semua status antara 'terpilih' dan 'selesai penilaian')
    review_statuses = ['selected', 'curators-assigned', 'assessment-dosen-done', 'assessment-mitra-done', 'assessment-complete']
    review_count = my_projects.filter(curation_status__in=review_statuses).count()
    
    # Status "Curated" (siap publikasi tapi belum live)
    curated_count = my_projects.filter(curation_status='ready-for-publication').count()

    context = {
        'my_projects': my_projects,
        'total_count': total_count,
        'published_count': published_count,
        'review_count': review_count,
        'curated_count': curated_count,
    }
    return render(request, 'dashboard/mahasiswa.html', context)

@login_required
def my_projects_view(request):
    """
    View baru untuk halaman "My Projects" yang menampilkan daftar lengkap.
    """
    if request.user.peran not in ['mahasiswa', 'dosen']: # Asumsi Dosen juga bisa lihat
        messages.error(request, "Akses tidak diizinkan.")
        return redirect('catalog')

    my_projects = Produk.objects.filter(id_pemilik=request.user).order_by('-created_at')
    
    context = {
        'my_projects': my_projects
    }
    return render(request, 'dashboard/mahasiswa_my_project.html', context)

@login_required
def dashboard_dosen(request):
    if request.user.peran != 'dosen':
        messages.error(request, "Akses dashboard tidak sesuai.")
        return redirect('catalog')

    # --- Logika untuk Statistik (Sesuai Figma) ---
    
    # 1. Pending Tasks (Tugas kurasi yang belum selesai)
    tugas_penilaian_qs = Kurasi.objects.filter(
        id_kurator_dosen=request.user,
        tanggal_selesai_dosen__isnull=True
    ).exclude(status='Menunggu Penugasan')
    pending_tasks_count = tugas_penilaian_qs.count()

    # 2. My Projects (Proyek yang diunggah oleh dosen sendiri)
    my_projects = Produk.objects.filter(id_pemilik=request.user).order_by('-created_at')
    my_projects_count = my_projects.count()
    
    # 3. Supervised (Contoh, karena data bimbingan belum ada)
    supervised_count = 3 # Ganti ini dengan kueri jika Anda punya relasi mahasiswa bimbingan
    
    # 4. Curated (Tugas kurasi yang sudah selesai)
    curated_count = Kurasi.objects.filter(
        id_kurator_dosen=request.user,
        tanggal_selesai_dosen__isnull=False
    ).count()

    context = {
        # Statistik untuk Kartu
        'pending_tasks_count': pending_tasks_count,
        'my_projects_count': my_projects_count,
        'supervised_count': supervised_count,
        'curated_count': curated_count,
        
        # Daftar untuk "Recently Supervised Projects" (Kita gunakan "My Projects" sebagai contoh)
        'recent_projects': my_projects,
    }
    # Render template BARU (yang akan kita buat di Langkah 4)
    return render(request, 'dashboard/dosen.html', context)


# ==================================
# === TAMBAHKAN DUA VIEW BARU INI ===
# ==================================
@login_required
def dosen_my_projects_view(request):
    """
    Halaman "My Projects" untuk Dosen (Daftar proyek milik dosen).
    """
    if request.user.peran != 'dosen':
        messages.error(request, "Akses tidak diizinkan.")
        return redirect('catalog')

    my_projects = Produk.objects.filter(id_pemilik=request.user).order_by('-created_at')
    
    context = {
        'my_projects': my_projects
    }
    # Render template BARU (yang akan kita buat di Langkah 5)
    return render(request, 'dashboard/dosen_my_project.html', context)

@login_required
def kurasi_produk_list_view(request):
    """
    Halaman "Kurasi Produk" (Daftar tugas penilaian).
    Ini adalah LOGIKA LAMA dari dashboard_dosen Anda.
    """
    if request.user.peran != 'dosen':
        messages.error(request, "Akses dashboard tidak sesuai.")
        return redirect('catalog')

    # 1. Kueri Dasar (Semua tugas yang ditugaskan ke user ini)
    tugas_penilaian_qs = Kurasi.objects.filter(
        id_kurator_dosen=request.user
    ).exclude(
        status='Menunggu Penugasan'  # Hanya ambil yang statusnya sudah 'Penilaian Berlangsung' atau selesai
    ).select_related('id_produk', 'id_produk__id_pemilik').order_by('tanggal_penugasan')

    # 2. Pisahkan ke daftar "Belum Dinilai" (di mana dosen ini BELUM selesai)
    belum_dinilai_list = tugas_penilaian_qs.filter(tanggal_selesai_dosen__isnull=True)

    # 3. Pisahkan ke daftar "Sudah Selesai" (di mana dosen ini SUDAH selesai)
    sudah_selesai_list = tugas_penilaian_qs.filter(tanggal_selesai_dosen__isnull=False)

    context = {
        # Statistik untuk halaman ini
        'total_tugas': tugas_penilaian_qs.count(),
        'belum_dinilai_count': belum_dinilai_list.count(),
        'sudah_selesai_count': sudah_selesai_list.count(),
        
        # Daftar list untuk ditampilkan di template
        'belum_dinilai_list': belum_dinilai_list,
        'sudah_selesai_list': sudah_selesai_list,
    }
    
    # Render template yangTADI kita ganti namanya
    return render(request, 'dashboard/kurasi_produk_list.html', context)

@login_required
def dashboard_mitra(request):
    if request.user.peran != 'mitra':
        messages.error(request, "Akses dashboard tidak sesuai.")
        return redirect('catalog')

    # --- Logika BARU untuk Statistik Dashboard Mitra ---
    
    # 1. Pending Tasks (Tugas kurasi yang belum selesai)
    tugas_penilaian_qs = Kurasi.objects.filter(
        id_kurator_mitra=request.user,
        tanggal_selesai_mitra__isnull=True
    ).exclude(status='Menunggu Penugasan')
    pending_tasks_count = tugas_penilaian_qs.count()

    # 2. Curated (Tugas kurasi yang sudah selesai)
    curated_count = Kurasi.objects.filter(
        id_kurator_mitra=request.user,
        tanggal_selesai_mitra__isnull=False
    ).count()

    # Ambil 3 proyek yang baru selesai dinilai untuk preview
    recent_projects = Kurasi.objects.filter(
        id_kurator_mitra=request.user,
        tanggal_selesai_mitra__isnull=False
    ).select_related('id_produk').order_by('-tanggal_selesai_mitra')[:3]

    context = {
        # Statistik untuk Kartu
        'pending_tasks_count': pending_tasks_count,
        'curated_count': curated_count,
        'recent_projects': recent_projects, # Untuk preview di dashboard
    }
    # Render template mitra.html (yang sekarang adalah dashboard)
    return render(request, 'dashboard/mitra.html', context)


# ==================================
# === TAMBAHKAN VIEW BARU INI ===
# ==================================
@login_required
def mitra_kurasi_produk_list_view(request):
    """
    Halaman "Kurasi Produk" untuk Mitra (Daftar tugas penilaian).
    Ini adalah LOGIKA LAMA dari dashboard_mitra.
    """
    if request.user.peran != 'mitra':
        messages.error(request, "Akses dashboard tidak sesuai.")
        return redirect('catalog')

    # 1. Kueri Dasar (Semua tugas yang ditugaskan)
    tugas_penilaian_qs = Kurasi.objects.filter(
        id_kurator_mitra=request.user
    ).exclude(
        status='Menunggu Penugasan'
    ).select_related('id_produk', 'id_produk__id_pemilik').order_by('tanggal_penugasan')

    # 2. Pisahkan ke daftar "Belum Dinilai"
    belum_dinilai_list = tugas_penilaian_qs.filter(tanggal_selesai_mitra__isnull=True)

    # 3. Pisahkan ke daftar "Sudah Selesai"
    sudah_selesai_list = tugas_penilaian_qs.filter(tanggal_selesai_mitra__isnull=False)

    context = {
        'total_tugas': tugas_penilaian_qs.count(),
        'belum_dinilai_count': belum_dinilai_list.count(),
        'sudah_selesai_count': sudah_selesai_list.count(),
        'belum_dinilai_list': belum_dinilai_list,
        'sudah_selesai_list': sudah_selesai_list,
        'tipe_kurator': 'mitra' # TAMBAHAN PENTING untuk template
    }
    
    # Render template YANG SAMA DENGAN DOSEN
    return render(request, 'dashboard/kurasi_produk_list.html', context)

@login_required
def dashboard_unit_bisnis(request):
    if request.user.peran != 'unit_bisnis':
        return redirect('catalog') 

    total_produk = Produk.objects.count()
    proyek_terpublikasi = Produk.objects.filter(dipublikasikan=True).count()
    proyek_di_repository = Produk.objects.filter(curation_status='pending').count()
    proyek_menunggu_penugasan = Produk.objects.filter(curation_status='selected').count()
    status_penilaian = ['curators-assigned', 'Penilaian Berlangsung', 'Penilaian Dosen Selesai', 'Penilaian Mitra Selesai']
    proyek_dalam_penilaian = Produk.objects.filter(curation_status__in=status_penilaian).count()
    proyek_menunggu_keputusan = Produk.objects.filter(curation_status='assessment-complete').count()

    statistik_kategori = Kategori.objects.annotate(
        jumlah_proyek=Count('produk') 
    ).filter(jumlah_proyek__gt=0).order_by('-jumlah_proyek') 

    aktivitas_terkini = [
        {'nama': 'Produk "Smart Parking System" dipilih untuk kurasi', 'waktu': '10 menit yang lalu', 'pelaku': 'Admin Unit Bisnis'},
        {'nama': 'Kurator ditugaskan untuk "AI Chatbot"', 'waktu': '1 jam yang lalu', 'pelaku': 'Admin Unit Bisnis'},
        {'nama': 'Penilaian selesai untuk "IoT Monitoring"', 'waktu': '2 jam yang lalu', 'pelaku': 'Dr. Ahmad (Dosen)'},
    ]

    context = {
        'total_produk': total_produk,
        'proyek_terpublikasi': proyek_terpublikasi,
        'proyek_di_repository': proyek_di_repository,
        'proyek_menunggu_penugasan': proyek_menunggu_penugasan,
        'proyek_dalam_penilaian': proyek_dalam_penilaian,
        'proyek_menunggu_keputusan': proyek_menunggu_keputusan,
        'statistik_kategori': statistik_kategori,
        'aktivitas_terkini': aktivitas_terkini,
        'tugas_penugasan_mendesak': proyek_menunggu_penugasan,
        'tugas_keputusan_mendesak': proyek_menunggu_keputusan,
        'tugas_publikasi_mendesak': Produk.objects.filter(
            Q(curation_status='ready-for-publication') | Q(curation_status='revision-minor')
        ).filter(dipublikasikan=False).count(),
    }
    return render(request, 'dashboard/unit_bisnis.html', context)
# --- AKHIR DASHBOARD VIEWS ---

# --- VIEW BARU UNTUK DETAIL PROYEK ---
@login_required # Pastikan @login_required tetap ada
def project_detail_view(request, project_id):
    # Ambil proyek, pastikan prefetch data pemilik
    project = get_object_or_404(Produk.objects.select_related('id_pemilik').prefetch_related('kategori', 'tags'), id=project_id)
    
    # Coba ambil data kurasi terkait (jika ada)
    try:
        kurasi = Kurasi.objects.get(id_produk=project)
    except Kurasi.DoesNotExist:
        kurasi = None

    # Cek apakah user yang login sudah pernah request
    existing_request = RequestSourceCode.objects.filter(id_produk=project, id_pemohon=request.user).first()

    # HAPUS BLOK LOGIKA IZIN AKSES (if allowed_roles... s/d else...)
    # Langsung kirim data ke template
    context = {
        'project': project,
        'kurasi': kurasi, # Kirim None jika tidak ada
        'existing_request': existing_request, # Kirim status request (None atau objek)
    }
    return render(request, 'project_detail.html', context)
# --- AKHIR VIEW DETAIL PROYEK ---


# --- VIEW BARU UNTUK HANDLE REQUEST SOURCE CODE ---
@login_required
@require_POST  
def request_source_code_view(request, project_id):
    project = get_object_or_404(Produk, id=project_id)
    user = request.user

    if project.id_pemilik == user:
        messages.error(request, "Anda adalah pemilik proyek ini.")
        return redirect('project_detail', project_id=project.id)

    existing_request = RequestSourceCode.objects.filter(
        id_produk=project,
        id_pemohon=user
    ).first()

    if existing_request:
        messages.info(
            request,
            f"Anda sudah pernah meminta akses untuk proyek ini (Status: {existing_request.get_status_display()})."
        )
        return redirect('project_detail', project_id=project.id)

    alasan = request.POST.get('alasan_request', '').strip()
    if not alasan:
        messages.error(request, "Alasan Permintaan (Alasan Request) wajib diisi.")
        return redirect('project_detail', project_id=project.id)

    RequestSourceCode.objects.create(
        id_produk=project,
        id_pemohon=user,
        alasan_request=alasan,  
        status='pending'
    )

    messages.success(
        request,
        f"Permintaan akses source code untuk '{project.title}' telah terkirim."
    )
    return redirect('project_detail', project_id=project.id)
# --- AKHIR VIEW REQUEST SOURCE CODE ---

# --- VIEW BARU: ACCESS REQUESTS (DAFTAR) ---
@login_required
def access_requests_view(request):
    # BARU: Izinkan mahasiswa, dosen, DAN unit_bisnis
    if request.user.peran not in ['mahasiswa', 'dosen', 'unit_bisnis']:
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog') 

    if request.user.peran == 'unit_bisnis':
        # BARU: Jika Unit Bisnis, tampilkan SEMUA request
        requests_for_my_projects = RequestSourceCode.objects.all().select_related(
            'id_pemohon', 'id_produk', 'id_produk__id_pemilik', 'id_peninjau'
        ).order_by('-tanggal_request')
    else:
        # LAMA: Mahasiswa/Dosen hanya melihat request untuk proyek milik mereka
        requests_for_my_projects = RequestSourceCode.objects.filter(
            id_produk__id_pemilik=request.user
        ).select_related(
            'id_pemohon', 'id_produk', 'id_peninjau'
        ).order_by('-tanggal_request')

    # Pisahkan antara yang pending dan yang sudah ditanggapi
    pending_requests = requests_for_my_projects.filter(status='pending')
    other_requests = requests_for_my_projects.exclude(status='pending')

    context = {
        'pending_requests': pending_requests,
        'other_requests': other_requests,
    }
    return render(request, 'dashboard/access_requests.html', context)
# --- AKHIR VIEW ACCESS REQUESTS ---


# --- VIEW BARU: HANDLE APPROVE/DENY REQUEST ---
@login_required
@require_POST 
def handle_access_request_view(request, request_id, action):
    req_object = get_object_or_404(RequestSourceCode, id=request_id)
    user = request.user

    # Logika Keamanan BARU
    is_owner = req_object.id_produk.id_pemilik == user
    is_unit_bisnis = user.peran == 'unit_bisnis'

    if not (is_owner or is_unit_bisnis):
        messages.error(request, "Anda tidak memiliki izin untuk mengelola permintaan ini.")
        return redirect('access_requests')

    # Pastikan status masih 'pending'
    if req_object.status != 'pending':
        messages.warning(request, "Permintaan ini sudah ditanggapi sebelumnya.")
        return redirect('access_requests')

    if action == 'approve':
        req_object.status = 'approved'
        req_object.id_peninjau = user  # Peninjau adalah user yg sedang login (bisa pemilik atau unit bisnis)
        req_object.save()
        messages.success(request, f"Permintaan dari '{req_object.id_pemohon.username}' telah disetujui.")
    elif action == 'deny':
        req_object.status = 'rejected'
        req_object.id_peninjau = user
        req_object.save()
        messages.warning(request, f"Permintaan dari '{req_object.id_pemohon.username}' telah ditolak.")
    # ...
    return redirect('access_requests')
# --- AKHIR VIEW HANDLE REQUEST ---


# --- REPOSITORY VIEWS (PERBAIKAN FINAL UNTUK REQ 3) ---
@login_required
def repository_view(request):
    # Requirement: Tampilkan SEMUA produk yang diupload,
    # termasuk yang sudah terkurasi dan dipublikasikan.
    
    # Ambil SEMUA proyek, diurutkan dari yang terbaru dibuat.
    projects_list = Produk.objects.all().select_related(
        'id_pemilik'
    ).prefetch_related(
        'kategori', 'tags'
    ).order_by('-created_at') # Urutkan berdasarkan tanggal dibuat

    # Hitung statistik
    # Total Proyek (total di sistem)
    total_proyek_all_internal = projects_list.count()
    # Terpilih untuk Kurasi (menunggu penugasan)
    total_proyek_selected = projects_list.filter(curation_status='selected').count()
    # Proyek di Repository (masih pending)
    total_proyek_repo = projects_list.filter(curation_status='pending').count()


    context = {
        'projects_list': projects_list, # Kirim satu daftar saja
        'total_proyek_repo_count': total_proyek_repo, # Stat: Pending
        'total_proyek_selected_count': total_proyek_selected, # Stat: Selected
        'total_proyek': total_proyek_all_internal, # Stat: Total
        'current_tab': 'all', # Hanya untuk menandakan (templat tidak lagi pakai tab)
    }
    return render(request, 'repository.html', context)
# --- AKHIR REPOSITORY VIEW ---


@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='repository')
def select_for_curation(request, project_id):
    project = get_object_or_404(Produk, id=project_id)
    if project.curation_status == 'pending':
        project.curation_status = 'selected'
        project.save(update_fields=['curation_status', 'updated_at'])
        messages.success(request, f"Proyek '{project.title}' telah berhasil dipilih untuk kurasi.")
        return redirect('repository')
    else:
        messages.warning(request, f"Proyek '{project.title}' tidak dalam status 'pending' (Status saat ini: {project.get_curation_status_display()}).")
        referer = request.META.get('HTTP_REFERER', reverse('repository'))
        return redirect(referer)
# --- AKHIR REPOSITORY VIEWS ---


# --- UPLOAD PROJECT VIEW ---
@login_required
def upload_project_view(request):
    if request.user.peran not in ['mahasiswa', 'dosen']:
         messages.error(request, "Hanya Mahasiswa dan Dosen yang dapat mengunggah proyek.")
         if request.user.peran == 'mitra': return redirect('dashboard_mitra')
         if is_unit_bisnis(request.user): return redirect('dashboard_unit_bisnis')
         return redirect('catalog')
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                project = form.save(commit=True, owner=request.user)
                messages.success(request, f"Proyek '{project.title}' berhasil diunggah dan menunggu seleksi.")
                if request.user.peran == 'mahasiswa': return redirect('dashboard_mahasiswa')
                elif request.user.peran == 'dosen': return redirect('dashboard_dosen')
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan saat menyimpan proyek: {e}")
    else:
        form = ProjectForm()
    context = {'form': form}
    return render(request, 'upload_project.html', context)
# --- AKHIR UPLOAD PROJECT VIEW ---


# --- CURATION ASSIGNMENT VIEWS ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def assign_curator_view(request):
    projects_selected = Produk.objects.filter(curation_status='selected').select_related('id_pemilik').prefetch_related('kategori').order_by('updated_at')
    assign_form = AssignCuratorForm()
    context = {
        'projects_selected': projects_selected,
        'assign_form': assign_form
    }
    return render(request, 'assign_curator.html', context)

@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='assign_curator_list')
def handle_assign_curator(request, project_id):
    project = get_object_or_404(Produk, id=project_id, curation_status='selected')
    form = AssignCuratorForm(request.POST)
    if form.is_valid():
        kurator_dosen = form.cleaned_data['kurator_dosen']
        kurator_mitra = form.cleaned_data['kurator_mitra']
        kurasi, created = Kurasi.objects.update_or_create(
            id_produk=project,
            defaults={
                'id_kurator_dosen': kurator_dosen,
                'id_kurator_mitra': kurator_mitra,
                'tanggal_penugasan': timezone.now(),
                'status': 'Penilaian Berlangsung',
                'tanggal_selesai_dosen': None, 'tanggal_selesai_mitra': None,
                'nilai_akhir_dosen': None, 'nilai_akhir_mitra': None,
                'nilai_akhir_final': None, 'catatan_dosen': None, 'catatan_mitra': None,
            }
        )
        AspekPenilaian.objects.filter(id_kurasi=kurasi).delete()
        aspek_list = AssessmentForm.ASPEK_CHOICES.keys()
        aspek_records_to_create = []
        for aspek_nama in aspek_list:
            aspek_records_to_create.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='dosen', skor=None))
            aspek_records_to_create.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='mitra', skor=None))
        AspekPenilaian.objects.bulk_create(aspek_records_to_create)
        project.curation_status = 'curators-assigned'
        project.save(update_fields=['curation_status', 'updated_at'])
        messages.success(request, f"Kurator berhasil ditugaskan untuk proyek '{project.title}'.")
        return redirect('assign_curator_list')
    else:
        error_message = "Gagal menugaskan kurator. "
        first_field_errors = next(iter(form.errors.values()), None)
        if first_field_errors: error_message += first_field_errors[0]
        else: error_message += " Pastikan kedua kurator dipilih."
        messages.error(request, error_message)
        return redirect('assign_curator_list')
# --- AKHIR CURATION ASSIGNMENT VIEWS ---


# --- ASSESSMENT VIEW ---
@login_required # Tambahkan ini jika belum ada
def assess_project_view(request, kurasi_id):
    kurasi = get_object_or_404(Kurasi.objects.select_related('id_produk'), id=kurasi_id)
    project = kurasi.id_produk
    user = request.user
    
    # === 1. TAMBAHKAN BARIS INI ===
    existing_request = RequestSourceCode.objects.filter(id_produk=project, id_pemohon=request.user).first()
    
    tipe_kurator = None
    existing_note = None
    is_completed = False # <-- Variabel BARU

    if user.peran == 'dosen' and kurasi.id_kurator_dosen == user:
        tipe_kurator = 'dosen'
        existing_note = kurasi.catatan_dosen
        if kurasi.tanggal_selesai_dosen: # <-- Cek BARU
            is_completed = True
            
    elif user.peran == 'mitra' and kurasi.id_kurator_mitra == user:
        tipe_kurator = 'mitra'
        existing_note = kurasi.catatan_mitra
        if kurasi.tanggal_selesai_mitra: # <-- Cek BARU
            is_completed = True

    if not tipe_kurator:
        messages.error(request, "Anda tidak ditugaskan untuk menilai proyek ini atau peran Anda tidak sesuai.")
        if user.peran == 'dosen': return redirect('kurasi_produk_list') # Link diperbarui
        if user.peran == 'mitra': return redirect('mitra_kurasi_produk_list') # <-- 2. PERBAIKI REDIRECT INI
        return redirect('catalog')

    existing_scores_qs = AspekPenilaian.objects.filter(id_kurasi=kurasi, tipe_kurator=tipe_kurator)
    initial_scores_dict = {score.aspek: score.skor for score in existing_scores_qs if score.skor is not None}
    
    initial_form_data = {'catatan': existing_note}
    for aspek_nama, skor in initial_scores_dict.items():
        field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
        initial_form_data[field_name] = skor

    if request.method == 'POST':
        
        # === TAMBAHAN: Blokir POST jika sudah selesai ===
        if is_completed:
            messages.error(request, "Penilaian ini sudah selesai dan tidak dapat diubah.")
            if tipe_kurator == 'dosen': return redirect('kurasi_produk_list')
            else: return redirect('mitra_kurasi_produk_list') # <-- 3. PERBAIKI REDIRECT INI
        # ===============================================

        form = AssessmentForm(request.POST, initial=initial_form_data)
        if form.is_valid():
            total_weighted_score = 0
            aspek_objects_to_update = []
            all_fields_valid = True
            for aspek_nama, bobot in AssessmentForm.ASPEK_CHOICES.items():
                field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
                skor_str = form.cleaned_data.get(field_name)
                if not skor_str:
                     all_fields_valid = False
                     form.add_error(field_name, "Skor harus dipilih.")
                     continue
                try:
                    skor = int(skor_str)
                    aspek_obj = AspekPenilaian.objects.get(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator=tipe_kurator)
                    aspek_obj.skor = skor
                    aspek_objects_to_update.append(aspek_obj)
                    total_weighted_score += skor * (bobot / 100.0)
                except AspekPenilaian.DoesNotExist:
                     messages.error(request, f"Terjadi kesalahan internal: data aspek '{aspek_nama}' tidak ditemukan.")
                     context = {
                         'kurasi': kurasi, 
                         'project': project, 
                         'form': form, 
                         'tipe_kurator': tipe_kurator,
                         'is_completed': is_completed, 
                         'existing_request': existing_request # <-- 4. PERBAIKI SINTAKS (koma hilang)
                     }
                     return render(request, 'assess_project.html', context)
                except (ValueError, TypeError):
                     all_fields_valid = False
                     form.add_error(field_name, "Skor tidak valid.")
            
            if not all_fields_valid:
                 messages.error(request, "Terdapat kesalahan pada form. Pastikan semua aspek terisi skor (1-4).")
            else:
                if aspek_objects_to_update:
                    AspekPenilaian.objects.bulk_update(aspek_objects_to_update, ['skor'])
                
                catatan_kurator = form.cleaned_data['catatan']
                previous_status = kurasi.status
                
                if tipe_kurator == 'dosen':
                    kurasi.catatan_dosen = catatan_kurator
                    kurasi.nilai_akhir_dosen = round(total_weighted_score, 2)
                    kurasi.tanggal_selesai_dosen = timezone.now()
                    if previous_status == 'Penilaian Berlangsung': kurasi.status = 'Penilaian Dosen Selesai'
                    elif previous_status == 'Penilaian Mitra Selesai': kurasi.status = 'Penilaian Lengkap'
                else: # tipe_kurator == 'mitra'
                    kurasi.catatan_mitra = catatan_kurator
                    kurasi.nilai_akhir_mitra = round(total_weighted_score, 2)
                    kurasi.tanggal_selesai_mitra = timezone.now()
                    if previous_status == 'Penilaian Berlangsung': kurasi.status = 'Penilaian Mitra Selesai'
                    elif previous_status == 'Penilaian Dosen Selesai': kurasi.status = 'Penilaian Lengkap'
                
                if kurasi.status == 'Penilaian Lengkap':
                     if kurasi.nilai_akhir_dosen is not None and kurasi.nilai_akhir_mitra is not None:
                         kurasi.nilai_akhir_final = round((kurasi.nilai_akhir_dosen + kurasi.nilai_akhir_mitra) / 2.0, 2)
                     project.curation_status = 'assessment-complete'
                     project.save(update_fields=['curation_status', 'updated_at'])
                
                kurasi.save()
                messages.success(request, f"Penilaian untuk proyek '{project.title}' berhasil disimpan.")
                
                if tipe_kurator == 'dosen': return redirect('kurasi_produk_list') 
                else: return redirect('mitra_kurasi_produk_list') # <-- 5. PERBAIKI REDIRECT INI
    else:
        form = AssessmentForm(initial=initial_form_data)
    
    context = {
        'kurasi': kurasi, 
        'project': project, 
        'form': form, 
        'tipe_kurator': tipe_kurator,
        'is_completed': is_completed,
        'existing_request': existing_request # <-- 6. TAMBAHKAN KE CONTEXT
    }
    return render(request, 'assess_project.html', context)

# --- VIEW MONITORING PENILAIAN (DAFTAR) ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def monitoring_penilaian_list_view(request):
    assessment_statuses_in_progress = ['Penilaian Berlangsung', 'Penilaian Dosen Selesai', 'Penilaian Mitra Selesai']
    projects_in_assessment_qs = Kurasi.objects.filter(
        status__in=assessment_statuses_in_progress,
        id_produk__curation_status='curators-assigned'
    ).select_related(
        'id_produk', 'id_produk__id_pemilik', 'id_kurator_dosen', 'id_kurator_mitra'
    ).order_by('tanggal_penugasan')
    projects_in_assessment_list = []
    for kurasi in projects_in_assessment_qs:
        progress = 0
        if kurasi.tanggal_selesai_dosen: progress += 50
        if kurasi.tanggal_selesai_mitra: progress += 50
        kurasi.progress_percentage = progress
        projects_in_assessment_list.append(kurasi)
    total_in_assessment = len(projects_in_assessment_list)
    assessment_complete_count = Kurasi.objects.filter(status='Penilaian Lengkap', id_produk__curation_status='assessment-complete').count()
    assessment_ongoing_count = total_in_assessment
    context = {
        'projects_in_assessment': projects_in_assessment_list,
        'total_in_assessment': total_in_assessment,
        'assessment_complete_count': assessment_complete_count,
        'assessment_ongoing_count': assessment_ongoing_count,
    }
    return render(request, 'monitoring_penilaian.html', context)


# --- VIEW DETAIL MONITORING (JSON untuk Modal) ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def get_monitoring_details_json(request, kurasi_id):
    try:
        kurasi = Kurasi.objects.select_related(
            'id_produk', 'id_produk__id_pemilik', 'id_kurator_dosen', 'id_kurator_mitra'
        ).get(id=kurasi_id)
        project = kurasi.id_produk
    except Kurasi.DoesNotExist:
        return JsonResponse({'error': 'Data Kurasi tidak ditemukan'}, status=404)
    dosen_name = "N/A"
    if kurasi.id_kurator_dosen:
        dosen_name = kurasi.id_kurator_dosen.get_full_name() or kurasi.id_kurator_dosen.username
    mitra_name = "N/A"
    if kurasi.id_kurator_mitra:
         mitra_name = kurasi.id_kurator_mitra.get_full_name() or kurasi.id_kurator_mitra.username
    data = {
        'kurasi': {
            'id': kurasi.id, 'tanggal_penugasan': kurasi.tanggal_penugasan,
            'tanggal_selesai_dosen': kurasi.tanggal_selesai_dosen, 'tanggal_selesai_mitra': kurasi.tanggal_selesai_mitra,
            'status': kurasi.status, 'kurator_dosen_name': dosen_name, 'kurator_mitra_name': mitra_name,
        },
        'project': {
            'title': project.title, 'owner': project.id_pemilik.username,
            'category': project.kategori.first().nama if project.kategori.exists() else "N/A",
        },
    }
    return JsonResponse(data)
# --- AKHIR MONITORING ---


# --- VIEWS REVIEW & KEPUTUSAN ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def review_decision_list_view(request):
    projects_to_review = Kurasi.objects.filter(
        status='Penilaian Lengkap', id_produk__curation_status='assessment-complete'
    ).select_related(
        'id_produk', 'id_produk__id_pemilik'
    ).order_by('id_produk__updated_at')
    decision_form = DecisionForm()
    context = {
        'projects_to_review': projects_to_review,
        'decision_form': decision_form,
    }
    return render(request, 'review_decision_list.html', context)

@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def get_review_details_json(request, kurasi_id):
    try:
        kurasi = Kurasi.objects.select_related(
            'id_produk', 'id_produk__id_pemilik', 'id_kurator_dosen', 'id_kurator_mitra'
        ).get(id=kurasi_id)
        project = kurasi.id_produk
    except Kurasi.DoesNotExist:
        return JsonResponse({'error': 'Data Kurasi tidak ditemukan'}, status=404)
    if kurasi.status != 'Penilaian Lengkap' or project.curation_status != 'assessment-complete':
         return JsonResponse({'error': 'Penilaian belum lengkap atau status proyek tidak sesuai untuk review.'}, status=400)
    aspek_penilaian = AspekPenilaian.objects.filter(id_kurasi=kurasi)
    aspek_details = {}
    for aspek_nama in AssessmentForm.ASPEK_CHOICES.keys():
        aspek_details[aspek_nama] = {'dosen': None, 'mitra': None}
    for ap in aspek_penilaian:
        if ap.aspek in aspek_details:
             if ap.tipe_kurator in aspek_details[ap.aspek]:
                 aspek_details[ap.aspek][ap.tipe_kurator] = ap.skor
    suggested_decision_text = "N/A"
    suggested_decision_value = ""
    nilai = kurasi.nilai_akhir_final
    if nilai is not None:
        if nilai >= 3.5:
            suggested_decision_text = "Sangat Layak"
            suggested_decision_value = "ready-for-publication"
        elif nilai >= 2.75:
            suggested_decision_text = "Revisi Minor"
            suggested_decision_value = "revision-minor"
        elif nilai >= 2.0:
            suggested_decision_text = "Perlu Pembinaan"
            suggested_decision_value = "needs-coaching"
        else:
            suggested_decision_text = "Tidak Layak"
            suggested_decision_value = "rejected"
    data = {
        'kurasi': {
            'id': kurasi.id, 'nilai_akhir_dosen': kurasi.nilai_akhir_dosen, 'nilai_akhir_mitra': kurasi.nilai_akhir_mitra,
            'nilai_akhir_final': kurasi.nilai_akhir_final, 'catatan_dosen': kurasi.catatan_dosen or "",
            'catatan_mitra': kurasi.catatan_mitra or "",
        },
        'project': { 'title': project.title, },
        'aspek_details': aspek_details,
        'suggested_decision': suggested_decision_text,
        'suggested_decision_value': suggested_decision_value,
        'decision_choices': [{'value': val, 'label': label} for val, label in DecisionForm.DECISION_CHOICES if val]
    }
    return JsonResponse(data)

@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='review_decision_list')
def handle_project_decision(request, kurasi_id):
    kurasi = get_object_or_404(Kurasi.objects.select_related('id_produk'), id=kurasi_id)
    project = kurasi.id_produk
    if kurasi.status != 'Penilaian Lengkap' or project.curation_status != 'assessment-complete':
         messages.warning(request, "Status proyek atau penilaian tidak sesuai untuk membuat keputusan.")
         return redirect('review_decision_list')
    form = DecisionForm(request.POST)
    if form.is_valid():
        selected_status = form.cleaned_data['decision']
        catatan_unit_bisnis = form.cleaned_data['catatan_unit_bisnis']
        project.curation_status = selected_status
        decision_label = dict(DecisionForm.DECISION_CHOICES).get(selected_status, selected_status.replace('-', ' ').title())
        project.final_decision = decision_label
        if selected_status in ['ready-for-publication', 'revision-minor']:
             project.dipublikasikan = False
        else:
             project.dipublikasikan = False
        project.save(update_fields=['curation_status', 'final_decision', 'dipublikasikan', 'updated_at'])
        # Simpan catatan unit bisnis jika fieldnya ada
        # if hasattr(kurasi, 'catatan_unit_bisnis'):
        #     kurasi.catatan_unit_bisnis = catatan_unit_bisnis
        #     kurasi.save(update_fields=['catatan_unit_bisnis'])
        messages.success(request, f"Keputusan '{decision_label}' berhasil disimpan untuk proyek '{project.title}'.")
        return redirect('review_decision_list')
    else:
        error_msg = "Gagal menyimpan keputusan. "
        first_field_errors = next(iter(form.errors.values()), ["Periksa kembali pilihan Anda."])
        error_msg += first_field_errors[0]
        messages.error(request, error_msg)
        return redirect('review_decision_list')
# --- AKHIR REVIEW & KEPUTUSAN ---


# --- VIEWS PUBLIKASI KATALOG ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def publish_catalog_list_view(request):
    projects_ready = Produk.objects.filter(
        Q(curation_status='ready-for-publication') | Q(curation_status='revision-minor'),
        dipublikasikan=False
    ).select_related('id_pemilik', 'kurasi').prefetch_related('kategori').order_by('-updated_at')
    projects_published = Produk.objects.filter(dipublikasikan=True).select_related('id_pemilik', 'kurasi').order_by('-updated_at')
    confirmation_form = PublishConfirmationForm()
    context = {
        'projects_ready_to_publish': projects_ready,
        'projects_published': projects_published,
        'confirmation_form': confirmation_form,
    }
    return render(request, 'publish_catalog_list.html', context)

@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='publish_catalog_list')
def handle_publish_project(request, project_id):
    project = get_object_or_404(Produk,
        id=project_id,
        curation_status__in=['ready-for-publication', 'revision-minor'],
        dipublikasikan=False
    )
    form = PublishConfirmationForm(request.POST)
    if form.is_valid():
        project.dipublikasikan = True
        project.curation_status = 'published'
        project.save(update_fields=['dipublikasikan', 'curation_status', 'updated_at'])
        messages.success(request, f"Proyek '{project.title}' berhasil dipublikasikan ke katalog.")
        return redirect('publish_catalog_list')
    else:
        messages.error(request, "Anda harus mencentang kotak konfirmasi untuk mempublikasikan.")
        return redirect('publish_catalog_list')
# --- AKHIR PUBLIKASI ---


# --- VIEWS MANAJEMEN USER (DIPERBAIKI) ---
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog') 
def manage_users_view(request):
    # Basis query: semua user yang relevan (bukan superuser atau unit bisnis)
    base_query = CustomUser.objects.exclude(is_superuser=True).exclude(peran='unit_bisnis')

    # Ambil list lengkap untuk tab 'All Users'
    all_users_list = base_query.order_by('username')

    # Ambil list pending untuk tab 'Account Requests'
    users_pending_list = base_query.filter(is_approved=False).order_by('date_joined')

    # --- Hitung Statistik ---
    total_users_count = all_users_list.count()
    active_users_count = all_users_list.filter(is_active=True, status='aktif', is_approved=True).count()
    pending_approval_count = users_pending_list.count() # Hitung dari query pending
    mahasiswa_count = all_users_list.filter(peran='mahasiswa').count()
    dosen_count = all_users_list.filter(peran='dosen').count()
    mitra_count = all_users_list.filter(peran='mitra').count()

    # Tentukan tab aktif dari parameter URL (default ke 'pending' jika ada yg pending)
    default_tab = 'pending' if pending_approval_count > 0 else 'all'
    current_tab = request.GET.get('tab', default_tab) 

    # === PERBAIKAN DI SINI ===
    # Tentukan list mana yang akan ditampilkan berdasarkan tab
    # Variabel 'users_list' ini yang dibaca oleh template
    if current_tab == 'pending':
        users_list_to_display = users_pending_list
    else:
        users_list_to_display = all_users_list
    # === AKHIR PERBAIKAN ===

    context = {
        # Kirim list yang benar ke template
        'users_list': users_list_to_display, 
        
        # Data untuk Tab (untuk hitungan di badge)
        'all_users_list': all_users_list, 
        'pending_approval_count': pending_approval_count, # Kirim count pending

        # Stats Cards
        'total_users_count': total_users_count,
        'active_users_count': active_users_count,
        
        # Stats Cards (Row 2 - Distribusi)
        'mahasiswa_count': mahasiswa_count,
        'dosen_count': dosen_count,
        'mitra_count': mitra_count,

        # Tab control
        'current_tab': current_tab,
    }
    return render(request, 'dashboard/manage_users.html', context)

@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='catalog')
def approve_user_view(request, user_id):
    user_to_approve = get_object_or_404(CustomUser, id=user_id, is_superuser=False, peran__in=['mahasiswa', 'dosen', 'mitra'])
    if not user_to_approve.is_approved:
        user_to_approve.is_approved = True
        user_to_approve.status = 'aktif'
        user_to_approve.save()
        messages.success(request, f"Akun '{user_to_approve.username}' ({user_to_approve.get_peran_display()}) telah disetujui dan diaktifkan.")
    else:
        messages.info(request, f"Akun '{user_to_approve.username}' sudah disetujui sebelumnya.")
    
    # === PERBAIKAN REDIRECT ===
    # Arahkan kembali ke tab pending agar daftarnya refresh
    return redirect(reverse('manage_users') + '?tab=pending')

@login_required
@require_POST
@user_passes_test(is_unit_bisnis, login_url='catalog')
def toggle_active_user_view(request, user_id):
    user_to_toggle = get_object_or_404(CustomUser, id=user_id, is_superuser=False, peran__in=['mahasiswa', 'dosen', 'mitra'])
    
    # === PERBAIKAN REDIRECT ===
    # Ambil tab saat ini dari POST data atau default ke 'all'
    current_tab = request.POST.get('current_tab', 'all')
    redirect_url = reverse('manage_users') + f'?tab={current_tab}'

    if user_to_toggle.status == 'aktif':
        user_to_toggle.status = 'nonaktif'
        user_to_toggle.save(update_fields=['status'])
        messages.warning(request, f"Akun '{user_to_toggle.username}' telah dinonaktifkan.")
    elif user_to_toggle.status == 'nonaktif':
        if user_to_toggle.is_approved:
            user_to_toggle.status = 'aktif'
            user_to_toggle.save(update_fields=['status'])
            messages.success(request, f"Akun '{user_to_toggle.username}' telah diaktifkan kembali.")
        else:
            messages.error(request, f"Akun '{user_to_toggle.username}' belum disetujui. Silakan setujui terlebih dahulu sebelum mengaktifkan.")
    
    # Arahkan kembali ke tab tempat user melakukan aksi
    return redirect(redirect_url)
@login_required
@user_passes_test(is_unit_bisnis, login_url='catalog')
def manage_products_view(request):
    """
    Halaman untuk Unit Bisnis melihat, mencari, dan menghapus
    semua produk dalam sistem.
    """
    # Ambil semua produk, urutkan dari yang terbaru
    all_products_list = Produk.objects.all().order_by('-created_at').select_related('id_pemilik').prefetch_related('kategori')
    
    # Ambil Statistik (Sama seperti di manage_users)
    total_produk_count = all_products_list.count()
    published_count = all_products_list.filter(dipublikasikan=True).count()
    pending_count = all_products_list.filter(curation_status='pending').count()
    in_curation_count = all_products_list.filter(curation_status__in=[
        'selected', 'curators-assigned', 'assessment-complete', 
        'ready-for-publication', 'revision-minor'
    ]).count()

    context = {
        # Lists untuk Tabel
        'all_products_list': all_products_list,

        # Stats Cards
        'total_produk_count': total_produk_count,
        'published_count': published_count,
        'pending_count': pending_count,
        'in_curation_count': in_curation_count,
        
        # Tab control (default ke 'all')
        'current_tab': 'all', 
    }
    # Kita akan buat template baru ini di Langkah 3
    return render(request, 'dashboard/manage_products.html', context)


@login_required
@require_POST # Hanya izinkan metode POST untuk keamanan
@user_passes_test(is_unit_bisnis, login_url='catalog')
def delete_product_view(request, project_id):
    """
    View untuk menghapus produk. Hanya bisa diakses oleh Unit Bisnis via POST.
    """
    # Cari produk atau kembalikan 404
    product_to_delete = get_object_or_404(Produk, id=project_id)
    
    try:
        product_name = product_to_delete.title
        product_to_delete.delete()
        messages.success(request, f"Produk '{product_name}' telah berhasil dihapus secara permanen.")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus produk: {e}")

    # Kembali ke halaman manajemen produk
    return redirect('manage_products')

@login_required
@require_POST # Hanya izinkan metode POST untuk keamanan
def delete_own_project_view(request, project_id):
    """
    Menangani permintaan penghapusan proyek oleh pemiliknya.
    """
    # Ambil proyek, pastikan itu ada
    product = get_object_or_404(Produk, id=project_id)
    
    # Tentukan halaman redirect berdasarkan peran user
    if request.user.peran == 'dosen':
        redirect_url = 'dosen_my_projects'
    else:
        redirect_url = 'my_projects' # Default untuk mahasiswa

    # 1. Cek Kepemilikan: Apakah user ini pemilik proyek?
    if product.id_pemilik != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus proyek ini.")
        return redirect(redirect_url)

    # 2. Cek Status: Apakah proyek masih 'pending'?
    if product.curation_status != 'pending':
        messages.error(request, f"Proyek '{product.title}' tidak dapat dihapus karena sudah masuk dalam proses kurasi.")
        return redirect(redirect_url)

    # Jika semua pengecekan lolos, hapus produk
    try:
        product_title = product.title
        product.delete()
        messages.success(request, f"Proyek '{product_title}' telah berhasil dihapus.")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus proyek: {e}")
    
    return redirect(redirect_url)
