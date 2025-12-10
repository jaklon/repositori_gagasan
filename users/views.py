# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q # Digunakan untuk filtering kurasi
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# KOREKSI IMPORT: Sekarang form ini ADA di users/forms.py
from .forms import UserRegistrationForm, UserUpdateForm 

# ASUMSI: Import model-model repository ada di sini (Perlu di setup jika belum)
try:
    from repository.models import Produk, RequestSourceCode, Kurasi
except ImportError:
    # Fallback jika model belum di-migrate, agar server tetap running
    class Produk: pass 
    class RequestSourceCode: pass
    class Kurasi: pass

# ASUMSI: Fungsi is_unit_bisnis tersedia
def is_unit_bisnis(user):
    return user.peran == 'unit_bisnis'


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username') 
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email dan Password harus diisi!')
            return redirect('login')

        try:
            user_obj = CustomUser.objects.get(email__iexact=email)
            username = user_obj.username
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                 messages.error(request, 'Akun Anda dinonaktifkan oleh administrator.')
                 return redirect('login')
            elif not user.is_approved:
                 messages.error(request, 'Akun Anda belum disetujui oleh Unit Bisnis.')
                 return redirect('login')
            elif user.status == 'nonaktif':
                 messages.error(request, 'Akun Anda saat ini tidak aktif. Hubungi Unit Bisnis.')
                 return redirect('login')

            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')

            if user.peran == 'mahasiswa':
                return redirect('dashboard_mahasiswa')
            elif user.peran == 'dosen':
                return redirect('dashboard_dosen')
            elif user.peran == 'mitra':
                return redirect('dashboard_mitra')
            elif user.peran == 'unit_bisnis':
                return redirect('dashboard_unit_bisnis')
            elif user.is_superuser:
                return redirect('admin:index')
            else:
                return redirect('catalog')

        else:
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')

    return render(request, 'login.html')


def register_view(request):
    # KOREKSI: Menggunakan UserRegistrationForm
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST) 

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data.get('password'))
            user.save()
            
            messages.success(request, 'Akun berhasil dibuat! Akun Anda perlu disetujui oleh Unit Bisnis sebelum bisa login.')
            return redirect('login')
            
        else:
            first_error = next(iter(form.errors.values()))[0] if form.errors else 'Terjadi kesalahan saat membuat akun.'
            messages.error(request, f'Pendaftaran gagal: {first_error}')
            return redirect('register')
    else:
        return render(request, 'register.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah berhasil logout.")
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    edit_mode = request.GET.get('edit') == 'true'
    
    # --- START: Ambil data terkait berdasarkan peran ---
    context_data = {}
    
    # 1. Proyek yang dimiliki (Mahasiswa & Dosen)
    # Cek apakah model Produk sudah memiliki relasi id_pemilik (menghindari error jika model belum di-migrate/import)
    if hasattr(Produk, 'id_pemilik') and user.peran in ['mahasiswa', 'dosen']:
        context_data['produk_list'] = Produk.objects.filter(id_pemilik=user).order_by('-created_at')
    
    # 2. Penugasan Kurasi (Dosen & Mitra)
    if hasattr(Kurasi, 'id_produk') and user.peran in ['dosen', 'mitra']:
        if user.peran == 'dosen':
            kurasi_filter = Q(id_kurator_dosen=user)
        else: # mitra
            kurasi_filter = Q(id_kurator_mitra=user)
            
        context_data['kurasi_list'] = Kurasi.objects.filter(kurasi_filter).select_related('id_produk').order_by('-tanggal_penugasan')
    
    # 3. Permintaan Akses Source Code yang diajukan (Dosen & Mitra)
    if hasattr(RequestSourceCode, 'id_pemohon') and user.peran in ['dosen', 'mitra']:
        context_data['request_list'] = RequestSourceCode.objects.filter(id_pemohon=user).select_related('id_produk').order_by('-tanggal_request')
    
    # --- END: Ambil data terkait berdasarkan peran ---
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('profile') 
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa isian Anda.')
            edit_mode = True
    else:
        form = UserUpdateForm(instance=user)

    context = {
        'form': form,
        'user': user,
        'edit_mode': edit_mode,
        **context_data
    }
    return render(request, 'profile.html', context)