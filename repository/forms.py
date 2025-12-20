from django import forms
from django.forms import modelformset_factory
from django.forms.models import BaseModelFormSet # Diperlukan untuk Formset kustom model
from .models import Produk, Kategori, DokumenProyek
from users.models import CustomUser 
from .models import Tag 

# --- ProdukForm (SEMUA FIELD WAJIB DIISI) ---
class ProdukForm(forms.ModelForm):
    
    # Field Non-Model: Program Studi (Wajib)
    program_studi = forms.ChoiceField(
        choices=[('', 'Pilih Program Studi')] + list(CustomUser.PROGRAM_STUDI_CHOICES),
        label='Program Studi',
        required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'})
    )
    
    # Field Non-Model: Tags (Wajib)
    tags_input = forms.CharField(
        label='Tags',
        required=True, 
        help_text='Pisahkan dengan koma (,) cth: AI, Web Dev, UI/UX',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Tags (cth: Web Dev, Mobile App)'})
    )

    class Meta:
        model = Produk
        fields = ['title', 'description', 'poster_image', 'source_code_link', 'demo_link', 'kategori']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Judul Proyek Anda'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Deskripsi lengkap proyek'}),
            'source_code_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Link ke GitHub atau repository lainnya'}),
            'demo_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Link ke demo aplikasi (live preview)'}),
            'poster_image': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'}),
            'kategori': forms.SelectMultiple(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'}),
        }
        
        labels = {
            'title': 'Judul Proyek', 'description': 'Deskripsi Proyek',
            'poster_image': 'Gambar Poster/Preview', 'source_code_link': 'Link Source Code',
            'demo_link': 'Link Demo (Live Preview)', 'kategori': 'Kategori Proyek',
        }
        help_texts = {
            'poster_image': 'Unggah gambar utama proyek Anda.',
            'source_code_link': 'Link ke repository (GitHub, GitLab, dll.)',
            'demo_link': 'Link ke aplikasi yang sudah di-deploy.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Penegasan semua field model wajib diisi
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['poster_image'].required = True
        self.fields['kategori'].required = True
        self.fields['source_code_link'].required = True 
        self.fields['demo_link'].required = True        

    def save(self, commit=True, owner=None):
        tags_input = self.cleaned_data.pop('tags_input', '')
        program_studi_value = self.cleaned_data.pop('program_studi', None)
        
        instance = super().save(commit=False)
        if owner:
            instance.id_pemilik = owner
        
        if commit:
            instance.save()
            self.save_m2m() 
            
            if program_studi_value and instance.id_pemilik.peran == 'mahasiswa':
                instance.id_pemilik.program_studi = program_studi_value
                instance.id_pemilik.save()
            
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                instance.tags.clear()
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(nama=tag_name)
                    instance.tags.add(tag)

        return instance


# --- DokumenProyek Form (Validasi AND Logic) ---
class DokumenProyekForm(forms.ModelForm):
    
    class Meta:
        model = DokumenProyek
        fields = ['tipe_dokumen', 'file_dokumen', 'keterangan'] 
        
        widgets = {
            'tipe_dokumen': forms.Select(choices=DokumenProyek.TIPE_CHOICES, attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'}),
            'file_dokumen': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'}),
            'keterangan': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Contoh: Rancangan ERD atau Link Google Drive'}),
        }
        labels = {
            'tipe_dokumen': 'Jenis Dokumen',
            'file_dokumen': 'Pilih File',
            'keterangan': 'Keterangan File / Link',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Menetapkan semua field dokumen sebagai wajib (AND Logic)
        self.fields['file_dokumen'].required = True
        self.fields['keterangan'].required = True
        self.fields['tipe_dokumen'].required = True


    def clean(self):
        cleaned_data = super().clean()
        file_dokumen = cleaned_data.get('file_dokumen')
        keterangan = cleaned_data.get('keterangan')
        tipe_dokumen = cleaned_data.get('tipe_dokumen')
        
        if cleaned_data.get('DELETE'):
            return cleaned_data

        is_being_filled = tipe_dokumen or file_dokumen or keterangan

        if is_being_filled:
            # Periksa jika ada field yang kosong, dan tambahkan error secara spesifik.
            # (Validasi required=True di __init__ sudah membantu, tapi ini memastikan pesan spesifik)
            
            # Jika user mengisi salah satu field tapi yang lain kosong, validasi gagal.
            if not tipe_dokumen:
                self.add_error('tipe_dokumen', "Jenis Dokumen wajib diisi.")
            
            # KOREKSI: Pengecekan AND (Harus keduanya ada)
            if not file_dokumen:
                 self.add_error('file_dokumen', "File Dokumen wajib diunggah.")
            
            if not keterangan:
                 self.add_error('keterangan', "Keterangan/Link wajib diisi.")
            
        return cleaned_data

# --- DokumenProyek Base Formset (Validasi Minimal 1 Dokumen Lengkap) ---
class DokumenProyekBaseFormSet(BaseModelFormSet):
    
    def clean(self):
        super().clean()
        
        if self.has_changed() or self.initial:
            total_valid_forms = 0
            for form in self.forms:
                # Lewati form yang memiliki error, yang ditandai DELETE
                if form.errors:
                    continue
                if form.cleaned_data.get('DELETE'):
                    continue
                
                tipe = form.cleaned_data.get('tipe_dokumen')
                file = form.cleaned_data.get('file_dokumen')
                keterangan = form.cleaned_data.get('keterangan')
                
                # Hanya hitung sebagai form valid jika SEMUA field diisi (AND Logic)
                if tipe and file and keterangan:
                    total_valid_forms += 1
            
            if total_valid_forms < 1:
                raise forms.ValidationError("Anda wajib menyediakan minimal satu Dokumen Proyek yang lengkap (Jenis Dokumen, File, dan Keterangan harus diisi).")


# --- Formset Factory ---
DokumenProyekFormSet = modelformset_factory(
    DokumenProyek, 
    form=DokumenProyekForm,
    formset=DokumenProyekBaseFormSet,
    fields=('tipe_dokumen', 'file_dokumen', 'keterangan'),
    extra=0, 
    max_num=5, 
    can_delete=True,
    min_num=1,
    validate_min=True,
)