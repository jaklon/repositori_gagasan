# repository/views.py

from django.shortcuts import render
from .models import Produk
from django.db.models import Q 

def catalog_view(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    # --- PERBAIKAN UTAMA DI SINI ---
    # Mulai dengan HANYA produk yang sudah dipublikasikan
    projects = Produk.objects.filter(dipublikasikan=True).order_by('-created_at')

    if query:
        projects = projects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )

    if category:
        # TODO: Tambahkan filter kategori
        pass 

    context = {
        'projects': projects
    }
    
    return render(request, 'catalog.html', context)