# users/forms.py (Pastikan file ini berisi kedua class form di bawah ini)

from django import forms
from .models import CustomUser

# --- Form untuk memperbarui profil ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']
        
        labels = {
            'first_name': 'Nama Depan',
            'last_name': 'Nama Belakang',
        }
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': 'Masukkan nama depan Anda'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': 'Masukkan nama belakang Anda'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# --- Form untuk pendaftaran akun baru ---
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Konfirmasi Password')

    class Meta:
        model = CustomUser
        # Sertakan semua field yang ada di CustomUser yang relevan untuk registrasi
        fields = [
            'username', 'email', 'peran', 'nim', 'program_studi', 
            'id_dosen', 'jurusan', 'id_mitra', 'organisasi', 
            'bidang_keahlian',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        optional_fields = [
            'nim', 'program_studi', 'id_dosen', 'jurusan', 
            'id_mitra', 'organisasi', 'bidang_keahlian'
        ]
        for field_name in optional_fields:
            self.fields[field_name].required = False
            
        default_attrs = {
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white transition'
        }
        self.fields['username'].widget.attrs.update({'placeholder': 'Nama lengkap Anda', **default_attrs})
        self.fields['email'].widget.attrs.update({'placeholder': 'nama@pnj.ac.id', **default_attrs})
        self.fields['peran'].widget.attrs.update({'class': default_attrs['class'] + ' appearance-none'})
        self.fields['nim'].widget.attrs.update({'placeholder': 'Nomor Induk Mahasiswa', **default_attrs})
        self.fields['id_dosen'].widget.attrs.update({'placeholder': 'e.g., DSN001', **default_attrs})
        self.fields['jurusan'].widget.attrs.update({'placeholder': 'e.g., Teknik Informatika dan Komputer', **default_attrs})
        self.fields['id_mitra'].widget.attrs.update({'placeholder': 'e.g., MTR001', **default_attrs})
        self.fields['organisasi'].widget.attrs.update({'placeholder': 'Nama Perusahaan/Organisasi', **default_attrs})
        self.fields['bidang_keahlian'].widget.attrs.update({'placeholder': 'e.g., Web Dev, AI, Data Science', **default_attrs})
        self.fields['program_studi'].widget.attrs.update({'class': default_attrs['class'] + ' appearance-none'})
        self.fields['program_studi'].empty_label = 'Pilih Program Studi' 
        self.fields['password'].widget.attrs.update({'placeholder': 'Buat password', **default_attrs})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Konfirmasi password', **default_attrs})
        self.fields['password'].required = True
        self.fields['password2'].required = True


    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Password tidak cocok.")
        return password2
        
    def clean(self):
        cleaned_data = super().clean()
        peran = cleaned_data.get('peran')

        if peran == 'mahasiswa':
            if not cleaned_data.get('nim'):
                self.add_error('nim', 'NIM wajib diisi untuk Mahasiswa.')
            # Jika Program Studi di CustomUser Anda adalah CharField, Anda mungkin perlu penyesuaian di sini.
            # Asumsi field program_studi menampung display value atau choice key.
            if not cleaned_data.get('program_studi'):
                self.add_error('program_studi', 'Program Studi wajib diisi untuk Mahasiswa.')
        elif peran == 'dosen':
            if not cleaned_data.get('id_dosen'):
                self.add_error('id_dosen', 'ID Dosen wajib diisi untuk Dosen Pembimbing.')
            if not cleaned_data.get('bidang_keahlian'):
                 self.add_error('bidang_keahlian', 'Bidang Keahlian wajib diisi untuk Dosen Pembimbing.')
        elif peran == 'mitra':
            if not cleaned_data.get('id_mitra'):
                self.add_error('id_mitra', 'ID Mitra wajib diisi untuk Mitra Industri.')
            if not cleaned_data.get('organisasi'):
                self.add_error('organisasi', 'Organisasi wajib diisi untuk Mitra Industri.')
            if not cleaned_data.get('bidang_keahlian'):
                self.add_error('bidang_keahlian', 'Bidang Keahlian wajib diisi untuk Mitra Industri.')

        return cleaned_data