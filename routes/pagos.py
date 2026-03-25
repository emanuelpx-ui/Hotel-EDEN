from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from datetime import date
from routes.validators import validar_numero_positivo, recolectar_errores

pagos_bp = Blueprint('pagos', __name__)

METODOS_PAGO = [
    'efectivo', 'tarjeta débito', 'tarjeta crédito',
    'transferencia bancaria', 'paypal'
]

# ─────────────────────────────────────────
#  LISTAR PAGOS
# ─────────────────────────────────────────
@pagos_bp.route('/admin/pagos')
@staff_required
def listar():
    metodo = request.args.get('metodo', '')
    tipo   = request.args.get('tipo', '')
    fecha  = request.args.get('fecha', '')

    sql = """
        SELECT p.*, 
               r.reserva_id,
               c.nombre || ' ' || c.apellido AS cliente,
               h.numero AS habitacion,
               ht.nombre AS hotel
        FROM Pagos p
        JOIN Reservas r     ON p.reserva_id    = r.reserva_id
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE 1=1
    """
    params = []

    if metodo:
        sql += " AND p.metodo = %s"
        params.append(metodo)
    if tipo:
        sql += " AND p.tipo = %s"
        params.append(tipo)
    if fecha:
        sql += " AND p.fecha_pago = %s"
        params.append(fecha)

    sql += " ORDER BY p.fecha_pago DESC, p.pago_id DESC"

    pagos = query_db(sql, params)

    # Totales
    total_ingresos  = sum(p['monto'] for p in pagos if p['tipo'] == 'pago')
    total_reembolsos = sum(p['monto'] for p in pagos if p['tipo'] == 'reembolso')
    balance = total_ingresos - total_reembolsos

    return render_template(
        'admin/pagos/listar.html',
        pagos            = pagos,
        metodos          = METODOS_PAGO,
        filtro_metodo    = metodo,
        filtro_tipo      = tipo,
        filtro_fecha     = fecha,
        total_ingresos   = total_ingresos,
        total_reembolsos = total_reembolsos,
        balance          = balance
    )


# ─────────────────────────────────────────
#  NUEVO PAGO (desde módulo de pagos)
# ─────────────────────────────────────────
@pagos_bp.route('/admin/pagos/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    reservas = query_db(
        """
        SELECT r.reserva_id,
               c.nombre || ' ' || c.apellido AS cliente,
               h.numero AS habitacion,
               ht.nombre AS hotel,
               r.total
        FROM Reservas r
        JOIN Clientes c     ON r.cliente_id    = c.cliente_id
        JOIN Habitaciones h ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht     ON h.hotel_id      = ht.hotel_id
        WHERE r.estado NOT IN ('cancelada', 'finalizada')
        ORDER BY r.reserva_id DESC
        """
    )

    if request.method == 'POST':
        return _guardar_pago()

    return render_template(
        'admin/pagos/form.html',
        reservas   = reservas,
        metodos    = METODOS_PAGO,
        reserva_id = None,
        today      = date.today()
    )


# ─────────────────────────────────────────
#  NUEVO PAGO (desde detalle de reserva)
# ─────────────────────────────────────────
@pagos_bp.route('/admin/pagos/nuevo/<int:reserva_id>', methods=['GET', 'POST'])
@staff_required
def nuevo_desde_reserva(reserva_id):
    reserva = query_db(
        """
        SELECT r.reserva_id,
               c.nombre || ' ' || c.apellido AS cliente,
               h.numero AS habitacion,
               ht.nombre AS hotel,
               r.total
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
        return redirect(url_for('pagos.listar'))

    if request.method == 'POST':
        return _guardar_pago()

    return render_template(
        'admin/pagos/form.html',
        reservas   = [reserva],
        metodos    = METODOS_PAGO,
        reserva_id = reserva_id,
        today      = date.today()
    )


# ─────────────────────────────────────────
#  ELIMINAR PAGO
# ─────────────────────────────────────────
@pagos_bp.route('/admin/pagos/<int:pago_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(pago_id):
    # Obtener reserva_id antes de eliminar para redirigir
    pago = query_db(
        "SELECT reserva_id FROM Pagos WHERE pago_id = %s",
        (pago_id,), fetchone=True
    )
    try:
        execute_db("DELETE FROM Pagos WHERE pago_id = %s", (pago_id,))
        flash('Pago eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar pago: {e}', 'danger')

    # Redirigir al detalle de la reserva si viene de ahí
    if pago and request.referrer and 'reservas' in request.referrer:
        return redirect(url_for('reservas.detalle', reserva_id=pago['reserva_id']))
    return redirect(url_for('pagos.listar'))


# ─────────────────────────────────────────
#  REEMBOLSO
# ─────────────────────────────────────────
@pagos_bp.route('/admin/pagos/<int:pago_id>/reembolso', methods=['POST'])
@staff_required
def reembolso(pago_id):
    pago = query_db(
        "SELECT * FROM Pagos WHERE pago_id = %s",
        (pago_id,), fetchone=True
    )
    if not pago:
        flash('Pago no encontrado.', 'danger')
        return redirect(url_for('pagos.listar'))

    notas = request.form.get('notas', 'Reembolso').strip()

    try:
        execute_db(
            """
            INSERT INTO Pagos (reserva_id, monto, fecha_pago, metodo, tipo, notas)
            VALUES (%s, %s, CURRENT_DATE, %s, 'reembolso', %s)
            """,
            (pago['reserva_id'], pago['monto'], pago['metodo'], notas)
        )
        flash(f'Reembolso de ${pago["monto"]} registrado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al registrar reembolso: {e}', 'danger')

    return redirect(url_for('reservas.detalle', reserva_id=pago['reserva_id']))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_pago():
    reserva_id = request.form.get('reserva_id')
    monto      = request.form.get('monto', '').strip()
    fecha_pago = request.form.get('fecha_pago', '').strip()
    metodo     = request.form.get('metodo')
    notas      = request.form.get('notas', '').strip()

    errores = recolectar_errores(
        None if reserva_id else 'La reserva es obligatoria.',
        None if fecha_pago else 'La fecha de pago es obligatoria.',
        None if metodo     else 'El método de pago es obligatorio.',
        validar_numero_positivo(monto, 'Monto')
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        execute_db(
            """
            INSERT INTO Pagos (reserva_id, monto, fecha_pago, metodo, tipo, notas)
            VALUES (%s, %s, %s, %s, 'pago', %s)
            """,
            (reserva_id, monto, fecha_pago, metodo, notas or None)
        )
        flash('Pago registrado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al registrar pago: {e}', 'danger')

    return redirect(url_for('reservas.detalle', reserva_id=reserva_id))