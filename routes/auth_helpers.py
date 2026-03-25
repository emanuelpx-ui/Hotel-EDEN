from functools import wraps
from flask import session, redirect, url_for, flash
from datetime import datetime

# Roles que pertenecen al staff (panel interno)
ROLES_STAFF = [
    'administración',
    'gerencia',
    'recepción',
    'limpieza',
    'mantenimiento',
    'seguridad',
    'concierge',
    'cocina',
    'atención al cliente',
]
ROLES_CLIENTE = ['cliente']

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.admin_login'))

        # Verificar expiración
        expira_en = session.get('expira_en')
        if expira_en and datetime.now() > datetime.fromisoformat(expira_en):
            session.clear()
            flash('Tu sesión ha expirado. Inicia sesión nuevamente.', 'warning')
            return redirect(url_for('auth.admin_login'))

        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    """Solo permite acceso a roles de staff."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Acceso restringido.', 'warning')
            return redirect(url_for('auth.admin_login'))
        if session.get('rol') not in ROLES_STAFF:
            flash('No tienes permiso para acceder al panel interno.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated

def cliente_required(f):
    """Solo permite acceso a clientes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth.cliente_login'))
        if session.get('rol') != 'cliente':
            flash('Acceso no permitido.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated