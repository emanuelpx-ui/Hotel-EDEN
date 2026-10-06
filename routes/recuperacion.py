from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from werkzeug.security import generate_password_hash
from routes.validators import validar_password, validar_username, recolectar_errores
import secrets
from datetime import datetime, timedelta

recuperacion_bp = Blueprint('recuperacion', __name__)

# ─────────────────────────────────────────
#  SOLICITAR TOKEN
# ─────────────────────────────────────────
@recuperacion_bp.route('/recuperar', methods=['GET', 'POST'])
def solicitar():
    token_generado = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        if not username:
            flash('Ingresa tu nombre de usuario.', 'warning')
            return render_template('public/recuperar.html', token=None)

        # Buscar usuario
        usuario = query_db(
            "SELECT usuario_id, username FROM UsuariosSistema WHERE username = %s AND activo = TRUE",
            (username,), fetchone=True
        )

        if not usuario:
            flash('No se encontró ningún usuario activo con ese nombre.', 'danger')
            return render_template('public/recuperar.html', token=None)

        # Invalidar tokens anteriores del mismo usuario
        execute_db(
            "UPDATE TokensRecuperacion SET usado = TRUE WHERE usuario_id = %s AND usado = FALSE",
            (usuario['usuario_id'],)
        )

        # Generar token único
        token = secrets.token_urlsafe(32)
        expira = datetime.now() + timedelta(minutes=30)

        execute_db(
            """
            INSERT INTO TokensRecuperacion (usuario_id, token, fecha_expira, usado)
            VALUES (%s, %s, %s, FALSE)
            """,
            (usuario['usuario_id'], token, expira)
        )

        token_generado = token
        flash('Token generado correctamente. Cópialo antes de salir de esta página.', 'success')

    return render_template('public/recuperar.html', token=token_generado)


# ─────────────────────────────────────────
#  RESTABLECER CONTRASEÑA
# ─────────────────────────────────────────
@recuperacion_bp.route('/restablecer', methods=['GET', 'POST'])
def restablecer():
    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        token       = request.form.get('token', '').strip()
        password    = request.form.get('password', '').strip()
        confirmar   = request.form.get('confirmar', '').strip()

        errores = recolectar_errores(
            validar_username(username),
            validar_password(password, min_len=6),
            None if token else 'El token es obligatorio.',
        )

        if password != confirmar:
            errores.append('Las contraseñas no coinciden.')

        if errores:
            for e in errores:
                flash(e, 'warning')
            return render_template('public/restablecer.html')

        # Buscar usuario
        usuario = query_db(
            "SELECT usuario_id FROM UsuariosSistema WHERE username = %s AND activo = TRUE",
            (username,), fetchone=True
        )

        if not usuario:
            flash('Usuario no encontrado.', 'danger')
            return render_template('public/restablecer.html')

        # Validar token
        registro = query_db(
            """
            SELECT token_id, fecha_expira, usado
            FROM TokensRecuperacion
            WHERE token = %s AND usuario_id = %s
            """,
            (token, usuario['usuario_id']), fetchone=True
        )

        if not registro:
            flash('Token inválido o no corresponde a ese usuario.', 'danger')
            return render_template('public/restablecer.html')

        if registro['usado']:
            flash('Este token ya fue utilizado. Genera uno nuevo.', 'danger')
            return render_template('public/restablecer.html')

        if datetime.now() > registro['fecha_expira']:
            flash('El token ha expirado. Genera uno nuevo.', 'danger')
            return render_template('public/restablecer.html')

        # Actualizar contraseña
        execute_db(
            "UPDATE UsuariosSistema SET password_hash = %s WHERE usuario_id = %s",
            (generate_password_hash(password), usuario['usuario_id'])
        )

        # Invalidar token
        execute_db(
            "UPDATE TokensRecuperacion SET usado = TRUE WHERE token_id = %s",
            (registro['token_id'],)
        )

        flash('Contraseña restablecida correctamente. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.cliente_login'))

    return render_template('public/restablecer.html')