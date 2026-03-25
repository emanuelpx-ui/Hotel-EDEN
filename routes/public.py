from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db
from routes.auth_helpers import cliente_required
from datetime import date
from werkzeug.security import generate_password_hash
from routes.validators import (validar_texto, validar_email, validar_telefono,
                                validar_username, validar_password,
                                validar_fechas, validar_numero_positivo,
                                validar_entero_positivo, recolectar_errores)

public_bp = Blueprint('public', __name__)

# ─────────────────────────────────────────
#  PÁGINA DE INICIO
# ─────────────────────────────────────────
@public_bp.route('/')
def index():
    # Habitaciones destacadas (3 disponibles)
    habitaciones = query_db(
        """
        SELECT h.*, ht.nombre AS hotel_nombre
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE h.estado = 'disponible'
        ORDER BY h.precio_base ASC
        LIMIT 3
        """
    )

    # Servicios
    servicios = query_db("SELECT * FROM Servicios ORDER BY servicio_id")

    # Promociones vigentes (3 máximo)
    hoy = date.today()
    promociones = query_db(
        """
        SELECT p.*, ht.nombre AS hotel_nombre
        FROM Promociones p
        JOIN Hoteles ht ON p.hotel_id = ht.hotel_id
        WHERE p.fecha_fin >= %s
        ORDER BY p.descuento DESC
        LIMIT 3
        """,
        (hoy,)
    )

    # Total promociones vigentes
    total_promociones = query_db(
        "SELECT COUNT(*) AS total FROM Promociones WHERE fecha_fin >= %s",
        (hoy,), fetchone=True
    )['total']

    # Opiniones de clientes
    opiniones = query_db(
        """
        SELECT o.*, c.nombre || ' ' || c.apellido AS cliente,
               ht.nombre AS hotel_nombre
        FROM OpinionesClientes o
        JOIN Clientes c  ON o.cliente_id = c.cliente_id
        JOIN Hoteles ht  ON o.hotel_id   = ht.hotel_id
        ORDER BY o.fecha DESC
        LIMIT 6
        """
    )

    # Hoteles para contacto
    hoteles = query_db("SELECT * FROM Hoteles ORDER BY hotel_id")

    return render_template(
        'public/index.html',
        habitaciones      = habitaciones,
        servicios         = servicios,
        promociones       = promociones,
        total_promociones = total_promociones,
        opiniones         = opiniones,
        hoteles           = hoteles
    )


# ─────────────────────────────────────────
#  HABITACIONES
# ─────────────────────────────────────────
@public_bp.route('/habitaciones')
def habitaciones():
    tipo     = request.args.get('tipo', '')
    mascotas = request.args.get('mascotas', '')

    sql = """
        SELECT h.*, ht.nombre AS hotel_nombre
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE h.estado = 'disponible'
    """
    params = []

    if tipo:
        sql += " AND h.tipo = %s"
        params.append(tipo)
    if mascotas:
        sql += " AND h.permite_mascotas = TRUE"

    sql += " ORDER BY h.precio_base ASC"

    habitaciones = query_db(sql, params)
    tipos = [
        'individual', 'doble estándar', 'doble twin', 'triple',
        'cuadruple', 'suite junior', 'suite ejecutiva', 'apartamento'
    ]

    return render_template(
        'public/habitaciones.html',
        habitaciones     = habitaciones,
        tipos            = tipos,
        filtro_tipo      = tipo,
        filtro_mascotas  = mascotas
    )


# ─────────────────────────────────────────
#  PROMOCIONES
# ─────────────────────────────────────────
@public_bp.route('/promociones')
def promociones():
    hoy = date.today()
    promociones = query_db(
        """
        SELECT p.*, ht.nombre AS hotel_nombre
        FROM Promociones p
        JOIN Hoteles ht ON p.hotel_id = ht.hotel_id
        WHERE p.fecha_fin >= %s
        ORDER BY p.descuento DESC
        """,
        (hoy,)
    )
    return render_template('public/promociones.html', promociones=promociones)


# ─────────────────────────────────────────
#  RESERVAR identacion revisar
# ─────────────────────────────────────────
@public_bp.route('/reservar', methods=['GET', 'POST'])
@public_bp.route('/reservar', methods=['GET', 'POST'])
def reservar():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para hacer una reserva.', 'warning')
        return redirect(url_for('auth.cliente_login'))

    habitacion_id = request.args.get('habitacion_id', '')
    habitaciones  = query_db(
        """
        SELECT h.*, ht.nombre AS hotel_nombre
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE h.estado = 'disponible'
        ORDER BY h.precio_base ASC
        """
    )

    if request.method == 'POST':
        cliente_id    = request.form.get('cliente_id')
        habitacion_id = request.form.get('habitacion_id')
        fecha_inicio  = request.form.get('fecha_inicio')
        fecha_fin     = request.form.get('fecha_fin')
        num_adultos   = request.form.get('num_adultos', 1)
        num_menores   = request.form.get('num_menores', 0)
        num_mascotas  = request.form.get('num_mascotas', 0)
        total         = request.form.get('total', 0)

        errores = recolectar_errores(
            None if cliente_id    else 'No se encontró tu perfil. Contacta a recepción.',
            None if habitacion_id else 'La habitación es obligatoria.',
            None if fecha_inicio  else 'La fecha de entrada es obligatoria.',
            None if fecha_fin     else 'La fecha de salida es obligatoria.',
            validar_fechas(fecha_inicio, fecha_fin) if fecha_inicio and fecha_fin else None,
            validar_entero_positivo(num_adultos, 'Número de adultos', min_val=1),
            validar_numero_positivo(total, 'Total') if total else None
        )

        if errores:
            for e in errores:
                flash(e, 'warning')
            return redirect(request.referrer)

        try:
            execute_db(
                """
                INSERT INTO Reservas
                    (cliente_id, habitacion_id, fecha_inicio, fecha_fin,
                     num_adultos, num_menores, num_mascotas, estado, total)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'pendiente',%s)
                """,
                (cliente_id, habitacion_id, fecha_inicio, fecha_fin,
                 num_adultos, num_menores, num_mascotas, total)
            )
            execute_db(
                "UPDATE Habitaciones SET estado='reservada' WHERE habitacion_id=%s",
                (habitacion_id,)
            )
            flash('¡Reserva creada correctamente! El hotel confirmará en breve.', 'success')
            return redirect(url_for('public.mis_reservas'))
        except Exception as e:
            flash(f'Error al crear reserva: {e}', 'danger')

    # Obtener cliente_id del usuario logueado
    usuario = query_db(
        """
        SELECT e.empleado_id, u.usuario_id
        FROM UsuariosSistema u
        LEFT JOIN Empleados e ON u.empleado_id = e.empleado_id
        WHERE u.usuario_id = %s
        """,
        (session.get('usuario_id'),), fetchone=True
    )

    cliente = query_db(
        """
        SELECT c.cliente_id FROM Clientes c
        JOIN UsuariosSistema u ON u.usuario_id = %s
        WHERE c.email = (
            SELECT email FROM Empleados WHERE empleado_id = u.empleado_id
        )
        """,
        (session.get('usuario_id'),), fetchone=True
    )

    return render_template(
        'public/reservar.html',
        habitaciones  = habitaciones,
        habitacion_id = habitacion_id,
        cliente       = cliente,
        today         = date.today()
    )


# ─────────────────────────────────────────
#  REGISTRO CLIENTE revisar identacion
# ─────────────────────────────────────────
@public_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre           = request.form.get('nombre', '').strip()
        apellido         = request.form.get('apellido', '').strip()
        email            = request.form.get('email', '').strip()
        telefono         = request.form.get('telefono', '').strip()
        direccion        = request.form.get('direccion', '').strip()
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()
        username         = request.form.get('username', '').strip()
        password         = request.form.get('password', '').strip()

        errores = recolectar_errores(
            validar_texto(nombre,   'Nombre',   min_len=2, max_len=50),
            validar_texto(apellido, 'Apellido', min_len=2, max_len=50),
            validar_email(email),
            validar_telefono(telefono),
            validar_username(username),
            validar_password(password, min_len=6)
        )

        if not email:
            errores.append('El email es obligatorio.')

        if errores:
            for e in errores:
                flash(e, 'warning')
            return redirect(request.referrer)

        try:
            email_existe = query_db(
                "SELECT cliente_id FROM Clientes WHERE email = %s",
                (email,), fetchone=True
            )
            if email_existe:
                flash('Ya existe una cuenta con ese email.', 'warning')
                return redirect(request.referrer)

            username_existe = query_db(
                "SELECT usuario_id FROM UsuariosSistema WHERE username = %s",
                (username,), fetchone=True
            )
            if username_existe:
                flash('Ese nombre de usuario ya está en uso.', 'warning')
                return redirect(request.referrer)

            cliente_id = execute_db(
                """
                INSERT INTO Clientes
                    (nombre, apellido, email, telefono, direccion, fecha_nacimiento)
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING cliente_id
                """,
                (nombre, apellido, email,
                 telefono or None, direccion or None,
                 fecha_nacimiento or None)
            )

            rol = query_db(
                "SELECT rol_id FROM Roles WHERE nombre = 'cliente'",
                fetchone=True
            )

            empleado_id = execute_db(
                """
                INSERT INTO Empleados (nombre, apellido, email, rol_id, activo)
                VALUES (%s,%s,%s,%s,TRUE)
                RETURNING empleado_id
                """,
                (nombre, apellido, email, rol['rol_id'])
            )

            execute_db(
                """
                INSERT INTO UsuariosSistema
                    (empleado_id, username, password_hash, rol_id, activo)
                VALUES (%s,%s,%s,%s,TRUE)
                """,
                (empleado_id, username, generate_password_hash(password), rol['rol_id'])
            )

            flash('¡Cuenta creada correctamente! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.cliente_login'))

        except Exception as e:
            flash(f'Error al registrar: {e}', 'danger')

    return render_template('public/registro.html')


# ─────────────────────────────────────────
#  MIS RESERVAS
# ─────────────────────────────────────────
@public_bp.route('/mis-reservas')
def mis_reservas():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('auth.cliente_login'))

    # Buscar cliente por usuario
    cliente = query_db(
        """
        SELECT c.* FROM Clientes c
        JOIN Empleados e     ON c.email = e.email
        JOIN UsuariosSistema u ON e.empleado_id = u.empleado_id
        WHERE u.usuario_id = %s
        """,
        (session.get('usuario_id'),), fetchone=True
    )

    if not cliente:
        flash('No se encontró tu perfil de cliente.', 'danger')
        return redirect(url_for('public.index'))

    reservas = query_db(
        """
        SELECT r.*, h.numero AS habitacion, h.tipo AS tipo_hab,
               ht.nombre AS hotel
        FROM Reservas r
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE r.cliente_id = %s
        ORDER BY r.fecha_inicio DESC
        """,
        (cliente['cliente_id'],)
    )

    return render_template(
        'public/mis_reservas.html',
        cliente  = cliente,
        reservas = reservas
    )


# ─────────────────────────────────────────
#  MI PERFIL identacion
# ─────────────────────────────────────────
@public_bp.route('/mi-perfil', methods=['GET', 'POST'])
def mi_perfil():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('auth.cliente_login'))

    cliente = query_db(
        """
        SELECT c.* FROM Clientes c
        JOIN Empleados e      ON c.email = e.email
        JOIN UsuariosSistema u ON e.empleado_id = u.empleado_id
        WHERE u.usuario_id = %s
        """,
        (session.get('usuario_id'),), fetchone=True
    )

    if not cliente:
        flash('No se encontró tu perfil.', 'danger')
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        nombre           = request.form.get('nombre', '').strip()
        apellido         = request.form.get('apellido', '').strip()
        telefono         = request.form.get('telefono', '').strip()
        direccion        = request.form.get('direccion', '').strip()
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()

        errores = recolectar_errores(
            validar_texto(nombre,   'Nombre',   min_len=2, max_len=50),
            validar_texto(apellido, 'Apellido', min_len=2, max_len=50),
            validar_telefono(telefono)
        )

        if errores:
            for e in errores:
                flash(e, 'warning')
            return redirect(request.referrer)

        try:
            execute_db(
                """
                UPDATE Clientes
                SET nombre=%s, apellido=%s, telefono=%s,
                    direccion=%s, fecha_nacimiento=%s
                WHERE cliente_id=%s
                """,
                (nombre, apellido, telefono or None,
                 direccion or None, fecha_nacimiento or None,
                 cliente['cliente_id'])
            )
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('public.mi_perfil'))
        except Exception as e:
            flash(f'Error al actualizar perfil: {e}', 'danger')

    return render_template('public/perfil.html', cliente=cliente)