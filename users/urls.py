# users/urls.py
from django.urls import path
# Import view logout
from .views import login_view, register_view, logout_view

urlpatterns = [
    path('', login_view, name='login'), 
    path('register/', register_view, name='register'),
    # --- TAMBAHKAN URL LOGOUT ---
    path('logout/', logout_view, name='logout'),
]