from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from datetime import date
from routes.validators import recolectar_errores

turnos_bp = Blueprint('turnos', __name__)

# ─────────────────────────────────────────
#  LISTAR TURNOS
# ─────────────────────────────────────────
@turnos_bp.route('/admin/turnos')
@staff_required
def listar():
    empleado_id = request.args.get('empleado_id', '')
    fecha       = request.args.get('fecha', '')

    sql = """
        SELECT t.*, e.nombre || ' ' || e.apellido AS empleado,
               r.nombre AS rol
        FROM Turnos t
        JOIN Empleados e ON t.empleado_id = e.empleado_id
        JOIN Roles r     ON e.rol_id      = r.rol_id
        WHERE 1=1
    """
    params = []

    if empleado_id:
        sql += " AND t.empleado_id = %s"
        params.append(empleado_id)
    if fecha:
        sql += " AND t.fecha_inicio <= %s AND t.fecha_fin >= %s"
        params.extend([fecha, fecha])

    sql += " ORDER BY t.fecha_inicio DESC, t.hora_inicio DESC"

    turnos    = query_db(sql, params)
    empleados = query_db(
        "SELECT empleado_id, nombre, apellido FROM Empleados ORDER BY nombre"
    )

    # Turnos de hoy
    turnos_hoy = query_db(
        """
        SELECT t.*, e.nombre || ' ' || e.apellido AS empleado,
               r.nombre AS rol
        FROM Turnos t
        JOIN Empleados e ON t.empleado_id = e.empleado_id
        JOIN Roles r     ON e.rol_id      = r.rol_id
        WHERE t.fecha_inicio <= CURRENT_DATE
        AND   t.fecha_fin    >= CURRENT_DATE
        ORDER BY t.hora_inicio
        """
    )

    return render_template(
        'admin/turnos/listar.html',
        turnos          = turnos,
        turnos_hoy      = turnos_hoy,
        empleados       = empleados,
        filtro_empleado = empleado_id,
        filtro_fecha    = fecha
    )


# ─────────────────────────────────────────
#  NUEVO TURNO (desde módulo turnos)
# ─────────────────────────────────────────
@turnos_bp.route('/admin/turnos/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    empleados = query_db(
        "SELECT empleado_id, nombre, apellido FROM Empleados WHERE activo=TRUE ORDER BY nombre"
    )
    if request.method == 'POST':
        return _guardar_turno()
    return render_template(
        'admin/turnos/form.html',
        empleados   = empleados,
        empleado_id = None,
        today       = date.today()
    )


# ─────────────────────────────────────────
#  NUEVO TURNO (desde detalle empleado)
# ─────────────────────────────────────────
@turnos_bp.route('/admin/turnos/nuevo/<int:empleado_id>', methods=['GET', 'POST'])
@staff_required
def nuevo_para_empleado(empleado_id):
    empleado = query_db(
        "SELECT empleado_id, nombre, apellido FROM Empleados WHERE empleado_id = %s",
        (empleado_id,), fetchone=True
    )
    if not empleado:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('turnos.listar'))

    if request.method == 'POST':
        return _guardar_turno()

    return render_template(
        'admin/turnos/form.html',
        empleados   = [empleado],
        empleado_id = empleado_id,
        today       = date.today()
    )


# ─────────────────────────────────────────
#  ELIMINAR TURNO
# ─────────────────────────────────────────
@turnos_bp.route('/admin/turnos/<int:turno_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(turno_id):
    turno = query_db(
        "SELECT empleado_id FROM Turnos WHERE turno_id = %s",
        (turno_id,), fetchone=True
    )
    try:
        execute_db("DELETE FROM Turnos WHERE turno_id = %s", (turno_id,))
        flash('Turno eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar turno: {e}', 'danger')

    if turno and request.referrer and 'empleados' in request.referrer:
        return redirect(url_for('empleados.detalle', empleado_id=turno['empleado_id']))
    return redirect(url_for('turnos.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_turno():
    empleado_id  = request.form.get('empleado_id')
    fecha_inicio = request.form.get('fecha_inicio')
    hora_inicio  = request.form.get('hora_inicio')
    fecha_fin    = request.form.get('fecha_fin')
    hora_fin     = request.form.get('hora_fin')

    errores = recolectar_errores(
        None if empleado_id  else 'El empleado es obligatorio.',
        None if fecha_inicio else 'La fecha de inicio es obligatoria.',
        None if hora_inicio  else 'La hora de inicio es obligatoria.',
        None if fecha_fin    else 'La fecha de fin es obligatoria.',
        None if hora_fin     else 'La hora de fin es obligatoria.'
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    # Validar que fecha/hora fin > fecha/hora inicio
    if fecha_fin < fecha_inicio or (fecha_fin == fecha_inicio and hora_fin <= hora_inicio):
        flash('La fecha y hora de fin deben ser posteriores al inicio.', 'warning')
        return redirect(request.referrer)

    # Verificar conflicto de turnos
    conflicto = query_db(
        """
        SELECT turno_id FROM Turnos
        WHERE empleado_id = %s
        AND NOT (fecha_fin < %s OR fecha_inicio > %s)
        """,
        (empleado_id, fecha_inicio, fecha_fin),
        fetchone=True
    )
    if conflicto:
        flash('⚠️ Conflicto de turnos: el empleado ya tiene un turno en ese período.', 'danger')
        return redirect(request.referrer)

    try:
        execute_db(
            """
            INSERT INTO Turnos
                (empleado_id, fecha_inicio, hora_inicio, fecha_fin, hora_fin)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (empleado_id, fecha_inicio, hora_inicio, fecha_fin, hora_fin)
        )
        flash('Turno asignado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar turno: {e}', 'danger')

    return redirect(url_for('empleados.detalle', empleado_id=empleado_id))