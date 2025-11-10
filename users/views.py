from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
# Import fungsi-fungsi autentikasi
from django.contrib.auth import authenticate, login, logout
# --- TAMBAHKAN IMPORT INI ---
from django.contrib.auth.decorators import login_required
# === TAMBAHKAN IMPORT FORM DI SINI ===
from .forms import UserProfileForm


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username') # Tetap 'username' sesuai name di HTML
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email dan Password harus diisi!')
            return redirect('login')

        # Cari user berdasarkan email (case-insensitive bisa lebih baik)
        try:
            user_obj = CustomUser.objects.get(email__iexact=email) # Gunakan __iexact
            username = user_obj.username
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')

        # Authenticate menggunakan username
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # === CEK is_active bawaan, is_approved, dan status ===
            if not user.is_active: # Cek field is_active bawaan (misal diban admin)
                 messages.error(request, 'Akun Anda dinonaktifkan oleh administrator.')
                 return redirect('login')
            elif not user.is_approved: # Cek approval Unit Bisnis
                 messages.error(request, 'Akun Anda belum disetujui oleh Unit Bisnis.')
                 return redirect('login')
            elif user.status == 'nonaktif': # Cek status internal
                 messages.error(request, 'Akun Anda saat ini tidak aktif. Hubungi Unit Bisnis.')
                 return redirect('login')
            # === AKHIR CEK ===

            # Jika semua cek lolos, baru login
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')

            # --- LOGIKA REDIRECT ---
            if user.peran == 'mahasiswa':
                return redirect('dashboard_mahasiswa')
            elif user.peran == 'dosen':
                return redirect('dashboard_dosen')
            elif user.peran == 'mitra':
                return redirect('dashboard_mitra')
            elif user.peran == 'unit_bisnis':
                return redirect('dashboard_unit_bisnis')
            elif user.is_superuser: # Cek superuser
                return redirect('admin:index') # Arahkan ke admin Django
            else:
                return redirect('catalog') # Fallback

        else:
            # Jika authenticate gagal (username/password salah ATAU user.is_active bawaan = False)
            messages.error(request, 'Email atau Password salah!')
            return redirect('login')

    # Jika method GET
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        # 1. Ambil data utama
        username = request.POST.get('username')
        email = request.POST.get('email')
        peran = request.POST.get('peran')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # 2. Validasi dasar
        if not all([username, email, peran, password, password2]):
             messages.error(request, 'Semua field wajib diisi!')
             return redirect('register') 

        if password != password2:
            messages.error(request, 'Password tidak cocok!')
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah terdaftar!')
            return redirect('register')

        # 3. Kumpulkan data tambahan berdasarkan peran
        try:
            user_data = {
                'username': username,
                'email': email,
                'password': password,
                'peran': peran
            }
            
            if peran == 'mahasiswa':
                user_data['nim'] = request.POST.get('nim')
                user_data['program_studi'] = request.POST.get('program_studi')
            elif peran == 'dosen':
                user_data['id_dosen'] = request.POST.get('id_dosen')
                user_data['bidang_keahlian'] = request.POST.get('bidang_keahlian') # Ambil dari field dosen
            elif peran == 'mitra':
                user_data['id_mitra'] = request.POST.get('id_mitra')
                user_data['organisasi'] = request.POST.get('organisasi')
                user_data['bidang_keahlian'] = request.POST.get('bidang_keahlian') # Ambil dari field mitra

            # 4. Buat user baru menggunakan create_user
            user = CustomUser.objects.create_user(**user_data)
            
            messages.success(request, 'Akun berhasil dibuat! Akun Anda perlu disetujui oleh Unit Bisnis sebelum bisa login.')
            return redirect('login')
            
        except Exception as e:
             # Tangkap error tak terduga (misal jika NIM/ID Dosen unique=True)
             messages.error(request, f'Terjadi kesalahan saat membuat akun: {e}')
             return redirect('register')

    # Jika method adalah GET
    else:
        return render(request, 'register.html')

# Fungsi Logout (Sudah benar)
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah berhasil logout.")
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    
    # Cek apakah kita dalam mode edit dari parameter URL
    edit_mode = request.GET.get('edit') == 'true'

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            # Redirect kembali ke mode 'view' (tanpa parameter edit)
            return redirect('profile') 
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa isian Anda.')
            edit_mode = True # Tetap di mode edit jika form error
    else:
        # Jika GET request, siapkan form dengan data yang ada
        form = UserProfileForm(instance=user)

    context = {
        'form': form,
        'user': user,
        'edit_mode': edit_mode  # Kirim status edit_mode ke template
    }
    return render(request, 'profile.html', context)