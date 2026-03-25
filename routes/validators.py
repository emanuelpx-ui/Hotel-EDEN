import re

# ─────────────────────────────────────────
#  VALIDACIONES GENERALES
# ─────────────────────────────────────────

def validar_texto(valor, nombre, min_len=2, max_len=100):
    """Valida que un campo de texto no esté vacío y tenga longitud correcta."""
    if not valor or not valor.strip():
        return f'{nombre} es obligatorio.'
    if len(valor.strip()) < min_len:
        return f'{nombre} debe tener al menos {min_len} caracteres.'
    if len(valor.strip()) > max_len:
        return f'{nombre} no puede tener más de {max_len} caracteres.'
    return None

def validar_email(email):
    """Valida formato de email."""
    if not email:
        return None  # Email es opcional en algunos formularios
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return 'El email no tiene un formato válido.'
    return None

def validar_telefono(telefono):
    """Valida que el teléfono solo tenga números y guiones."""
    if not telefono:
        return None  # Teléfono es opcional
    patron = r'^[\d\s\-\+\(\)]{7,20}$'
    if not re.match(patron, telefono):
        return 'El teléfono solo puede contener números, espacios y guiones.'
    return None

def validar_numero_positivo(valor, nombre):
    """Valida que un número sea positivo."""
    try:
        num = float(valor)
        if num <= 0:
            return f'{nombre} debe ser mayor a 0.'
    except (TypeError, ValueError):
        return f'{nombre} debe ser un número válido.'
    return None

def validar_entero_positivo(valor, nombre, min_val=0):
    """Valida que un entero sea positivo."""
    try:
        num = int(valor)
        if num < min_val:
            return f'{nombre} debe ser mayor o igual a {min_val}.'
    except (TypeError, ValueError):
        return f'{nombre} debe ser un número entero válido.'
    return None

def validar_fechas(fecha_inicio, fecha_fin):
    """Valida que fecha_fin sea posterior a fecha_inicio."""
    from datetime import datetime
    try:
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fin    = datetime.strptime(fecha_fin, '%Y-%m-%d')
        if fin <= inicio:
            return 'La fecha de salida debe ser posterior a la de entrada.'
    except (TypeError, ValueError):
        return 'Las fechas no tienen un formato válido.'
    return None

def validar_password(password, min_len=6):
    """Valida que la contraseña tenga la longitud mínima."""
    if not password:
        return 'La contraseña es obligatoria.'
    if len(password) < min_len:
        return f'La contraseña debe tener al menos {min_len} caracteres.'
    return None

def validar_username(username):
    """Valida que el username solo tenga caracteres permitidos."""
    if not username:
        return 'El nombre de usuario es obligatorio.'
    patron = r'^[a-zA-Z0-9_\.]{3,50}$'
    if not re.match(patron, username):
        return 'El usuario solo puede contener letras, números, puntos y guiones bajos (3-50 caracteres).'
    return None

def recolectar_errores(*validaciones):
    """
    Recibe múltiples resultados de validación y devuelve
    lista de errores (sin None).
    """
    return [e for e in validaciones if e is not None]