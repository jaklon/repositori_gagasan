# repository/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
# --- Models ---
from .models import Produk, Kategori, Kurasi, Tag, AspekPenilaian
from users.models import CustomUser # Import CustomUser
# --- Utils ---
from django.db.models import Q, Count, Case, When, IntegerField
from django.contrib.auth.decorators import login_required
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone
import datetime
from django.http import JsonResponse
# --- Tambahkan Template Tag Loader ---
from django.template.defaulttags import register


# === TEMPLATE TAGS ===
# Filter sederhana untuk mengakses item dictionary di template
# Pindahkan ini ke repository/templatetags/repository_extras.py
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
# === AKHIR TEMPLATE TAGS ===


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
        required=False, # Sesuai model (blank=True)
        label="Kategori Proyek (Pilih satu atau lebih)",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'category-checkbox-list'})
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
            'demo_link', 'program_studi', 'kategori', 'tags_input',
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
        self.fields['poster_image'].required = True
        self.fields['demo_link'].required = True
        self.fields['program_studi'].required = True

        if self.instance and self.instance.pk:
            self.initial['tags_input'] = ', '.join(t.nama for t in self.instance.tags.all())

    def clean_poster_image(self):
        image = self.cleaned_data.get('poster_image', False)
        if image:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Ukuran gambar tidak boleh melebihi 5MB.")
        elif not self.instance or not self.instance.pk:
             if not image:
                 raise ValidationError("Gambar overview proyek wajib diisi.")
        return image

    def clean_source_code_link(self):
        link = self.cleaned_data.get('source_code_link')
        if link:
            if not ('github.com' in link or 'drive.google.com' in link):
                raise ValidationError("Link harus berasal dari github.com atau drive.google.com.")
        return link

    def clean_tags_input(self):
        tags_string = self.cleaned_data.get('tags_input', '')
        tag_names = [name.strip().lower() for name in tags_string.split(',') if name.strip()]
        tags_list = []
        if tag_names:
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(nama=name)
                tags_list.append(tag)
        return tags_list

    def save(self, commit=True, owner=None):
        instance = super().save(commit=False)
        if owner:
            instance.id_pemilik = owner
        instance.curation_status = 'pending'
        # Simpan field non-model jika perlu
        # instance.program_studi = self.cleaned_data.get('program_studi')
        # instance.source_code_link = self.cleaned_data.get('source_code_link')
        if commit:
            instance.save()
            self.save_m2m() # Simpan kategori (ManyToMany)
            tags_list = self.cleaned_data.get('tags_input')
            if tags_list is not None:
                instance.tags.set(tags_list)
        return instance
# --- AKHIR FORM UNGGAH ---


# --- FORM PENUGASAN KURATOR ---
class AssignCuratorForm(forms.Form):
    kurator_dosen = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(peran='dosen', is_active=True),
        required=True, label="Kurator Dosen", empty_label="Pilih Dosen",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
    kurator_mitra = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(peran='mitra', is_active=True),
        required=True, label="Kurator Mitra Industri", empty_label="Pilih Mitra",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
# --- AKHIR FORM PENUGASAN ---


# --- FORM PENILAIAN ASPEK ---
class AssessmentForm(forms.Form):
    ASPEK_CHOICES = {
        'Orisinalitas & Inovasi': 15, 'Fungsionalitas Produk': 20,
        'Desain UI/UX & Aksesibilitas': 15, 'Teknologi & Kesesuaian Tren': 15,
        'Kelayakan Bisnis & Potensi Pasar': 20, 'Dokumentasi Teknis & Panduan Pengguna': 15,
    }
    # Ambil choices skor dari model AspekPenilaian
    SCORE_CHOICES = [('', 'Pilih Skor')] + list(AspekPenilaian._meta.get_field('skor').choices)

    def __init__(self, *args, **kwargs):
        initial_scores = kwargs.pop('initial_scores', {})
        super().__init__(*args, **kwargs)
        for aspek_nama in self.ASPEK_CHOICES.keys():
            field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
            self.fields[field_name] = forms.ChoiceField(
                label=aspek_nama, choices=self.SCORE_CHOICES,
                widget=forms.RadioSelect(attrs={'class': 'assessment-radio'}),
                required=True, initial=initial_scores.get(aspek_nama)
            )
    catatan = forms.CharField(label="Catatan Keseluruhan (Opsional)", required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'})
    )
# --- AKHIR FORM PENILAIAN ---


# --- FORM KEPUTUSAN UNIT BISNIS ---
class DecisionForm(forms.Form):
    DECISION_CHOICES = [
        ('', 'Pilih keputusan final...'),
        ('Sangat Layak', '🟢 Layak - Siap Publikasi (Nilai >= 3.50)'),
        ('Revisi Minor', '🔵 Revisi Minor - Publikasi Setelah Perbaikan (2.75 - 3.49)'),
        ('Perlu Pembinaan', '🟡 Perlu Pembinaan - Tidak Dipublikasi (2.00 - 2.74)'),
        ('Tidak Layak', '🔴 Tidak Layak - Ditolak (Nilai < 2.00)'),
    ]
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        required=True,
        label="Tetapkan Keputusan",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white appearance-none', 'id':'id_decision_modal', 'x-ref':'decisionSelect'})
    )
    catatan_unit_bisnis = forms.CharField(
        label="Catatan Tambahan Unit Bisnis (Opsional)",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent', 'id':'id_catatan_unit_bisnis_modal'})
    )

    def __init__(self, *args, **kwargs):
        self.kurasi_instance = kwargs.pop('kurasi_instance', None)
        super().__init__(*args, **kwargs)

    def clean_decision(self):
        decision = self.cleaned_data.get("decision")
        nilai = self.kurasi_instance.nilai_akhir_final if self.kurasi_instance else None
        if nilai is not None and decision:
            can_decide = False
            if decision == 'Sangat Layak' and nilai >= 3.5: can_decide = True
            elif decision == 'Revisi Minor' and 2.75 <= nilai < 3.5: can_decide = True
            elif decision == 'Perlu Pembinaan' and 2.0 <= nilai < 2.75: can_decide = True
            elif decision == 'Tidak Layak' and nilai < 2.0: can_decide = True
            if not can_decide:
                 raise ValidationError(f"Keputusan '{decision}' tidak valid untuk Nilai Akhir Final ({nilai:.2f}).")
        elif not decision:
             raise ValidationError("Keputusan harus dipilih.")
        elif nilai is None and decision:
             raise ValidationError("Nilai Akhir Final belum dihitung, keputusan belum bisa dibuat.")
        return decision
# --- AKHIR FORM KEPUTUSAN ---


# --- FORM KONFIRMASI PUBLIKASI ---
class PublishConfirmationForm(forms.Form):
    confirm_publish = forms.BooleanField(
        required=True,
        label="",
        error_messages={'required': 'Anda harus menyetujui konfirmasi ini.'},
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 cursor-pointer', 'id': 'id_confirm_publish'})
    )
# --- AKHIR FORM KONFIRMASI ---


# === VIEWS ===

# --- CATALOG VIEW (INI YANG PENTING ADA) ---
def catalog_view(request):
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    projects = Produk.objects.filter(dipublikasikan=True).order_by('-created_at')
    if query:
        projects = projects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__nama__icontains=query)
        ).distinct()
    if category_slug:
        projects = projects.filter(kategori__slug=category_slug)
    categories = Kategori.objects.all()
    context = {'projects': projects, 'categories': categories, 'selected_category': category_slug}
    return render(request, 'catalog.html', context)
# --- AKHIR CATALOG VIEW ---


# --- DASHBOARD VIEWS ---
@login_required
def dashboard_mahasiswa(request):
    my_projects = Produk.objects.filter(id_pemilik=request.user).order_by('-created_at')
    context = {'my_projects': my_projects}
    return render(request, 'dashboard/mahasiswa.html', context)

@login_required
def dashboard_dosen(request):
    # Ambil queryset dasar untuk semua tugas yang ditugaskan ke dosen ini
    tugas_penilaian_qs = Kurasi.objects.filter(
        id_kurator_dosen=request.user
    ).exclude(
        status='Menunggu Penugasan' # Kecualikan yang belum ditugaskan
    ).select_related('id_produk', 'id_produk__id_pemilik') # Optimasi query

    # Hitung Statistik
    total_tugas = tugas_penilaian_qs.count()
    
    # Pisahkan daftar berdasarkan status tanggal selesai
    belum_dinilai_list = tugas_penilaian_qs.filter(
        tanggal_selesai_dosen__isnull=True
    ).order_by('tanggal_penugasan') # Tampilkan yang terlama (mendekati deadline) dulu
    
    sudah_selesai_list = tugas_penilaian_qs.filter(
        tanggal_selesai_dosen__isnull=False
    ).order_by('-tanggal_selesai_dosen') # Tampilkan yang terbaru selesai
    
    # Hitung count
    belum_dinilai_count = belum_dinilai_list.count()
    sudah_selesai_count = sudah_selesai_list.count()

    context = {
        'total_tugas': total_tugas,
        'belum_dinilai_count': belum_dinilai_count,
        'sudah_selesai_count': sudah_selesai_count,
        'belum_dinilai_list': belum_dinilai_list, # Kirim daftar yang belum dinilai
        'sudah_selesai_list': sudah_selesai_list, # Kirim daftar yang sudah selesai
    }
    return render(request, 'dashboard/dosen.html', context)

# --- DASHBOARD STATS BARU UNTUK DOSEN ---
@login_required
def dashboard_dosen_main(request):
    # Pastikan hanya dosen
    if request.user.peran != 'dosen':
        # TODO: Arahkan ke dashboard yang sesuai
        return redirect('catalog')
    
    # Query untuk statistik (contoh, perlu disesuaikan dengan model Anda)
    # 1. Supervised: (Perlu relasi Dosen-Mahasiswa, saat ini tidak ada di model)
    supervised_count = 0 
    # 2. My Projects: Proyek yang diupload oleh dosen
    my_projects_count = Produk.objects.filter(id_pemilik=request.user).count()
    # 3. Curated: Tugas kurasi yang sudah selesai
    curated_count = Kurasi.objects.filter(id_kurator_dosen=request.user, status='Penilaian Lengkap').count()
    # 4. Pending Tasks: Tugas kurasi yang belum selesai
    pending_tasks_count = Kurasi.objects.filter(id_kurator_dosen=request.user, status__in=['Penilaian Berlangsung', 'Penilaian Mitra Selesai']).count()
    
    # Query untuk daftar proyek (contoh)
    recently_supervised_projects = [] # (Perlu relasi Dosen-Mahasiswa)

    context = {
        'supervised_count': supervised_count,
        'my_projects_count': my_projects_count,
        'curated_count': curated_count,
        'pending_tasks_count': pending_tasks_count,
        'recently_supervised_projects': recently_supervised_projects,
    }
    return render(request, 'dashboard/dosen_main.html', context)

# --- VIEW TUGAS PENILAIAN DOSEN (Nama view lama) ---
@login_required
def dashboard_dosen(request):
# ... (existing code) ...
    # Ambil semua tugas penilaian (termasuk yang selesai)
    tugas_penilaian = Kurasi.objects.filter(id_kurator_dosen=request.user).exclude(status='Menunggu Penugasan').order_by('status', 'tanggal_penugasan')

    # Hitung statistik untuk halaman ini
    belum_dinilai_list = tugas_penilaian.exclude(tanggal_selesai_dosen__isnull=False)
    sudah_selesai_list = tugas_penilaian.filter(tanggal_selesai_dosen__isnull=False)

    belum_dinilai_count = belum_dinilai_list.count()
    sudah_selesai_count = sudah_selesai_list.count()
    total_tugas = belum_dinilai_count + sudah_selesai_count

    context = {
        'total_tugas': total_tugas,
        'belum_dinilai_count': belum_dinilai_count,
        'sudah_selesai_count': sudah_selesai_count,
        'belum_dinilai_list': belum_dinilai_list,
        'sudah_selesai_list': sudah_selesai_list,
    }
    return render(request, 'dashboard/dosen.html', context)

# --- DASHBOARD STATS BARU UNTUK MITRA ---
@login_required
def dashboard_mitra_main(request):
    # Pastikan hanya mitra
    if request.user.peran != 'mitra':
        return redirect('catalog')

    # Query untuk statistik (contoh)
    # 1. Mahasiswa: (Perlu relasi Mitra-Mahasiswa, tidak ada)
    mahasiswa_count = 12 # Hardcoded sesuai desain
    # 2. Proyek Mahasiswa: (Tugas kurasi total?)
    proyek_mahasiswa_count = Kurasi.objects.filter(id_kurator_mitra=request.user).count()
    # 3. Curated: Tugas kurasi yang sudah selesai
    curated_count = Kurasi.objects.filter(id_kurator_mitra=request.user, status='Penilaian Lengkap').count()
    # 4. Not Curated: Tugas kurasi yang belum selesai
    not_curated_count = Kurasi.objects.filter(id_kurator_mitra=request.user).exclude(status='Penilaian Lengkap').count()

    # Query daftar proyek (semua proyek terbaru, bukan hanya milik mitra)
    proyek_mahasiswa_terbaru = Produk.objects.filter(
        curation_status='pending' # Tampilkan proyek yang baru diupload
    ).order_by('-created_at')[:5] # Ambil 5 terbaru

    context = {
        'mahasiswa_count': mahasiswa_count,
        'proyek_mahasiswa_count': proyek_mahasiswa_count,
        'curated_count': curated_count,
        'not_curated_count': not_curated_count,
        'proyek_mahasiswa_terbaru': proyek_mahasiswa_terbaru,
    }
    return render(request, 'dashboard/mitra_main.html', context)

# --- VIEW TUGAS PENILAIAN MITRA (Nama view lama) ---
@login_required
def dashboard_mitra(request):
# ... (existing code) ...
    # Ambil semua tugas penilaian (termasuk yang selesai)
    tugas_penilaian = Kurasi.objects.filter(id_kurator_mitra=request.user).exclude(status='Menunggu Penugasan').order_by('status', 'tanggal_penugasan')
    
    # Hitung statistik (mirip dosen)
    belum_dinilai_list = tugas_penilaian.exclude(tanggal_selesai_mitra__isnull=False)
    sudah_selesai_list = tugas_penilaian.filter(tanggal_selesai_mitra__isnull=False)

    belum_dinilai_count = belum_dinilai_list.count()
    sudah_selesai_count = sudah_selesai_list.count()
    total_tugas = belum_dinilai_count + sudah_selesai_count

    context = {
        'total_tugas': total_tugas,
        'belum_dinilai_count': belum_dinilai_count,
        'sudah_selesai_count': sudah_selesai_count,
        'belum_dinilai_list': belum_dinilai_list,
        'sudah_selesai_list': sudah_selesai_list,
    }
    # TODO: Buat template 'dashboard/mitra_tugas.html' yang mirip 'dosen.html'
    # Untuk sementara, kita bisa render template dosen jika tampilannya sama
    return render(request, 'dashboard/mitra.html', context) # Asumsi 'mitra.html' adalah halaman tugas


@login_required
def dashboard_mitra(request):
    tugas_penilaian = Kurasi.objects.filter(id_kurator_mitra=request.user).exclude(status='Menunggu Penugasan').order_by('status', 'tanggal_penugasan')
    context = {'tugas_penilaian': tugas_penilaian}
    return render(request, 'dashboard/mitra.html', context)

@login_required
def dashboard_unit_bisnis(request):
    context = {
        'total_proyek': Produk.objects.count(),
        'proyek_terkurasi': Produk.objects.filter(dipublikasikan=True).count(),
        'proyek_menunggu': Produk.objects.filter(curation_status='pending').count(),
    }
    return render(request, 'dashboard/unit_bisnis.html', context)
# --- AKHIR DASHBOARD VIEWS ---


# --- REPOSITORY VIEWS ---
@login_required
def repository_view(request):
    current_tab = request.GET.get('tab', 'pending')
    
    # Tab "Terpilih untuk Kurasi" (hanya 'selected')
    projects_selected = Produk.objects.filter(curation_status='selected').order_by('-created_at')

    # Tab "Repository" (semua status lain kecuali 'published' dan 'selected')
    projects_all_other = Produk.objects.exclude(
        curation_status__in=['selected', 'published']
    ).select_related('id_pemilik').order_by('-created_at')

    # Hitung statistik
    total_proyek_repo_count = projects_all_other.count()
    total_proyek_selected_count = projects_selected.count()
    total_proyek = total_proyek_repo_count + total_proyek_selected_count # Total di repository (non-published)

    if current_tab == 'selected':
        projects_to_show = projects_selected
    else:
        projects_to_show = projects_all_other
        current_tab = 'pending'

    context = {
        'projects_all_other': projects_all_other, # Untuk data tab
        'projects_selected': projects_selected, # Untuk data tab
        'total_proyek_repo_count': total_proyek_repo_count,
        'total_proyek_selected_count': total_proyek_selected_count,
        'total_proyek': total_proyek,
        'current_tab': current_tab,
        'projects_to_show': projects_to_show,
    }
    return render(request, 'repository.html', context)

@login_required
@require_POST
def select_for_curation(request, project_id):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin untuk melakukan aksi ini.")
        return redirect('repository')
    project = get_object_or_404(Produk, id=project_id)
    if project.curation_status == 'pending':
        project.curation_status = 'selected'
        project.save()
        messages.success(request, f"Proyek '{project.title}' telah berhasil dipilih untuk kurasi.")
    else:
        messages.warning(request, f"Proyek '{project.title}' statusnya bukan 'pending'.")
    return redirect(f"{request.META.get('HTTP_REFERER', '/repository/')}?tab=pending")
# --- AKHIR REPOSITORY VIEWS ---


# --- UPLOAD PROJECT VIEW ---
@login_required
def upload_project_view(request):
    if request.user.peran not in ['mahasiswa', 'dosen']:
         messages.error(request, "Hanya Mahasiswa dan Dosen yang dapat mengunggah proyek.")
         if request.user.peran == 'mitra': return redirect('dashboard_mitra')
         if request.user.peran == 'unit_bisnis': return redirect('dashboard_unit_bisnis')
         return redirect('catalog')
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=True, owner=request.user)
            messages.success(request, f"Proyek '{project.title}' berhasil diunggah!")
            if request.user.peran == 'mahasiswa': return redirect('dashboard_mahasiswa')
            elif request.user.peran == 'dosen': return redirect('dashboard_dosen')
        # else: form invalid, biarkan view merender ulang form dengan errors
    else:
        form = ProjectForm()
    context = {'form': form}
    return render(request, 'upload_project.html', context)
# --- AKHIR UPLOAD PROJECT VIEW ---


# --- CURATION ASSIGNMENT VIEWS ---
@login_required
def assign_curator_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')
    projects_selected = Produk.objects.filter(curation_status='selected').order_by('updated_at')
    assign_form = AssignCuratorForm()
    context = {'projects_selected': projects_selected, 'assign_form': assign_form}
    return render(request, 'assign_curator.html', context)

@login_required
@require_POST
def handle_assign_curator(request, project_id):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin untuk melakukan aksi ini.")
        return redirect('assign_curator_list')
    project = get_object_or_404(Produk, id=project_id, curation_status='selected')
    form = AssignCuratorForm(request.POST)
    if form.is_valid():
        kurator_dosen = form.cleaned_data['kurator_dosen']
        kurator_mitra = form.cleaned_data['kurator_mitra']
        kurasi, created = Kurasi.objects.update_or_create(
            id_produk=project,
            defaults={
                'id_kurator_dosen': kurator_dosen, 'id_kurator_mitra': kurator_mitra,
                'tanggal_penugasan': timezone.now(), 'status': 'Penilaian Berlangsung'
            }
        )
        AspekPenilaian.objects.filter(id_kurasi=kurasi).delete()
        aspek_list = AssessmentForm.ASPEK_CHOICES.keys()
        aspek_records = []
        for aspek_nama in aspek_list:
            aspek_records.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='dosen', skor=None))
            aspek_records.append(AspekPenilaian(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator='mitra', skor=None))
        AspekPenilaian.objects.bulk_create(aspek_records)
        project.curation_status = 'curators-assigned'
        project.save()
        messages.success(request, f"Kurator berhasil ditugaskan untuk proyek '{project.title}'.")
        return redirect('assign_curator_list')
    else:
        error_message = "Gagal menugaskan kurator."
        if form.errors:
             first_field = next(iter(form.errors))
             error_message += f" Error pada '{form[first_field].label}': {form[first_field].errors[0]}"
        else:
             error_message += " Pastikan kedua kurator dipilih."
        messages.error(request, error_message)
        return redirect('assign_curator_list')
# --- AKHIR CURATION ASSIGNMENT VIEWS ---


# --- ASSESSMENT VIEW ---
@login_required
def assess_project_view(request, kurasi_id):
    kurasi = get_object_or_404(Kurasi, id=kurasi_id)
    project = kurasi.id_produk
    user = request.user
    tipe_kurator = None
    existing_note = None
    if user.peran == 'dosen' and kurasi.id_kurator_dosen == user:
        tipe_kurator = 'dosen'
        existing_note = kurasi.catatan_dosen
    elif user.peran == 'mitra' and kurasi.id_kurator_mitra == user:
        tipe_kurator = 'mitra'
        existing_note = kurasi.catatan_mitra
    if not tipe_kurator:
        messages.error(request, "Anda tidak ditugaskan untuk menilai proyek ini atau peran Anda tidak sesuai.")
        return redirect('catalog')

    existing_scores = AspekPenilaian.objects.filter(id_kurasi=kurasi, tipe_kurator=tipe_kurator)
    initial_scores_dict = {score.aspek: score.skor for score in existing_scores if score.skor is not None}
    initial_form_data = {'catatan': existing_note}
    for aspek_nama, skor in initial_scores_dict.items():
        # Pastikan nama field konsisten
        field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
        initial_form_data[field_name] = skor

    if request.method == 'POST':
        form = AssessmentForm(request.POST, initial=initial_form_data)
        if form.is_valid():
            total_weighted_score = 0
            aspek_to_update = []
            all_fields_valid = True
            for aspek_nama, bobot in AssessmentForm.ASPEK_CHOICES.items():
                field_name = f"aspek_{aspek_nama.lower().replace('& ', '').replace(' ', '_').replace('/', '_')}"
                skor_str = form.cleaned_data.get(field_name)
                if not skor_str:
                     all_fields_valid = False
                     form.add_error(field_name, "Skor harus dipilih.")
                     continue
                skor = int(skor_str)
                try:
                    aspek_obj = AspekPenilaian.objects.get(id_kurasi=kurasi, aspek=aspek_nama, tipe_kurator=tipe_kurator)
                    aspek_obj.skor = skor
                    aspek_to_update.append(aspek_obj)
                except AspekPenilaian.DoesNotExist:
                     messages.error(request, f"Terjadi kesalahan: data aspek '{aspek_nama}' tidak ditemukan.")
                     return redirect('assess_project', kurasi_id=kurasi.id)
                total_weighted_score += skor * (bobot / 100.0)

            if not all_fields_valid:
                 messages.error(request, "Terdapat kesalahan pada form. Pastikan semua aspek terisi skor (1-4).")
            else:
                if aspek_to_update:
                    AspekPenilaian.objects.bulk_update(aspek_to_update, ['skor'])
                catatan_kurator = form.cleaned_data['catatan']
                previous_status = kurasi.status
                if tipe_kurator == 'dosen':
                    kurasi.catatan_dosen = catatan_kurator
                    kurasi.nilai_akhir_dosen = round(total_weighted_score, 2)
                    kurasi.tanggal_selesai_dosen = timezone.now()
                    if previous_status == 'Penilaian Berlangsung': kurasi.status = 'Penilaian Dosen Selesai'
                    elif previous_status == 'Penilaian Mitra Selesai': kurasi.status = 'Penilaian Lengkap'
                else: # mitra
                    kurasi.catatan_mitra = catatan_kurator
                    kurasi.nilai_akhir_mitra = round(total_weighted_score, 2)
                    kurasi.tanggal_selesai_mitra = timezone.now()
                    if previous_status == 'Penilaian Berlangsung': kurasi.status = 'Penilaian Mitra Selesai'
                    elif previous_status == 'Penilaian Dosen Selesai': kurasi.status = 'Penilaian Lengkap'

                if kurasi.status == 'Penilaian Lengkap':
                     if kurasi.nilai_akhir_dosen is not None and kurasi.nilai_akhir_mitra is not None:
                         # Hitung nilai akhir final berdasarkan rata-rata
                         kurasi.nilai_akhir_final = round((kurasi.nilai_akhir_dosen + kurasi.nilai_akhir_mitra) / 2.0, 2)
                     project.curation_status = 'assessment-complete'
                     project.save()
                kurasi.save()
                messages.success(request, f"Penilaian untuk proyek '{project.title}' berhasil disimpan.")
                if tipe_kurator == 'dosen': return redirect('dashboard_dosen')
                else: return redirect('dashboard_mitra')
        # else: form invalid, biarkan view merender ulang form dengan errors
    else: # GET request
        form = AssessmentForm(initial=initial_form_data)

    context = {'kurasi': kurasi, 'project': project, 'form': form, 'tipe_kurator': tipe_kurator}
    return render(request, 'assess_project.html', context)
# --- AKHIR ASSESSMENT VIEW ---


# --- REVIEW & DECISION VIEWS ---
@login_required
def review_decision_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')
    projects_to_review = Kurasi.objects.filter(
        status='Penilaian Lengkap',
        id_produk__curation_status='assessment-complete'
    ).select_related('id_produk', 'id_produk__id_pemilik').order_by('id_produk__updated_at')
    decision_form = DecisionForm()
    context = {'projects_to_review': projects_to_review, 'decision_form': decision_form}
    return render(request, 'review_decision_list.html', context)

@login_required
def get_review_details_json(request, kurasi_id):
    if request.user.peran != 'unit_bisnis':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    try:
        kurasi = Kurasi.objects.select_related('id_produk', 'id_produk__id_pemilik').get(id=kurasi_id)
        project = kurasi.id_produk
    except Kurasi.DoesNotExist:
        return JsonResponse({'error': 'Kurasi not found'}, status=404)
    if kurasi.status != 'Penilaian Lengkap' or project.curation_status != 'assessment-complete':
         return JsonResponse({'error': 'Penilaian belum lengkap atau status proyek tidak sesuai'}, status=400)
    aspek_penilaian = AspekPenilaian.objects.filter(id_kurasi=kurasi)
    aspek_details = {}
    for aspek_nama in AssessmentForm.ASPEK_CHOICES.keys():
        aspek_details[aspek_nama] = {'dosen': None, 'mitra': None}
    for ap in aspek_penilaian:
        if ap.aspek in aspek_details:
             aspek_details[ap.aspek][ap.tipe_kurator] = ap.skor
    suggested_decision_value = ""
    suggested_decision_text = "Belum Dinilai"
    nilai = kurasi.nilai_akhir_final
    if nilai is not None:
        if nilai >= 3.5:
            suggested_decision_value = "Sangat Layak"
            suggested_decision_text = "Sangat Layak"
        elif nilai >= 2.75:
             suggested_decision_value = "Revisi Minor"
             suggested_decision_text = "Layak (Revisi Minor)"
        elif nilai >= 2.0:
             suggested_decision_value = "Perlu Pembinaan"
             suggested_decision_text = "Perlu Pembinaan"
        else:
             suggested_decision_value = "Tidak Layak"
             suggested_decision_text = "Tidak Layak"
    data = {
        'kurasi': {
            'id': kurasi.id, 'nilai_akhir_dosen': kurasi.nilai_akhir_dosen,
            'nilai_akhir_mitra': kurasi.nilai_akhir_mitra, 'nilai_akhir_final': kurasi.nilai_akhir_final,
            'catatan_dosen': kurasi.catatan_dosen or "", 'catatan_mitra': kurasi.catatan_mitra or "",
        },
        'project': {'title': project.title},
        'aspek_details': aspek_details,
        'suggested_decision': suggested_decision_text,
        'suggested_decision_value': suggested_decision_value,
    }
    return JsonResponse(data)

@login_required
@require_POST
def handle_project_decision(request, kurasi_id):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin untuk melakukan aksi ini.")
        return redirect('review_decision_list')
    kurasi = get_object_or_404(Kurasi, id=kurasi_id)
    project = kurasi.id_produk
    if kurasi.status != 'Penilaian Lengkap' or project.curation_status != 'assessment-complete':
         messages.warning(request, "Status proyek atau penilaian tidak sesuai untuk membuat keputusan.")
         return redirect('review_decision_list')
    form = DecisionForm(request.POST, kurasi_instance=kurasi)
    if form.is_valid():
        decision = form.cleaned_data['decision']
        catatan_unit_bisnis = form.cleaned_data['catatan_unit_bisnis']
        if decision == 'Sangat Layak':
            project.curation_status = 'ready-for-publication'
        elif decision == 'Revisi Minor':
            project.curation_status = 'revision-minor'
        elif decision == 'Perlu Pembinaan':
            project.curation_status = 'needs-coaching'
        elif decision == 'Tidak Layak':
            project.curation_status = 'rejected'
        project.final_decision = decision
        project.dipublikasikan = False
        project.save()
        # Simpan catatan unit bisnis (jika ada fieldnya di model Kurasi)
        # kurasi.catatan_unit_bisnis = catatan_unit_bisnis
        # kurasi.save()
        messages.success(request, f"Keputusan '{decision}' berhasil disimpan untuk proyek '{project.title}'.")
        return redirect('review_decision_list')
    else:
        error_msg = "Gagal menyimpan keputusan. "
        if 'decision' in form.errors:
            error_msg += form.errors['decision'][0]
        else:
            first_field_errors = next(iter(form.errors.values()), None)
            if first_field_errors:
                error_msg += first_field_errors[0]
            else:
                 error_msg += "Periksa kembali pilihan keputusan dan catatan Anda."
        messages.error(request, error_msg)
        return redirect('review_decision_list')
# --- AKHIR REVIEW & DECISION VIEWS ---


# --- PUBLISH CATALOG VIEWS ---
@login_required
def publish_catalog_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')
    projects_ready = Produk.objects.filter(
        Q(curation_status='ready-for-publication') | Q(curation_status='revision-minor')
    ).filter(dipublikasikan=False).select_related('id_pemilik', 'kurasi').order_by('-updated_at')
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
def handle_publish_project(request, project_id):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin untuk melakukan aksi ini.")
        return redirect('publish_catalog_list')
    project = get_object_or_404(Produk, id=project_id, dipublikasikan=False)
    if project.curation_status not in ['ready-for-publication', 'revision-minor']:
        messages.warning(request, f"Proyek '{project.title}' belum siap untuk dipublikasikan (status: {project.curation_status}).")
        return redirect('publish_catalog_list')
    form = PublishConfirmationForm(request.POST)
    if form.is_valid():
        project.dipublikasikan = True
        project.curation_status = 'published'
        project.save()
        messages.success(request, f"Proyek '{project.title}' berhasil dipublikasikan ke katalog.")
        return redirect('publish_catalog_list')
    else:
        error_msg = "Gagal mempublikasikan. "
        if 'confirm_publish' in form.errors:
             error_msg += form.errors['confirm_publish'][0]
        else:
             error_msg += "Terjadi kesalahan validasi."
        messages.error(request, error_msg)
        return redirect('publish_catalog_list')
# --- AKHIR PUBLISH CATALOG VIEWS ---


# --- MONITORING PENILAIAN VIEWS ---
@login_required
def monitoring_penilaian_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')
    assessment_statuses = [
        'Penilaian Berlangsung', 'Penilaian Dosen Selesai', 'Penilaian Mitra Selesai',
    ]
    projects_in_assessment_qs = Kurasi.objects.filter(
        status__in=assessment_statuses
    ).select_related(
        'id_produk', 'id_produk__id_pemilik',
        'id_kurator_dosen', 'id_kurator_mitra'
    ).order_by('tanggal_penugasan')
    projects_in_assessment_list = []
    for kurasi in projects_in_assessment_qs:
        progress = 0
        if kurasi.tanggal_selesai_dosen: progress += 50
        if kurasi.tanggal_selesai_mitra: progress += 50
        kurasi.progress_percentage = progress
        projects_in_assessment_list.append(kurasi)
    total_in_assessment = len(projects_in_assessment_list)
    assessment_complete_count = Kurasi.objects.filter(status='Penilaian Lengkap').count()
    assessment_ongoing_count = total_in_assessment
    context = {
        'projects_in_assessment': projects_in_assessment_list,
        'total_in_assessment': total_in_assessment,
        'assessment_complete_count': assessment_complete_count,
        'assessment_ongoing_count': assessment_ongoing_count,
    }
    return render(request, 'monitoring_penilaian.html', context)

@login_required
def get_monitoring_details_json(request, kurasi_id):
    if request.user.peran != 'unit_bisnis':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    try:
        kurasi = Kurasi.objects.select_related(
            'id_produk', 'id_produk__id_pemilik',
            'id_kurator_dosen', 'id_kurator_mitra'
        ).get(id=kurasi_id)
        project = kurasi.id_produk
    except Kurasi.DoesNotExist:
        return JsonResponse({'error': 'Kurasi not found'}, status=404)
    data = {
        'kurasi': {
            'id': kurasi.id, 'tanggal_penugasan': kurasi.tanggal_penugasan,
            'tanggal_selesai_dosen': kurasi.tanggal_selesai_dosen,
            'tanggal_selesai_mitra': kurasi.tanggal_selesai_mitra,
            'status': kurasi.status,
            'kurator_dosen_name': kurasi.id_kurator_dosen.get_full_name() if kurasi.id_kurator_dosen else "N/A",
            'kurator_mitra_name': kurasi.id_kurator_mitra.get_full_name() if kurasi.id_kurator_mitra else "N/A",
        },
        'project': {
            'title': project.title, 'owner': project.id_pemilik.username,
            'category': project.kategori.first().nama if project.kategori.exists() else "N/A",
        },
    }
    return JsonResponse(data)
# --- AKHIR MONITORING PENILAIAN VIEWS ---

