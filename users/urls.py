# users/urls.py
from django.urls import path
# Import kedua view dari views.py
from .views import login_view, register_view

urlpatterns = [
    # Jika login adalah halaman utama Anda
    path('', login_view, name='login'), 
    
    # Jika login diakses lewat /login/
    # path('login/', login_view, name='login'), 

    # --- TAMBAHKAN URL BARU DI BAWAH INI ---
    path('register/', register_view, name='register'),
]