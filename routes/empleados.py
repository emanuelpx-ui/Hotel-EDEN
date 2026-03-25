from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from werkzeug.security import generate_password_hash
from routes.validators import (validar_texto, validar_email,
                                validar_telefono, validar_username,
                                validar_password, recolectar_errores)


empleados_bp = Blueprint('empleados', __name__)

# ─────────────────────────────────────────
#  LISTAR EMPLEADOS
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados')
@staff_required
def listar():
    filtro_rol    = request.args.get('rol_id', '')
    filtro_activo = request.args.get('activo', '')

    sql = """
        SELECT e.*, r.nombre AS rol_nombre
        FROM Empleados e
        JOIN Roles r ON e.rol_id = r.rol_id
        WHERE 1=1
    """
    params = []

    if filtro_rol:
        sql += " AND e.rol_id = %s"
        params.append(filtro_rol)
    if filtro_activo != '':
        sql += " AND e.activo = %s"
        params.append(filtro_activo == 'true')

    sql += " ORDER BY e.nombre ASC"

    empleados = query_db(sql, params)
    roles     = query_db("SELECT * FROM Roles ORDER BY nombre")

    total_activos   = sum(1 for e in empleados if e['activo'])
    total_inactivos = sum(1 for e in empleados if not e['activo'])

    return render_template(
        'admin/empleados/listar.html',
        empleados       = empleados,
        roles           = roles,
        filtro_rol      = filtro_rol,
        filtro_activo   = filtro_activo,
        total_activos   = total_activos,
        total_inactivos = total_inactivos
    )


# ─────────────────────────────────────────
#  NUEVO EMPLEADO
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    roles = query_db("SELECT * FROM Roles ORDER BY nombre")
    if request.method == 'POST':
        return _guardar_empleado(None)
    return render_template(
        'admin/empleados/form.html',
        empleado = None,
        roles    = roles
    )


# ─────────────────────────────────────────
#  EDITAR EMPLEADO
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/<int:empleado_id>/editar', methods=['GET', 'POST'])
@staff_required
def editar(empleado_id):
    empleado = query_db(
        "SELECT * FROM Empleados WHERE empleado_id = %s",
        (empleado_id,), fetchone=True
    )
    if not empleado:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('empleados.listar'))

    roles = query_db("SELECT * FROM Roles ORDER BY nombre")

    if request.method == 'POST':
        return _guardar_empleado(empleado_id)

    return render_template(
        'admin/empleados/form.html',
        empleado = empleado,
        roles    = roles
    )


# ─────────────────────────────────────────
#  DETALLE EMPLEADO
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/<int:empleado_id>')
@staff_required
def detalle(empleado_id):
    empleado = query_db(
        """
        SELECT e.*, r.nombre AS rol_nombre
        FROM Empleados e
        JOIN Roles r ON e.rol_id = r.rol_id
        WHERE e.empleado_id = %s
        """,
        (empleado_id,), fetchone=True
    )
    if not empleado:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('empleados.listar'))

    # Historial de turnos
    turnos = query_db(
        """
        SELECT * FROM Turnos
        WHERE empleado_id = %s
        ORDER BY fecha_inicio DESC, hora_inicio DESC
        """,
        (empleado_id,)
    )

    # Usuario del sistema
    usuario = query_db(
        """
        SELECT u.*, r.nombre AS rol_nombre
        FROM UsuariosSistema u
        JOIN Roles r ON u.rol_id = r.rol_id
        WHERE u.empleado_id = %s
        """,
        (empleado_id,), fetchone=True
    )

    # Turno activo hoy
    turno_hoy = query_db(
        """
        SELECT * FROM Turnos
        WHERE empleado_id = %s
        AND fecha_inicio <= CURRENT_DATE
        AND fecha_fin >= CURRENT_DATE
        """,
        (empleado_id,), fetchone=True
    )

    return render_template(
        'admin/empleados/detalle.html',
        empleado  = empleado,
        turnos    = turnos,
        usuario   = usuario,
        turno_hoy = turno_hoy
    )


# ─────────────────────────────────────────
#  ACTIVAR / DESACTIVAR EMPLEADO
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/<int:empleado_id>/toggle', methods=['POST'])
@staff_required
def toggle_activo(empleado_id):
    empleado = query_db(
        "SELECT activo FROM Empleados WHERE empleado_id = %s",
        (empleado_id,), fetchone=True
    )
    if not empleado:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('empleados.listar'))

    nuevo_estado = not empleado['activo']
    execute_db(
        "UPDATE Empleados SET activo = %s WHERE empleado_id = %s",
        (nuevo_estado, empleado_id)
    )
    estado_texto = 'activado' if nuevo_estado else 'desactivado'
    flash(f'Empleado {estado_texto} correctamente.', 'success')
    return redirect(url_for('empleados.detalle', empleado_id=empleado_id))


# ─────────────────────────────────────────
#  CREAR USUARIO DEL SISTEMA
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/<int:empleado_id>/crear-usuario', methods=['POST'])
@staff_required
def crear_usuario(empleado_id):
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    rol_id   = request.form.get('rol_id')

    errores = recolectar_errores(
        validar_username(username),
        validar_password(password, min_len=6),
        None if rol_id else 'El rol es obligatorio.'
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(url_for('empleados.detalle', empleado_id=empleado_id))

    # Verificar si ya tiene usuario
    existe = query_db(
        "SELECT usuario_id FROM UsuariosSistema WHERE empleado_id = %s",
        (empleado_id,), fetchone=True
    )
    if existe:
        flash('Este empleado ya tiene un usuario del sistema.', 'warning')
        return redirect(url_for('empleados.detalle', empleado_id=empleado_id))

    try:
        execute_db(
            """
            INSERT INTO UsuariosSistema
                (empleado_id, username, password_hash, rol_id, activo)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (empleado_id, username, generate_password_hash(password), rol_id)
        )
        flash('Usuario del sistema creado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al crear usuario: {e}', 'danger')

    return redirect(url_for('empleados.detalle', empleado_id=empleado_id))


# ─────────────────────────────────────────
#  ELIMINAR EMPLEADO
# ─────────────────────────────────────────
@empleados_bp.route('/admin/empleados/<int:empleado_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(empleado_id):
    try:
        execute_db("DELETE FROM Empleados WHERE empleado_id = %s", (empleado_id,))
        flash('Empleado eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'danger')
    return redirect(url_for('empleados.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_empleado(empleado_id):
    nombre   = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    email    = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    rol_id   = request.form.get('rol_id')

    errores = recolectar_errores(
        validar_texto(nombre,   'Nombre',   min_len=2, max_len=50),
        validar_texto(apellido, 'Apellido', min_len=2, max_len=50),
        validar_email(email),
        validar_telefono(telefono),
        None if rol_id else 'El rol es obligatorio.'
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        if empleado_id is None:
            execute_db(
                """
                INSERT INTO Empleados
                    (nombre, apellido, email, telefono, rol_id, activo)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                """,
                (nombre, apellido, email, telefono or None, rol_id)
            )
            flash('Empleado registrado correctamente.', 'success')
        else:
            execute_db(
                """
                UPDATE Empleados
                SET nombre=%s, apellido=%s, email=%s, telefono=%s, rol_id=%s
                WHERE empleado_id=%s
                """,
                (nombre, apellido, email, telefono or None, rol_id, empleado_id)
            )
            flash('Empleado actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar empleado: {e}', 'danger')

    return redirect(url_for('empleados.listar'))