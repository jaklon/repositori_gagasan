from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
# Import fungsi-fungsi autentikasi
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    # Logika untuk memproses data login (method POST)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Email dan Password harus diisi!')
            return redirect('login')

        # 'authenticate' mengecek data ke database
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Jika user valid, loginkan ke sistem
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')
            
            # TODO: Nanti kita arahkan ke dashboard yang sesuai
            # Untuk tes, kita bisa arahkan ke halaman admin
            return redirect('admin:index') 
        else:
            # Jika user tidak valid
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
        # TODO: Kita perlu membuat file 'register.html'
        return render(request, 'register.html')