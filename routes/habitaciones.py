from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from routes.validators import (validar_texto, validar_numero_positivo,
                                validar_entero_positivo, recolectar_errores)

habitaciones_bp = Blueprint('habitaciones', __name__)

TIPOS_HABITACION = [
    'individual', 'doble estándar', 'doble twin', 'triple',
    'cuadruple', 'suite junior', 'suite ejecutiva', 'apartamento'
]

ESTADOS_HABITACION = [
    'disponible', 'ocupada', 'reservada',
    'mantenimiento', 'limpieza', 'bloqueada'
]

# ─────────────────────────────────────────
#  LISTAR HABITACIONES
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones')
@staff_required
def listar():
    estado   = request.args.get('estado', '')
    tipo     = request.args.get('tipo', '')
    hotel_id = request.args.get('hotel_id', '')

    sql = """
        SELECT h.*, ht.nombre AS hotel_nombre
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE 1=1
    """
    params = []

    if estado:
        sql += " AND h.estado = %s"
        params.append(estado)
    if tipo:
        sql += " AND h.tipo = %s"
        params.append(tipo)
    if hotel_id:
        sql += " AND h.hotel_id = %s"
        params.append(hotel_id)

    sql += " ORDER BY ht.nombre, h.piso, h.numero"

    habitaciones = query_db(sql, params)
    hoteles      = query_db("SELECT hotel_id, nombre FROM Hoteles ORDER BY nombre")

    return render_template(
        'admin/habitaciones/listar.html',
        habitaciones     = habitaciones,
        hoteles          = hoteles,
        tipos            = TIPOS_HABITACION,
        estados          = ESTADOS_HABITACION,
        filtro_estado    = estado,
        filtro_tipo      = tipo,
        filtro_hotel     = hotel_id
    )


# ─────────────────────────────────────────
#  NUEVA HABITACIÓN
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones/nueva', methods=['GET', 'POST'])
@staff_required
def nueva():
    hoteles = query_db("SELECT hotel_id, nombre FROM Hoteles ORDER BY nombre")
    if request.method == 'POST':
        return _guardar_habitacion(None)
    return render_template(
        'admin/habitaciones/form.html',
        habitacion = None,
        hoteles    = hoteles,
        tipos      = TIPOS_HABITACION,
        estados    = ESTADOS_HABITACION
    )


# ─────────────────────────────────────────
#  EDITAR HABITACIÓN
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones/<int:habitacion_id>/editar', methods=['GET', 'POST'])
@staff_required
def editar(habitacion_id):
    habitacion = query_db(
        "SELECT * FROM Habitaciones WHERE habitacion_id = %s",
        (habitacion_id,), fetchone=True
    )
    if not habitacion:
        flash('Habitación no encontrada.', 'danger')
        return redirect(url_for('habitaciones.listar'))

    hoteles = query_db("SELECT hotel_id, nombre FROM Hoteles ORDER BY nombre")

    if request.method == 'POST':
        return _guardar_habitacion(habitacion_id)

    return render_template(
        'admin/habitaciones/form.html',
        habitacion = habitacion,
        hoteles    = hoteles,
        tipos      = TIPOS_HABITACION,
        estados    = ESTADOS_HABITACION
    )


# ─────────────────────────────────────────
#  DETALLE HABITACIÓN
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones/<int:habitacion_id>')
@staff_required
def detalle(habitacion_id):
    habitacion = query_db(
        """
        SELECT h.*, ht.nombre AS hotel_nombre
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE h.habitacion_id = %s
        """,
        (habitacion_id,), fetchone=True
    )
    if not habitacion:
        flash('Habitación no encontrada.', 'danger')
        return redirect(url_for('habitaciones.listar'))

    # Historial de reservas de esta habitación
    reservas = query_db(
        """
        SELECT r.reserva_id, r.fecha_inicio, r.fecha_fin, r.estado, r.total,
               c.nombre || ' ' || c.apellido AS cliente
        FROM Reservas r
        JOIN Clientes c ON r.cliente_id = c.cliente_id
        WHERE r.habitacion_id = %s
        ORDER BY r.fecha_inicio DESC
        """,
        (habitacion_id,)
    )

    return render_template(
        'admin/habitaciones/detalle.html',
        habitacion = habitacion,
        reservas   = reservas
    )


# ─────────────────────────────────────────
#  CAMBIAR ESTADO RÁPIDO
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones/<int:habitacion_id>/estado', methods=['POST'])
@staff_required
def cambiar_estado(habitacion_id):
    nuevo_estado = request.form.get('estado')
    if nuevo_estado not in ESTADOS_HABITACION:
        flash('Estado no válido.', 'danger')
        return redirect(url_for('habitaciones.listar'))
    try:
        execute_db(
            "UPDATE Habitaciones SET estado = %s WHERE habitacion_id = %s",
            (nuevo_estado, habitacion_id)
        )
        flash(f'Estado actualizado a "{nuevo_estado}".', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('habitaciones.listar'))


# ─────────────────────────────────────────
#  ELIMINAR HABITACIÓN
# ─────────────────────────────────────────
@habitaciones_bp.route('/admin/habitaciones/<int:habitacion_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(habitacion_id):
    try:
        execute_db("DELETE FROM Habitaciones WHERE habitacion_id = %s", (habitacion_id,))
        flash('Habitación eliminada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'danger')
    return redirect(url_for('habitaciones.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_habitacion(habitacion_id):
    hotel_id          = request.form.get('hotel_id')
    numero            = request.form.get('numero', '').strip()
    piso              = request.form.get('piso') or None
    tipo              = request.form.get('tipo')
    capacidad_adultos = request.form.get('capacidad_adultos', 1)
    capacidad_menores = request.form.get('capacidad_menores', 0)
    permite_mascotas  = 'permite_mascotas' in request.form
    precio_base       = request.form.get('precio_base', 0)
    estado            = request.form.get('estado', 'disponible')

    errores = recolectar_errores(
        validar_texto(numero, 'Número de habitación', min_len=1, max_len=10),
        validar_numero_positivo(precio_base, 'Precio por noche'),
        validar_entero_positivo(capacidad_adultos, 'Capacidad adultos', min_val=1),
        validar_entero_positivo(capacidad_menores, 'Capacidad menores', min_val=0),
        None if hotel_id else 'El hotel es obligatorio.',
        None if tipo else 'El tipo de habitación es obligatorio.'
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        if habitacion_id is None:
            execute_db(
                """
                INSERT INTO Habitaciones
                    (hotel_id, numero, piso, tipo, capacidad_adultos,
                     capacidad_menores, permite_mascotas, precio_base, estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (hotel_id, numero, piso, tipo, capacidad_adultos,
                 capacidad_menores, permite_mascotas, precio_base, estado)
            )
            flash('Habitación registrada correctamente.', 'success')
        else:
            execute_db(
                """
                UPDATE Habitaciones
                SET hotel_id=%s, numero=%s, piso=%s, tipo=%s,
                    capacidad_adultos=%s, capacidad_menores=%s,
                    permite_mascotas=%s, precio_base=%s, estado=%s
                WHERE habitacion_id=%s
                """,
                (hotel_id, numero, piso, tipo, capacidad_adultos,
                 capacidad_menores, permite_mascotas, precio_base,
                 estado, habitacion_id)
            )
            flash('Habitación actualizada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar habitación: {e}', 'danger')

    return redirect(url_for('habitaciones.listar'))