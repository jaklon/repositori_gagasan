# repository/forms.py

from django import forms
from django.forms import modelformset_factory
from .models import Produk, Kategori, DokumenProyek
from users.models import CustomUser 

# --- ProdukForm ---
class ProdukForm(forms.ModelForm):
    # Asumsi field program_studi dan tags_input adalah non-model fields yang diperlukan di form
    program_studi = forms.ChoiceField(
        choices=[('', 'Pilih Program Studi')] + list(CustomUser.PROGRAM_STUDI_CHOICES),
        label='Program Studi',
        required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition appearance-none'})
    )
    
    tags_input = forms.CharField(
        label='Tags',
        required=False,
        help_text='Pisahkan dengan koma (,) cth: AI, Web Dev, UI/UX',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition', 'placeholder': 'Tags (cth: Web Dev, Mobile App)'})
    )

    class Meta:
        model = Produk
        fields = ['title', 'description', 'poster_image', 'source_code_link', 'demo_link', 'kategori']
        
        # Atribut CSS diterapkan ke widget, BUKAN field model
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
            
            # Update CustomUser dengan Program Studi (jika Mahasiswa)
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


# --- DokumenProyek Form dan Formset ---
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
            'file_dokumen': 'Pilih File (Opsional)',
            'keterangan': 'Keterangan File / Link',
        }
        
    def clean(self):
        cleaned_data = super().clean()
        file_dokumen = cleaned_data.get('file_dokumen')
        keterangan = cleaned_data.get('keterangan')
        
        is_empty = not file_dokumen and not keterangan
        if is_empty and not cleaned_data.get('DELETE') and self.has_changed():
            if any(self.cleaned_data.values()): 
                self.add_error(None, "Dokumen wajib diisi: Unggah file atau berikan keterangan/link.")
            
        return cleaned_data
        
# KOREKSI UTAMA DILAKUKAN DI BAWAH: Argumen 'prefix' dihapus dari factory.
DokumenProyekFormSet = modelformset_factory(
    DokumenProyek, 
    form=DokumenProyekForm,
    fields=('tipe_dokumen', 'file_dokumen', 'keterangan'),
    extra=1, 
    max_num=5, 
    can_delete=True,
    # Hapus: prefix='dokumen'
)