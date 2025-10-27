# repository/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Arahkan URL kosong (halaman utama) ke catalog_view
    path('', views.catalog_view, name='catalog'),
]