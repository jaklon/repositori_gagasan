# users/urls.py
from django.urls import path
# Import view logout dan view profil yang BARU
from .views import login_view, register_view, logout_view, profile_view

urlpatterns = [
    path('', login_view, name='login'), 
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),    
    path('profile/', profile_view, name='profile'),
]