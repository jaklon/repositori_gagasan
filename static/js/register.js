// static/js/register.js
document.addEventListener("DOMContentLoaded", function () {
  
  // Ambil elemen-elemen yang diperlukan
  const roleSelect = document.getElementById("peran");
  const studentFields = document.getElementById("studentFields");
  const dosenFields = document.getElementById("dosenFields");
  const mitraFields = document.getElementById("mitraFields");
  
  // Masukkan semua field dinamis ke dalam array agar mudah dikelola
  const allRoleFields = [studentFields, dosenFields, mitraFields];

  /**
   * Mengatur properti 'required' pada semua input dan select di dalam container.
   * @param {HTMLElement} fieldContainer - Container field peran (studentFields, dll.).
   * @param {boolean} isRequired - True untuk required, false untuk tidak.
   */
  function setFieldsRequired(fieldContainer, isRequired) {
    if (!fieldContainer) return;
    
    // Nonaktifkan required pada semua input/select saat container disembunyikan
    fieldContainer.querySelectorAll('input:not([type="hidden"]), select').forEach(el => {
        el.required = false;
    });

    if (!isRequired) return;

    // Aktifkan required hanya untuk field yang wajib diisi berdasarkan peran
    const roleId = fieldContainer.id;

    if (roleId === 'studentFields') {
        fieldContainer.querySelectorAll('#nim, #program_studi').forEach(el => el.required = true);
    } else if (roleId === 'dosenFields') {
        // Field wajib untuk Dosen: ID Dosen & Bidang Keahlian
        fieldContainer.querySelectorAll('#id_dosen, #bidang_keahlian_dosen').forEach(el => el.required = true);
        // Field Jurusan & Program Studi Dosen tetap opsional (required=false)
    } else if (roleId === 'mitraFields') {
        // Field wajib untuk Mitra: ID Mitra, Organisasi & Bidang Keahlian
        fieldContainer.querySelectorAll('#id_mitra, #organisasi, #bidang_keahlian_mitra').forEach(el => el.required = true);
    }
  }


  function toggleRoleFields() {
    const selectedRole = roleSelect.value;

    // 1. Sembunyikan dan nonaktifkan required untuk semua field dinamis
    allRoleFields.forEach(field => {
      if (field) {
        field.classList.add("hidden");
        setFieldsRequired(field, false); 
      }
    });

    // 2. Tampilkan dan aktifkan required untuk field yang sesuai
    if (selectedRole === "mahasiswa") {
      if (studentFields) {
        studentFields.classList.remove("hidden");
        setFieldsRequired(studentFields, true);
      }
    } else if (selectedRole === "dosen") {
      if (dosenFields) {
        dosenFields.classList.remove("hidden");
        setFieldsRequired(dosenFields, true); 
      }
    } else if (selectedRole === "mitra") {
      if (mitraFields) {
        mitraFields.classList.remove("hidden");
        setFieldsRequired(mitraFields, true);
      }
    }
  }

  // Tambahkan event listener ke dropdown 'peran'
  if (roleSelect) {
    roleSelect.addEventListener("change", toggleRoleFields);
  }

  // Jalankan fungsi saat halaman pertama kali dimuat
  toggleRoleFields();
  
});