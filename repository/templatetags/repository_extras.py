from django import template
from datetime import datetime, timedelta, timezone

# 1. HANYA SATU baris 'register' ini yang diperlukan.
register = template.Library()

# ------------------------------------------------------------------
# Filter yang Anda buat (get_item) - Ini sudah benar
# ------------------------------------------------------------------
@register.filter(name='get_item')
def get_item(dictionary, key):
    """ Allows accessing dictionary keys with variables in templates """
    return dictionary.get(key)

# ------------------------------------------------------------------
# Filter add_days (Perbaikan: Menambahkan 'timedelta')
# ------------------------------------------------------------------
@register.filter
def add_days(value, days):
    """
    Menambahkan sejumlah hari ke sebuah tanggal (datetime object).
    """
    if not value:
        return None
    try:
        # 'value' diharapkan adalah objek datetime.date atau datetime.datetime
        # 2. PERBAIKAN: 'timedelta' sekarang sudah diimpor
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        # Jika 'value' bukan tanggal atau 'days' bukan angka
        return None

# ------------------------------------------------------------------
# Tag yang Hilang (Penyebab error 'parse_datetime' sebelumnya)
# ------------------------------------------------------------------
@register.simple_tag
def parse_datetime(datetime_str):
    """
    Mengubah string (seperti dari {% now "Y-m-d H:i:s" %})
    menjadi objek datetime.
    """
    if not datetime_str:
        return None
    try:
        # Coba parse format yang paling umum
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        try:
            # Coba format lain (misal, ISO format dari database)
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return None

@register.simple_tag
def timeuntil_days(dt1, dt2):
    """
    Menghitung selisih hari antara dua datetime.
    Mengembalikan selisih dalam integer (jumlah hari).
    dt1 = tanggal masa depan (deadline)
    dt2 = tanggal sekarang
    """
    if not dt1 or not dt2:
        return None

    try:
        # Menyamakan timezone jika salah satu 'aware' dan yang lain 'naive'
        if dt1.tzinfo is not None and dt2.tzinfo is None:
            # Jika dt1 (database) 'aware' dan dt2 (dari {% now %}) 'naive'
            dt2 = dt2.replace(tzinfo=dt1.tzinfo)
        elif dt1.tzinfo is None and dt2.tzinfo is not None:
            # Jika dt1 'naive' dan dt2 'aware'
            dt1 = dt1.replace(tzinfo=dt2.tzinfo)
        
        # Hitung selisih
        time_diff = dt1 - dt2
        
        # Ambil total detik dan bagi jadi hari, lalu bulatkan ke bawah (int)
        # 1.9 hari lagi -> 1 hari
        # 0.5 hari lagi -> 0 hari (Hari ini)
        # -0.1 hari lagi -> -1 hari (Terlambat)
        return int(time_diff.total_seconds() / (60 * 60 * 24))
    
    except (AttributeError, TypeError, ValueError):
        # Salah satu input bukan datetime yang valid
        return None