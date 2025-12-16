from django import forms
from django.forms import modelformset_factory
from django.forms.models import BaseModelFormSet # Diperlukan untuk formset berbasis model wajib
from .models import Produk, Kategori, DokumenProyek
from users.models import CustomUser 

# --- ProdukForm ---
class ProdukForm(forms.ModelForm):
    # Field non-model: program_studi (WAJIB diisi)
    program_studi = forms.ChoiceField(
        choices=[('', 'Pilih Program Studi')] + list(CustomUser.PROGRAM_STUDI_CHOICES),
        label='Program Studi',
        required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'})
    )
    
    # Field non-model: tags_input (WAJIB diisi)
    tags_input = forms.CharField(
        label='Tags',
        required=True, # Tags wajib
        help_text='Pisahkan dengan koma (,) cth: AI, Web Dev, UI/UX',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Tags (cth: Web Dev, Mobile App)'})
    )

    class Meta:
        model = Produk
        # poster_image, title, description, links WAJIB diisi (diasumsikan blank=False di model)
        fields = ['title', 'description', 'poster_image', 'source_code_link', 'demo_link', 'kategori']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Judul Proyek Anda'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Deskripsi lengkap proyek'}),
            'source_code_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Link ke GitHub atau repository lainnya'}),
            'demo_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Link ke demo aplikasi (live preview)'}),
            # poster_image WAJIB diisi (karena required=True default jika model blank=False)
            'poster_image': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'}),
            # Kategori Many-to-Many diatur di bawah
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

    # Validasi Kategori: Minimal satu harus dipilih
    def clean_kategori(self):
        kategori = self.cleaned_data.get('kategori')
        if not kategori or not kategori.exists():
            raise forms.ValidationError("Anda wajib memilih minimal satu Kategori.")
        return kategori
        
    def save(self, commit=True, owner=None):
        from .models import Tag
        
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
            
            # Simpan Tags 
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                instance.tags.clear()
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(nama=tag_name)
                    instance.tags.add(tag)

        return instance


# --- DokumenProyek Form ---
class DokumenProyekForm(forms.ModelForm):
    file_dokumen = forms.FileField(
        label='Pilih File (Opsional)',
        required=False, 
        widget=forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100'})
    )
    keterangan = forms.CharField(
        label='Keterangan File / Link',
        required=False, 
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Contoh: Rancangan ERD atau Link Google Drive'})
    )
    tipe_dokumen = forms.ChoiceField(
        choices=DokumenProyek.TIPE_CHOICES,
        label='Jenis Dokumen',
        required=True, # WAJIB DIISI
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'})
    )
    
    class Meta:
        model = DokumenProyek
        fields = ['tipe_dokumen', 'file_dokumen', 'keterangan'] 
        widgets = {} 
        labels = {}
        
    def clean(self):
        cleaned_data = super().clean()
        file_dokumen = cleaned_data.get('file_dokumen')
        keterangan = cleaned_data.get('keterangan')
        tipe_dokumen = cleaned_data.get('tipe_dokumen') 
        is_deleted = cleaned_data.get('DELETE')
        
        # Validasi Form Individual: Wajib File ATAU Keterangan jika Tipe Dokumen dipilih
        if tipe_dokumen and not is_deleted:
            if not file_dokumen and not keterangan:
                self.add_error('keterangan', "Wajib diisi: Berikan keterangan/link ATAU unggah file.")
                
        return cleaned_data
        
# --- Base Formset Kustom untuk Validasi Minimal 1 Dokumen ---
class RequiredDokumenFormSet(BaseModelFormSet): # Menerima 'queryset' argument
    """Memastikan minimal satu form dokumen yang valid diisi."""
    def clean(self):
        super().clean()
        
        total_valid_entries = 0
        
        for form in self.forms:
            # Hanya cek form yang diubah atau diisi
            if form.has_changed() or (form.cleaned_data and not form.cleaned_data.get('DELETE', False)):
                 
                 tipe = form.cleaned_data.get('tipe_dokumen')
                 file = form.cleaned_data.get('file_dokumen')
                 ket = form.cleaned_data.get('keterangan')
                 
                 # Pastikan form lolos validasi individual (tipe ada, dan file/ket ada)
                 if tipe and (file or ket):
                     total_valid_entries += 1
                     
        # Jika tidak ada form yang valid yang diisi, raise ValidationError
        if total_valid_entries < 1:
            raise forms.ValidationError(
                "Anda wajib mengunggah minimal satu Dokumen Pendukung (File atau Link) yang lengkap."
            )

# --- DokumenProyek Formset Factory ---
DokumenProyekFormSet = modelformset_factory(
    DokumenProyek, 
    form=DokumenProyekForm,
    formset=RequiredDokumenFormSet, 
    fields=('tipe_dokumen', 'file_dokumen', 'keterangan'),
    extra=1, 
    max_num=5, 
    can_delete=True,
)