from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from datetime import date
from routes.validators import (validar_entero_positivo,
                                validar_numero_positivo, recolectar_errores)

consumos_bp = Blueprint('consumos', __name__)

# ─────────────────────────────────────────
#  LISTAR CONSUMOS
# ─────────────────────────────────────────
@consumos_bp.route('/admin/consumos')
@staff_required
def listar():
    servicio_id = request.args.get('servicio_id', '')
    fecha       = request.args.get('fecha', '')

    sql = """
        SELECT co.*, s.nombre AS servicio, s.precio AS precio_unitario,
               c.nombre || ' ' || c.apellido AS cliente,
               r.reserva_id, h.numero AS habitacion,
               ht.nombre AS hotel
        FROM Consumos co
        JOIN Servicios s    ON co.servicio_id  = s.servicio_id
        JOIN Reservas r     ON co.reserva_id   = r.reserva_id
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE 1=1
    """
    params = []

    if servicio_id:
        sql += " AND co.servicio_id = %s"
        params.append(servicio_id)
    if fecha:
        sql += " AND co.fecha = %s"
        params.append(fecha)

    sql += " ORDER BY co.fecha DESC, co.consumo_id DESC"

    consumos  = query_db(sql, params)
    servicios = query_db("SELECT servicio_id, nombre FROM Servicios ORDER BY nombre")

    total_general = sum(c['subtotal'] for c in consumos)

    return render_template(
        'admin/consumos/listar.html',
        consumos        = consumos,
        servicios       = servicios,
        filtro_servicio = servicio_id,
        filtro_fecha    = fecha,
        total_general   = total_general
    )


# ─────────────────────────────────────────
#  NUEVO CONSUMO (desde módulo consumos)
# ─────────────────────────────────────────
@consumos_bp.route('/admin/consumos/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    reservas  = query_db(
        """
        SELECT r.reserva_id,
               c.nombre || ' ' || c.apellido AS cliente,
               h.numero AS habitacion,
               ht.nombre AS hotel
        FROM Reservas r
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE r.estado IN ('confirmada', 'check-in')
        ORDER BY r.reserva_id DESC
        """
    )
    servicios = query_db("SELECT * FROM Servicios ORDER BY nombre")

    if request.method == 'POST':
        return _guardar_consumo()

    return render_template(
        'admin/consumos/form.html',
        reservas    = reservas,
        servicios   = servicios,
        reserva_id  = None,
        today       = date.today()
    )


# ─────────────────────────────────────────
#  NUEVO CONSUMO (desde detalle reserva)
# ─────────────────────────────────────────
@consumos_bp.route('/admin/consumos/nuevo/<int:reserva_id>', methods=['GET', 'POST'])
@staff_required
def nuevo_desde_reserva(reserva_id):
    reserva = query_db(
        """
        SELECT r.reserva_id,
               c.nombre || ' ' || c.apellido AS cliente,
               h.numero AS habitacion,
               ht.nombre AS hotel
        FROM Reservas r
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE r.reserva_id = %s
        """,
        (reserva_id,), fetchone=True
    )
    if not reserva:
        flash('Reserva no encontrada.', 'danger')
        return redirect(url_for('consumos.listar'))

    servicios = query_db("SELECT * FROM Servicios ORDER BY nombre")

    if request.method == 'POST':
        return _guardar_consumo()

    return render_template(
        'admin/consumos/form.html',
        reservas   = [reserva],
        servicios  = servicios,
        reserva_id = reserva_id,
        today      = date.today()
    )


# ─────────────────────────────────────────
#  ELIMINAR CONSUMO
# ─────────────────────────────────────────
@consumos_bp.route('/admin/consumos/<int:consumo_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(consumo_id):
    consumo = query_db(
        "SELECT reserva_id FROM Consumos WHERE consumo_id = %s",
        (consumo_id,), fetchone=True
    )
    try:
        execute_db("DELETE FROM Consumos WHERE consumo_id = %s", (consumo_id,))
        flash('Consumo eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar consumo: {e}', 'danger')

    if consumo and request.referrer and 'reservas' in request.referrer:
        return redirect(url_for('reservas.detalle', reserva_id=consumo['reserva_id']))
    return redirect(url_for('consumos.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_consumo():
    reserva_id  = request.form.get('reserva_id')
    servicio_id = request.form.get('servicio_id')
    cantidad    = request.form.get('cantidad', 1)
    fecha       = request.form.get('fecha')
    subtotal    = request.form.get('subtotal', 0)

    errores = recolectar_errores(
        None if reserva_id  else 'La reserva es obligatoria.',
        None if servicio_id else 'El servicio es obligatorio.',
        None if fecha       else 'La fecha es obligatoria.',
        validar_entero_positivo(cantidad, 'Cantidad', min_val=1),
        validar_numero_positivo(subtotal, 'Subtotal')
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        execute_db(
            """
            INSERT INTO Consumos (reserva_id, servicio_id, cantidad, fecha, subtotal)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (reserva_id, servicio_id, cantidad, fecha, subtotal)
        )
        flash('Consumo registrado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al registrar consumo: {e}', 'danger')

    return redirect(url_for('reservas.detalle', reserva_id=reserva_id))