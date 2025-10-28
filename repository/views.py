# repository/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

# --- Models ---
# Pastikan semua model yang dibutuhkan diimpor
from .models import Produk, Kategori, Kurasi, Tag, AspekPenilaian
from users.models import CustomUser # Import CustomUser
# --- Utils ---
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone # Import timezone
# --- Tambahkan JsonResponse ---
from django.http import JsonResponse


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

# --- FORM BARU: KEPUTUSAN UNIT BISNIS ---
class DecisionForm(forms.Form):
    # Sesuaikan choices value & label agar lebih deskriptif dan cocok dengan model/logika
    DECISION_CHOICES = [
        ('', 'Pilih keputusan final...'), # Placeholder
        ('ready-for-publication', '🟢 Layak - Siap Publikasi'),
        ('revision-minor', '🔵 Revisi Minor - Publikasi Setelah Perbaikan'),
        ('needs-coaching', '🟡 Perlu Pembinaan - Tidak Dipublikasi'),
        ('rejected', '🔴 Tidak Layak - Ditolak'),
    ]
    # Beri ID unik untuk elemen form di modal
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        required=True,
        label="Tetapkan Keputusan",
        # Beri ID agar bisa diakses JS dan style Tailwind
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white appearance-none', 'id':'id_decision_modal', 'x-ref':'decisionSelect'})
    )
    catatan_unit_bisnis = forms.CharField(
        label="Catatan Tambahan Unit Bisnis (Opsional)",
        required=False,
        # Beri ID agar bisa diakses JS dan style Tailwind
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent', 'id':'id_catatan_unit_bisnis_modal'})
    )

    # Simpan instance kurasi untuk validasi nilai
    def __init__(self, *args, **kwargs):
        self.kurasi_instance = kwargs.pop('kurasi_instance', None)
        super().__init__(*args, **kwargs)
# --- AKHIR FORM KEPUTUSAN ---

# --- FORM BARU: KONFIRMASI PUBLIKASI ---
class PublishConfirmationForm(forms.Form):
    confirm_publish = forms.BooleanField(
        required=True,
        label="Saya konfirmasi untuk mempublikasikan produk ini.",
        # Beri ID agar bisa diakses JS dan style Tailwind
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500', 'id': 'id_confirm_publish'})
    )
# --- AKHIR FORM KONFIRMASI ---

# --- VIEW BARU: DAFTAR PUBLIKASI KATALOG ---
@login_required
def publish_catalog_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')

    # Ambil proyek yang siap dipublikasi (status 'ready-for-publication' atau 'revision-minor' yang sudah oke)
    # Untuk 'revision-minor', perlu logika tambahan jika revisi sudah diverifikasi
    projects_ready = Produk.objects.filter(
        Q(curation_status='ready-for-publication') | Q(curation_status='revision-minor') # Sesuaikan jika revisi perlu verifikasi
    ).filter(dipublikasikan=False).select_related('id_pemilik', 'kurasi').order_by('-updated_at')

    # Ambil proyek yang sudah dipublikasi
    projects_published = Produk.objects.filter(dipublikasikan=True).select_related('id_pemilik', 'kurasi').order_by('-updated_at')

    # Form kosong untuk modal konfirmasi
    confirmation_form = PublishConfirmationForm()

    context = {
        'projects_ready_to_publish': projects_ready,
        'projects_published': projects_published,
        'confirmation_form': confirmation_form, # Kirim form ke template
    }
    return render(request, 'publish_catalog_list.html', context)


# --- VIEW BARU: TANGANI AKSI PUBLIKASI (POST dari Modal) ---
@login_required
@require_POST
def handle_publish_project(request, project_id):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin untuk melakukan aksi ini.")
        return redirect('publish_catalog_list')

    # Ambil proyek yang siap dipublikasi
    project = get_object_or_404(Produk, id=project_id, dipublikasikan=False)
    # Pastikan statusnya memang siap publish
    if project.curation_status not in ['ready-for-publication', 'revision-minor']:
        messages.warning(request, f"Proyek '{project.title}' belum siap untuk dipublikasikan.")
        return redirect('publish_catalog_list')

    # Validasi form konfirmasi
    form = PublishConfirmationForm(request.POST)
    if form.is_valid():
        # Update status produk
        project.dipublikasikan = True
        project.curation_status = 'published' # Update status akhir
        project.save()

        messages.success(request, f"Proyek '{project.title}' berhasil dipublikasikan ke katalog.")
        return redirect('publish_catalog_list')
    else:
        # Jika checkbox tidak dicentang
        messages.error(request, "Anda harus mencentang kotak konfirmasi untuk mempublikasikan.")
        return redirect('publish_catalog_list')


# --- VIEW DAFTAR REVIEW & KEPUTUSAN (DIMODIFIKASI) ---
@login_required
def review_decision_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')

    projects_to_review = Kurasi.objects.filter(
        status='Penilaian Lengkap',
        id_produk__curation_status='assessment-complete'
    ).select_related('id_produk', 'id_produk__id_pemilik').order_by('id_produk__updated_at')

    # Buat instance form kosong untuk dikirim ke template (dibutuhkan untuk render field di modal & CSRF)
    decision_form = DecisionForm()

    context = {
        'projects_to_review': projects_to_review,
        'decision_form': decision_form, # Kirim form kosong
    }
    return render(request, 'review_decision_list.html', context)

# --- VIEW AMBIL DETAIL REVIEW JSON (Hapus suggested_decision_value) ---
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

    # Tentukan teks kategori otomatis
    suggested_decision_text = "Belum Dinilai"
    nilai = kurasi.nilai_akhir_final
    if nilai is not None:
        if nilai >= 3.5: suggested_decision_text = "Sangat Layak"
        elif nilai >= 2.75: suggested_decision_text = "Layak (Revisi Minor)"
        elif nilai >= 2.0: suggested_decision_text = "Perlu Pembinaan"
        else: suggested_decision_text = "Tidak Layak"

    data = {
        'kurasi': { 'id': kurasi.id, 'nilai_akhir_dosen': kurasi.nilai_akhir_dosen,
                    'nilai_akhir_mitra': kurasi.nilai_akhir_mitra, 'nilai_akhir_final': kurasi.nilai_akhir_final,
                    'catatan_dosen': kurasi.catatan_dosen or "", 'catatan_mitra': kurasi.catatan_mitra or "" },
        'project': { 'title': project.title },
        'aspek_details': aspek_details,
        'suggested_decision': suggested_decision_text, # Teks kategori otomatis
        # Hapus suggested_decision_value, tidak diperlukan lagi
        'decision_choices': [{'value': val, 'label': label} for val, label in DecisionForm.DECISION_CHOICES if val]
    }
    return JsonResponse(data)


# --- VIEW TANGANI SUBMIT KEPUTUSAN (DIMODIFIKASI) ---
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

    # Gunakan DecisionForm untuk validasi input POST (tanpa validasi nilai)
    form = DecisionForm(request.POST) # Tidak perlu kurasi_instance lagi

    if form.is_valid():
        # --- PERUBAHAN LOGIKA ---
        # Ambil status kurasi yang dipilih dari form
        selected_status = form.cleaned_data['decision']
        catatan_unit_bisnis = form.cleaned_data['catatan_unit_bisnis']

        # Update status Produk LANGSUNG berdasarkan pilihan
        project.curation_status = selected_status

        # Update final_decision (teks) berdasarkan pilihan status
        # Cari label yang cocok dari choices form
        decision_label = dict(DecisionForm.DECISION_CHOICES).get(selected_status, selected_status) # Fallback ke value jika label tidak ketemu
        project.final_decision = decision_label # Simpan teks keputusan

        # Atur status publikasi berdasarkan keputusan
        if selected_status in ['ready-for-publication', 'revision-minor']:
             project.dipublikasikan = False # Masih false, akan diubah di tahap publikasi
        else:
             project.dipublikasikan = False # Pastikan false untuk status lain

        project.save()

        # Simpan catatan unit bisnis (jika ada fieldnya di model Kurasi)
        # kurasi.catatan_unit_bisnis = catatan_unit_bisnis
        # kurasi.save()
        # --- AKHIR PERUBAHAN LOGIKA ---

        messages.success(request, f"Keputusan '{decision_label}' berhasil disimpan untuk proyek '{project.title}'.")
        return redirect('review_decision_list')

    else: # Form tidak valid (misal, decision kosong)
        error_msg = "Gagal menyimpan keputusan. "
        first_field_errors = next(iter(form.errors.values()), None)
        if first_field_errors:
            error_msg += first_field_errors[0]
        else:
             error_msg += "Periksa kembali pilihan keputusan Anda."
        messages.error(request, error_msg)
        return redirect('review_decision_list')


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
    tugas_penilaian = Kurasi.objects.filter(id_kurator_dosen=request.user).exclude(status='Menunggu Penugasan').order_by('status', 'tanggal_penugasan')
    context = {'tugas_penilaian': tugas_penilaian}
    return render(request, 'dashboard/dosen.html', context)

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
    projects_pending = Produk.objects.filter(curation_status='pending').order_by('-created_at')
    projects_selected = Produk.objects.filter(curation_status='selected').order_by('-created_at')
    total_proyek = Produk.objects.count()
    projects_to_show = projects_selected if current_tab == 'selected' else projects_pending
    current_tab = 'selected' if current_tab == 'selected' else 'pending'
    context = {
        'projects_pending': projects_pending, 'projects_selected': projects_selected,
        'total_proyek': total_proyek, 'current_tab': current_tab,
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
         # Redirect logic...
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
        # Redirect logic...
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
        # Tampilkan error form yang lebih detail
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
        # Redirect logic...
        return redirect('catalog')

    existing_scores = AspekPenilaian.objects.filter(id_kurasi=kurasi, tipe_kurator=tipe_kurator)
    initial_scores_dict = {score.aspek: score.skor for score in existing_scores if score.skor is not None}
    initial_form_data = {'catatan': existing_note}
    for aspek_nama, skor in initial_scores_dict.items():
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

# --- VIEW MONITORING PENILAIAN (DAFTAR - DIMODIFIKASI) ---
@login_required
def monitoring_penilaian_list_view(request):
    if request.user.peran != 'unit_bisnis':
        messages.error(request, "Anda tidak memiliki izin mengakses halaman ini.")
        return redirect('catalog')

    assessment_statuses = [
        'Penilaian Berlangsung',
        'Penilaian Dosen Selesai',
        'Penilaian Mitra Selesai',
    ]
    projects_in_assessment_qs = Kurasi.objects.filter(
        status__in=assessment_statuses
    ).select_related(
        'id_produk', 'id_produk__id_pemilik',
        'id_kurator_dosen', 'id_kurator_mitra'
    ).order_by('tanggal_penugasan')

    # --- HITUNG PROGRESS DI SINI ---
    projects_in_assessment_list = []
    for kurasi in projects_in_assessment_qs:
        progress = 0
        if kurasi.tanggal_selesai_dosen:
            progress += 50
        if kurasi.tanggal_selesai_mitra:
            progress += 50
        kurasi.progress_percentage = progress # Tambahkan atribut baru
        projects_in_assessment_list.append(kurasi)
    # --- AKHIR HITUNG PROGRESS ---

    # Hitung statistik
    total_in_assessment = len(projects_in_assessment_list) # Gunakan list yg sudah dihitung
    assessment_complete_count = Kurasi.objects.filter(status='Penilaian Lengkap').count()
    # Sedang berlangsung = Total (gunakan len dari list)
    assessment_ongoing_count = total_in_assessment # Semua yg difilter dianggap ongoing

    context = {
        # Gunakan list yang sudah ada progress_percentage
        'projects_in_assessment': projects_in_assessment_list,
        'total_in_assessment': total_in_assessment,
        'assessment_complete_count': assessment_complete_count,
        'assessment_ongoing_count': assessment_ongoing_count,
    }
    return render(request, 'monitoring_penilaian.html', context)

# --- VIEW BARU: DETAIL MONITORING (JSON untuk Modal) ---
@login_required
def get_monitoring_details_json(request, kurasi_id):
    if request.user.peran != 'unit_bisnis':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        # Ambil data kurasi lengkap dengan relasi terkait
        kurasi = Kurasi.objects.select_related(
            'id_produk', 'id_produk__id_pemilik',
            'id_kurator_dosen', 'id_kurator_mitra'
        ).get(id=kurasi_id)
        project = kurasi.id_produk
    except Kurasi.DoesNotExist:
        return JsonResponse({'error': 'Kurasi not found'}, status=404)

    # Siapkan data JSON
    data = {
        'kurasi': {
            'id': kurasi.id,
            'tanggal_penugasan': kurasi.tanggal_penugasan,
            'tanggal_selesai_dosen': kurasi.tanggal_selesai_dosen,
            'tanggal_selesai_mitra': kurasi.tanggal_selesai_mitra,
            'status': kurasi.status,
            'kurator_dosen_name': kurasi.id_kurator_dosen.get_full_name() if kurasi.id_kurator_dosen else "N/A",
            'kurator_mitra_name': kurasi.id_kurator_mitra.get_full_name() if kurasi.id_kurator_mitra else "N/A",
        },
        'project': {
            'title': project.title,
            'owner': project.id_pemilik.username,
            'category': project.kategori.first().nama if project.kategori.exists() else "N/A", # Ambil kategori pertama
        },
        # Tambahkan field lain jika perlu
    }
    return JsonResponse(data)
