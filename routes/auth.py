from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required, cliente_required, ROLES_STAFF, ROLES_CLIENTE
from werkzeug.security import check_password_hash
from datetime import timedelta
from flask import current_app

auth_bp = Blueprint('auth', __name__)

# ─────────────────────────────────────────
#  LOGIN STAFF  →  /admin/login
# ─────────────────────────────────────────
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'usuario_id' in session and session.get('tipo') == 'staff':
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        ip       = request.remote_addr

        # Verificar bloqueo
        intentos = get_intentos_fallidos(username, ip, 'staff')
        if intentos >= MAX_INTENTOS:
            flash(f'Demasiados intentos fallidos. Espera {BLOQUEO_MINUTOS} minutos.', 'danger')
            return render_template('admin/login.html')

        usuario = query_db(
            """
            SELECT u.usuario_id, u.username, u.password_hash, u.activo,
                   r.nombre AS rol
            FROM UsuariosSistema u
            JOIN Roles r ON u.rol_id = r.rol_id
            WHERE u.username = %s
            """,
            (username,),
            fetchone=True
        )

        if usuario and check_password_hash(usuario['password_hash'], password) and usuario['activo'] and usuario['rol'] not in ROLES_CLIENTE:
            limpiar_intentos(username, 'staff')
            session['usuario_id'] = usuario['usuario_id']
            session['username']   = usuario['username']
            session['rol']        = usuario['rol']
            session['tipo']       = 'staff'
            session.permanent     = True 
            session['expira_en']  = (datetime.now() + timedelta(minutes=5)).isoformat()

            try:
                execute_db(
                    "INSERT INTO LogsAcceso (usuario_id, accion, ip_origen, exitoso) VALUES (%s, %s, %s, TRUE)",
                    (usuario['usuario_id'], 'Inicio de sesión staff', ip)
                )
            except Exception:
                pass

            flash(f'Bienvenido, {username}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            registrar_intento(username, ip, 'staff')
            intentos_restantes = MAX_INTENTOS - intentos - 1
            try:
                if usuario:
                    execute_db(
                        "INSERT INTO LogsAcceso (usuario_id, accion, ip_origen, exitoso) VALUES (%s, %s, %s, FALSE)",
                        (usuario['usuario_id'], 'Intento de login fallido', ip)
                    )
            except Exception:
                pass

            if intentos_restantes > 0:
                flash(f'Usuario o contraseña incorrectos. Te quedan {intentos_restantes} intento(s).', 'danger')
            else:
                flash(f'Cuenta bloqueada por {BLOQUEO_MINUTOS} minutos.', 'danger')

    return render_template('admin/login.html')


# ─────────────────────────────────────────
#  LOGIN CLIENTE  →  /login
# ─────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def cliente_login():
    if 'usuario_id' in session and session.get('tipo') == 'cliente':
        return redirect(url_for('public.mis_reservas'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        ip       = request.remote_addr

        # Verificar bloqueo
        intentos = get_intentos_fallidos(username, ip, 'cliente')
        if intentos >= MAX_INTENTOS:
            flash(f'Demasiados intentos fallidos. Espera {BLOQUEO_MINUTOS} minutos.', 'danger')
            return render_template('public/login.html')

        usuario = query_db(
            """
            SELECT u.usuario_id, u.username, u.password_hash, u.activo,
                   r.nombre AS rol
            FROM UsuariosSistema u
            JOIN Roles r ON u.rol_id = r.rol_id
            WHERE u.username = %s
            """,
            (username,),
            fetchone=True
        )

        if usuario and check_password_hash(usuario['password_hash'], password) and usuario['activo']:
            limpiar_intentos(username, 'cliente')
            session['usuario_id'] = usuario['usuario_id']
            session['username']   = usuario['username']
            session['rol']        = usuario['rol']
            session['tipo']       = 'cliente'
            session.permanent     = True 
            session['expira_en']  = (datetime.now() + timedelta(minutes=30)).isoformat()


            flash(f'Bienvenido, {username}!', 'success')
            return redirect(url_for('public.index'))
        else:
            registrar_intento(username, ip, 'cliente')
            intentos_restantes = MAX_INTENTOS - intentos - 1
            try:
                if usuario:
                    execute_db(
                        "INSERT INTO LogsAcceso (usuario_id, accion, ip_origen, exitoso) VALUES (%s, %s, %s, FALSE)",
                        (usuario['usuario_id'], 'Intento de login fallido', ip)
                    )
            except Exception:
                pass

            if intentos_restantes > 0:
                flash(f'Usuario o contraseña incorrectos. Te quedan {intentos_restantes} intento(s).', 'danger')
            else:
                flash(f'Cuenta bloqueada por {BLOQUEO_MINUTOS} minutos.', 'danger')

    return render_template('public/login.html')
# ─────────────────────────────────────────
#  LOGOUT  →  /logout
# ─────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    tipo = session.get('tipo')
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')

    if tipo == 'staff':
        return redirect(url_for('auth.admin_login'))
    return redirect(url_for('auth.cliente_login'))

#intento de inicios de sesion

import os
from datetime import datetime, timedelta

MAX_INTENTOS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
BLOQUEO_MINUTOS = 15

def get_intentos_fallidos(username, ip, tipo):
    resultado = query_db(
        """
        SELECT COUNT(*) AS total FROM IntentosLogin
        WHERE (username = %s OR ip_origen = %s)
        AND tipo = %s
        AND fecha_hora > NOW() - INTERVAL '%s minutes'
        """,
        (username, ip, tipo, BLOQUEO_MINUTOS),
        fetchone=True
    )
    return resultado['total']

def registrar_intento(username, ip, tipo):
    execute_db(
        "INSERT INTO IntentosLogin (username, ip_origen, tipo) VALUES (%s, %s, %s)",
        (username, ip, tipo)
    )

def limpiar_intentos(username, tipo):
    execute_db(
        "DELETE FROM IntentosLogin WHERE username = %s AND tipo = %s",
        (username, tipo)
    )
