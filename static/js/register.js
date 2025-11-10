// static/js/register.js
document.addEventListener("DOMContentLoaded", function () {
  
  // Ambil elemen-elemen yang diperlukan
  const roleSelect = document.getElementById("peran");
  const studentFields = document.getElementById("studentFields");
  const dosenFields = document.getElementById("dosenFields");
  const mitraFields = document.getElementById("mitraFields");
  
  // Masukkan semua field dinamis ke dalam array agar mudah dikelola
  const allRoleFields = [studentFields, dosenFields, mitraFields];

  function toggleRoleFields() {
    // Ambil nilai peran yang dipilih
    const selectedRole = roleSelect.value;

    // Sembunyikan semua field dinamis terlebih dahulu
    allRoleFields.forEach(field => {
      if (field) { // Pastikan elemennya ada
        field.classList.add("hidden");
        // Nonaktifkan 'required' pada input di dalamnya saat tersembunyi
        field.querySelectorAll('input').forEach(input => input.required = false);
      }
    });

    // Tampilkan field yang sesuai
    if (selectedRole === "mahasiswa") {
      if (studentFields) {
        studentFields.classList.remove("hidden");
        // Aktifkan 'required' jika perlu
        // studentFields.querySelectorAll('input').forEach(input => input.required = true); 
        // NOTE: Anda bisa aktifkan 'required' jika field ini wajib diisi
      }
    } else if (selectedRole === "dosen") {
      if (dosenFields) {
        dosenFields.classList.remove("hidden");
        // dosenFields.querySelectorAll('input').forEach(input => input.required = true);
      }
    } else if (selectedRole === "mitra") {
      if (mitraFields) {
        mitraFields.classList.remove("hidden");
        // mitraFields.querySelectorAll('input').forEach(input => input.required = true);
      }
    }
  }

  // Tambahkan event listener ke dropdown 'peran'
  if (roleSelect) {
    roleSelect.addEventListener("change", toggleRoleFields);
  }

  // Jalankan fungsi saat halaman pertama kali dimuat
  toggleRoleFields();
  
  // Hapus logika validasi password dan spinner dari sini
  // Biarkan Django (backend) yang menangani validasi password
  // Spinner bisa ditambahkan nanti jika diperlukan
});