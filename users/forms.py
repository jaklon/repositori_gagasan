# users/forms.py

from django import forms
from .models import CustomUser

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Tentukan field mana saja yang boleh diedit oleh pengguna
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
