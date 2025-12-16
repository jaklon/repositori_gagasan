# repository/templatetags/repository_extras.py

from django import template
from datetime import datetime, timedelta, timezone
import re # <-- BARIS INI HARUS DITAMBAHKAN

# 1. HANYA SATU baris 'register' ini yang diperlukan.
register = template.Library()

# ------------------------------------------------------------------
# Filter BARU: is_url (WAJIB DITAMBAHKAN)
# ------------------------------------------------------------------
@register.filter
def is_url(value):
    """
    Cek apakah string menyerupai URL.
    """
    if not isinstance(value, str):
        return False
    
    # Regex yang lebih sederhana dan aman: cek apakah diawali http/https.
    # Jika perlu validasi yang lebih ketat, gunakan regex yang lebih kompleks.
    return value.lower().startswith('http://') or value.lower().startswith('https://')
    
    # Atau gunakan Regex yang lebih kompleks seperti:
    # url_regex = re.compile(r'^(?:http|ftp)s?://' 
    #                        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
    #                        r'localhost|' 
    #                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
    #                        r'(?::\d+)?' 
    #                        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    # return re.match(url_regex, value) is not None


# ------------------------------------------------------------------
# Filter BARU: is_in
# ------------------------------------------------------------------
@register.filter(name='is_in')
def is_in(value, arg):
    """
    Checks if a value (e.g., request.user.peran) is contained within a comma-separated list of strings (e.g., "dosen,mitra").
    Example usage: {% if request.user.peran|is_in:"dosen,mitra,unit_bisnis" %}
    """
    if not arg:
        return False
    # Split the argument string by comma and strip spaces
    list_of_values = [item.strip() for item in arg.split(',')]
    # Convert value to string for comparison and check for presence
    return str(value) in list_of_values

# ------------------------------------------------------------------
# Filter yang sudah ada
# ------------------------------------------------------------------
@register.filter(name='get_item')
def get_item(dictionary, key):
    """ Allows accessing dictionary keys with variables in templates """
    return dictionary.get(key)

@register.filter
def add_days(value, days):
    """
    Menambahkan sejumlah hari ke sebuah tanggal (datetime object).
    """
    if not value:
        return None
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        return None

# ------------------------------------------------------------------
# Tag yang sudah ada
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
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        try:
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return None

@register.simple_tag
def timeuntil_days(dt1, dt2):
    """
    Menghitung selisih hari antara dua datetime.
    """
    if not dt1 or not dt2:
        return None

    try:
        # Menangani timezone awareness
        if dt1.tzinfo is not None and dt2.tzinfo is None:
            dt2 = dt2.replace(tzinfo=dt1.tzinfo)
        elif dt1.tzinfo is None and dt2.tzinfo is not None:
            dt1 = dt1.replace(tzinfo=dt2.tzinfo)
        
        time_diff = dt1 - dt2
        
        # Mengembalikan selisih dalam hari (integer)
        return int(time_diff.total_seconds() / (60 * 60 * 24))
    
    except (AttributeError, TypeError, ValueError):
        return None