from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from routes.validators import (validar_numero_positivo, validar_entero_positivo,
                                validar_fechas, recolectar_errores)

reservas_bp = Blueprint('reservas', __name__)

ESTADOS_RESERVA = [
    'pendiente', 'confirmada', 'cancelada',
    'check-in', 'check-out', 'finalizada', 'no-show'
]

# ─────────────────────────────────────────
#  LISTAR RESERVAS
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas')
@staff_required
def listar():
    estado       = request.args.get('estado', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin    = request.args.get('fecha_fin', '')

    sql = """
        SELECT r.reserva_id, r.fecha_inicio, r.fecha_fin, r.estado, r.total,
               r.num_adultos, r.num_menores, r.num_mascotas,
               c.nombre || ' ' || c.apellido AS cliente,
               c.cliente_id,
               h.numero AS habitacion, h.tipo AS tipo_hab,
               ht.nombre AS hotel
        FROM Reservas r
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE 1=1
    """
    params = []

    if estado:
        sql += " AND r.estado = %s"
        params.append(estado)
    if fecha_inicio:
        sql += " AND r.fecha_inicio >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        sql += " AND r.fecha_fin <= %s"
        params.append(fecha_fin)

    sql += " ORDER BY r.fecha_inicio DESC"

    reservas = query_db(sql, params)

    return render_template(
        'admin/reservas/listar.html',
        reservas      = reservas,
        estados       = ESTADOS_RESERVA,
        filtro_estado = estado,
        filtro_inicio = fecha_inicio,
        filtro_fin    = fecha_fin
    )


# ─────────────────────────────────────────
#  NUEVA RESERVA
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas/nueva', methods=['GET', 'POST'])
@staff_required
def nueva():
    clientes     = query_db(
        "SELECT cliente_id, nombre, apellido FROM Clientes ORDER BY apellido"
    )
    habitaciones = query_db(
        """
        SELECT h.habitacion_id, h.numero, h.tipo, h.precio_base,
               h.capacidad_adultos, h.capacidad_menores, h.permite_mascotas,
               ht.nombre AS hotel
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        WHERE h.estado = 'disponible'
        ORDER BY ht.nombre, h.numero
        """
    )

    if request.method == 'POST':
        return _guardar_reserva(None)

    return render_template(
        'admin/reservas/form.html',
        reserva      = None,
        clientes     = clientes,
        habitaciones = habitaciones,
        estados      = ESTADOS_RESERVA
    )


# ─────────────────────────────────────────
#  EDITAR RESERVA
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas/<int:reserva_id>/editar', methods=['GET', 'POST'])
@staff_required
def editar(reserva_id):
    reserva = query_db(
        "SELECT * FROM Reservas WHERE reserva_id = %s",
        (reserva_id,), fetchone=True
    )
    if not reserva:
        flash('Reserva no encontrada.', 'danger')
        return redirect(url_for('reservas.listar'))

    clientes     = query_db(
        "SELECT cliente_id, nombre, apellido FROM Clientes ORDER BY apellido"
    )
    habitaciones = query_db(
        """
        SELECT h.habitacion_id, h.numero, h.tipo, h.precio_base,
               h.capacidad_adultos, h.capacidad_menores, h.permite_mascotas,
               ht.nombre AS hotel
        FROM Habitaciones h
        JOIN Hoteles ht ON h.hotel_id = ht.hotel_id
        ORDER BY ht.nombre, h.numero
        """
    )

    if request.method == 'POST':
        return _guardar_reserva(reserva_id)

    return render_template(
        'admin/reservas/form.html',
        reserva      = reserva,
        clientes     = clientes,
        habitaciones = habitaciones,
        estados      = ESTADOS_RESERVA
    )


# ─────────────────────────────────────────
#  DETALLE RESERVA
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas/<int:reserva_id>')
@staff_required
def detalle(reserva_id):
    reserva = query_db(
        """
        SELECT r.*, 
               c.nombre || ' ' || c.apellido AS cliente,
               c.email, c.telefono, c.cliente_id,
               h.numero AS habitacion, h.tipo AS tipo_hab,
               h.precio_base, h.permite_mascotas,
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
        return redirect(url_for('reservas.listar'))

    # Pagos de esta reserva
    pagos = query_db(
        """
        SELECT * FROM Pagos
        WHERE reserva_id = %s
        ORDER BY fecha_pago DESC
        """,
        (reserva_id,)
    )

    # Total pagado
    total_pagado = sum(p['monto'] for p in pagos)

    # Mascotas de esta reserva
    mascotas = query_db(
        "SELECT * FROM Mascotas WHERE reserva_id = %s",
        (reserva_id,)
    )

    # Consumos de esta reserva
    consumos = query_db(
        """
        SELECT co.*, s.nombre AS servicio
        FROM Consumos co
        JOIN Servicios s ON co.servicio_id = s.servicio_id
        WHERE co.reserva_id = %s
        ORDER BY co.fecha DESC
        """,
        (reserva_id,)
    )

    saldo_pendiente = float(reserva['total']) - float(total_pagado)

    return render_template(
        'admin/reservas/detalle.html',
        reserva         = reserva,
        pagos           = pagos,
        total_pagado    = total_pagado,
        saldo_pendiente = saldo_pendiente,
        mascotas        = mascotas,
        consumos        = consumos,
        estados         = ESTADOS_RESERVA
    )


# ─────────────────────────────────────────
#  CHECK-IN / CHECK-OUT RÁPIDO
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas/<int:reserva_id>/estado', methods=['POST'])
@staff_required
def cambiar_estado(reserva_id):
    nuevo_estado = request.form.get('estado')
    if nuevo_estado not in ESTADOS_RESERVA:
        flash('Estado no válido.', 'danger')
        return redirect(url_for('reservas.listar'))
    try:
        execute_db(
            "UPDATE Reservas SET estado = %s WHERE reserva_id = %s",
            (nuevo_estado, reserva_id)
        )
        # Si es check-in, marcar habitación como ocupada
        if nuevo_estado == 'check-in':
            execute_db(
                """
                UPDATE Habitaciones SET estado = 'ocupada'
                WHERE habitacion_id = (
                    SELECT habitacion_id FROM Reservas WHERE reserva_id = %s
                )
                """,
                (reserva_id,)
            )
        # Si es check-out o finalizada, marcar habitación como limpieza
        elif nuevo_estado in ('check-out', 'finalizada'):
            execute_db(
                """
                UPDATE Habitaciones SET estado = 'limpieza'
                WHERE habitacion_id = (
                    SELECT habitacion_id FROM Reservas WHERE reserva_id = %s
                )
                """,
                (reserva_id,)
            )
        # Si se cancela, marcar habitación como disponible
        elif nuevo_estado == 'cancelada':
            execute_db(
                """
                UPDATE Habitaciones SET estado = 'disponible'
                WHERE habitacion_id = (
                    SELECT habitacion_id FROM Reservas WHERE reserva_id = %s
                )
                """,
                (reserva_id,)
            )
        flash(f'Estado actualizado a "{nuevo_estado}".', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('reservas.detalle', reserva_id=reserva_id))


# ─────────────────────────────────────────
#  ELIMINAR RESERVA
# ─────────────────────────────────────────
@reservas_bp.route('/admin/reservas/<int:reserva_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(reserva_id):
    try:
        execute_db("DELETE FROM Reservas WHERE reserva_id = %s", (reserva_id,))
        flash('Reserva eliminada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'danger')
    return redirect(url_for('reservas.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_reserva(reserva_id):
    cliente_id    = request.form.get('cliente_id')
    habitacion_id = request.form.get('habitacion_id')
    fecha_inicio  = request.form.get('fecha_inicio')
    fecha_fin     = request.form.get('fecha_fin')
    num_adultos   = request.form.get('num_adultos', 1)
    num_menores   = request.form.get('num_menores', 0)
    num_mascotas  = request.form.get('num_mascotas', 0)
    estado        = request.form.get('estado', 'pendiente')
    total         = request.form.get('total', 0)

    errores = recolectar_errores(
        None if cliente_id    else 'El cliente es obligatorio.',
        None if habitacion_id else 'La habitación es obligatoria.',
        None if fecha_inicio  else 'La fecha de entrada es obligatoria.',
        None if fecha_fin     else 'La fecha de salida es obligatoria.',
        validar_fechas(fecha_inicio, fecha_fin) if fecha_inicio and fecha_fin else None,
        validar_entero_positivo(num_adultos, 'Número de adultos', min_val=1),
        validar_entero_positivo(num_menores, 'Número de menores', min_val=0),
        validar_entero_positivo(num_mascotas, 'Número de mascotas', min_val=0),
        validar_numero_positivo(total, 'Total') if total else None
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        if reserva_id is None:
            execute_db(
                """
                INSERT INTO Reservas
                    (cliente_id, habitacion_id, fecha_inicio, fecha_fin,
                     num_adultos, num_menores, num_mascotas, estado, total)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (cliente_id, habitacion_id, fecha_inicio, fecha_fin,
                 num_adultos, num_menores, num_mascotas, estado, total)
            )
            execute_db(
                "UPDATE Habitaciones SET estado = 'reservada' WHERE habitacion_id = %s",
                (habitacion_id,)
            )
            flash('Reserva creada correctamente.', 'success')
        else:
            execute_db(
                """
                UPDATE Reservas
                SET cliente_id=%s, habitacion_id=%s, fecha_inicio=%s, fecha_fin=%s,
                    num_adultos=%s, num_menores=%s, num_mascotas=%s, estado=%s, total=%s
                WHERE reserva_id=%s
                """,
                (cliente_id, habitacion_id, fecha_inicio, fecha_fin,
                 num_adultos, num_menores, num_mascotas, estado, total,
                 reserva_id)
            )
            flash('Reserva actualizada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar reserva: {e}', 'danger')

    return redirect(url_for('reservas.listar'))