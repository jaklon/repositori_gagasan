from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
# Import fungsi-fungsi autentikasi
from django.contrib.auth import authenticate, login, logout
# --- TAMBAHKAN IMPORT INI ---
from django.contrib.auth.decorators import login_required


def login_view(request):
    # Logika untuk memproses data login (method POST)
    if request.method == 'POST':
        # --- PERUBAHAN 1: Ambil 'email' dari form, bukan 'username' ---
        email = request.POST.get('username') # Biarkan 'username' karena <input> di login.html masih name="username"
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email dan Password harus diisi!')
            return redirect('login')

        # --- PERUBAHAN 2: Cari user berdasarkan email ---
        try:
            # Coba temukan user berdasarkan email
            user_obj = CustomUser.objects.get(email=email)
            # Dapatkan username dari user yang ditemukan
            username = user_obj.username
        except CustomUser.DoesNotExist:
            # Jika email tidak ditemukan, kirim pesan error
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')
        
        # --- PERUBAHAN 3: Authenticate menggunakan username yang sudah kita temukan ---
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Jika user valid, loginkan ke sistem
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')
            
            # --- LOGIKA REDIRECT (Sudah benar) ---
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
            # Jika user tidak valid (password salah)
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')
    
    # Jika method-nya GET, tampilkan halaman login
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        # 1. Ambil data dari form
        username = request.POST.get('username')
        email = request.POST.get('email')
        peran = request.POST.get('peran')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # 2. Lakukan Validasi
        if password != password2:
            messages.error(request, 'Password tidak cocok!')
            return redirect('register')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah terdaftar!')
            return redirect('register')

        # 3. Jika validasi lolos, buat user baru
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            peran=peran
        )
        
        messages.success(request, 'Akun berhasil dibuat! Silakan login.')
        return redirect('login') 

    # Jika method adalah GET, cukup tampilkan halaman registrasi
    else:
        return render(request, 'register.html')

# --- TAMBAHKAN FUNGSI LOGOUT BARU ---
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah berhasil logout.")
    return redirect('login')

