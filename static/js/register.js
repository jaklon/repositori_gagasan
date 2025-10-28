// Menjalankan skrip setelah semua konten halaman dimuat
document.addEventListener("DOMContentLoaded", function () {
  // --- 1. PENGATURAN FIELD DINAMIS BERDASARKAN PERAN ---

  const roleSelect = document.getElementById("role");
  const studentFields = document.getElementById("studentFields");
  const dosenFields = document.getElementById("dosenFields");
  const mitraFields = document.getElementById("mitraFields");

  // Fungsi untuk menyembunyikan semua field tambahan
  function hideAllRoleFields() {
    studentFields.classList.add("hidden");
    dosenFields.classList.add("hidden");
    mitraFields.classList.add("hidden");
  }

  // Tambahkan event listener pada dropdown peran
  roleSelect.addEventListener("change", function () {
    // Sembunyikan semua field terlebih dahulu
    hideAllRoleFields();

    // Tampilkan field yang sesuai berdasarkan nilai yang dipilih
    // Nilai ini (student, dosen, mitra) harus sesuai dengan <option value="..."> di HTML Anda
    if (this.value === "student") {
      studentFields.classList.remove("hidden");
    } else if (this.value === "dosen") {
      dosenFields.classList.remove("hidden");
    } else if (this.value === "mitra") {
      mitraFields.classList.remove("hidden");
    }
  });

  // --- 2. PENGATURAN TOGGLE PASSWORD ---

  // Fungsi generik untuk toggle password
  function setupPasswordToggle(
    toggleBtnId,
    passwordInputId,
    eyeIconId,
    eyeOffIconId
  ) {
    const toggleBtn = document.getElementById(toggleBtnId);
    const passwordInput = document.getElementById(passwordInputId);
    const eyeIcon = document.getElementById(eyeIconId);
    const eyeOffIcon = document.getElementById(eyeOffIconId);

    toggleBtn.addEventListener("click", function () {
      // Ubah tipe input
      if (passwordInput.type === "password") {
        passwordInput.type = "text";
        eyeIcon.classList.add("hidden");
        eyeOffIcon.classList.remove("hidden");
      } else {
        passwordInput.type = "password";
        eyeIcon.classList.remove("hidden");
        eyeOffIcon.classList.add("hidden");
      }
    });
  }

  // Terapkan fungsi untuk field "Password"
  setupPasswordToggle("togglePassword", "password", "eyeIcon1", "eyeOffIcon1");

  // Terapkan fungsi untuk field "Konfirmasi Password"
  setupPasswordToggle(
    "toggleConfirmPassword",
    "confirmPassword",
    "eyeIcon2",
    "eyeOffIcon2"
  );

  // --- 3. PENGATURAN SUBMIT FORM (VALIDASI & SPINNER) ---

  const registerForm = document.getElementById("registerForm");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const btnLoading = document.getElementById("btnLoading");
  const errorAlert = document.getElementById("errorAlert");
  const errorMessage = document.getElementById("errorMessage");

  registerForm.addEventListener("submit", function (e) {
    // Ambil nilai password
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    // Sembunyikan error alert jika ada
    errorAlert.classList.add("hidden");

    // Validasi: Cek apakah password cocok
    if (password !== confirmPassword) {
      // Hentikan form agar tidak terkirim
      e.preventDefault();

      // Tampilkan pesan error
      errorMessage.textContent =
        "Password dan Konfirmasi Password tidak cocok. Silakan periksa kembali.";
      errorAlert.classList.remove("hidden");

      return; // Hentikan eksekusi
    }

    // Jika validasi lolos, tampilkan spinner
    btnText.classList.add("hidden");
    btnLoading.classList.remove("hidden");
    // Nonaktifkan tombol agar tidak di-klik berkali-kali
    submitBtn.disabled = true;

    // Form akan melanjutkan proses submit ke backend Django...
  });
});
