from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from routes.validators import (validar_texto, validar_email,
                                validar_telefono, recolectar_errores)

clientes_bp = Blueprint('clientes', __name__)

# ─────────────────────────────────────────
#  LISTAR CLIENTES
# ─────────────────────────────────────────
@clientes_bp.route('/admin/clientes')
@staff_required
def listar():
    busqueda = request.args.get('q', '').strip()

    if busqueda:
        clientes = query_db(
            """
            SELECT * FROM Clientes
            WHERE nombre ILIKE %s OR apellido ILIKE %s OR email ILIKE %s
            ORDER BY apellido ASC
            """,
            (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%')
        )
    else:
        clientes = query_db("SELECT * FROM Clientes ORDER BY apellido ASC")

    return render_template('admin/clientes/listar.html',
                           clientes=clientes,
                           busqueda=busqueda)


# ─────────────────────────────────────────
#  NUEVO CLIENTE
# ─────────────────────────────────────────
@clientes_bp.route('/admin/clientes/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    if request.method == 'POST':
        return _guardar_cliente(None)
    return render_template('admin/clientes/form.html', cliente=None)


# ─────────────────────────────────────────
#  EDITAR CLIENTE
# ─────────────────────────────────────────
@clientes_bp.route('/admin/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
@staff_required
def editar(cliente_id):
    cliente = query_db(
        "SELECT * FROM Clientes WHERE cliente_id = %s",
        (cliente_id,), fetchone=True
    )
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clientes.listar'))

    if request.method == 'POST':
        return _guardar_cliente(cliente_id)

    return render_template('admin/clientes/form.html', cliente=cliente)


# ─────────────────────────────────────────
#  DETALLE + HISTORIAL DE RESERVAS
# ─────────────────────────────────────────
@clientes_bp.route('/admin/clientes/<int:cliente_id>')
@staff_required
def detalle(cliente_id):
    cliente = query_db(
        "SELECT * FROM Clientes WHERE cliente_id = %s",
        (cliente_id,), fetchone=True
    )
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clientes.listar'))

    reservas = query_db(
        """
        SELECT r.reserva_id, r.fecha_inicio, r.fecha_fin, r.estado, r.total,
               r.num_adultos, r.num_menores, r.num_mascotas,
               h.numero AS habitacion, h.tipo AS tipo_hab,
               ht.nombre AS hotel
        FROM Reservas r
        JOIN Habitaciones h  ON r.habitacion_id = h.habitacion_id
        JOIN Hoteles ht      ON h.hotel_id = ht.hotel_id
        WHERE r.cliente_id = %s
        ORDER BY r.fecha_inicio DESC
        """,
        (cliente_id,)
    )

    total_gastado = query_db(
        """
        SELECT COALESCE(SUM(p.monto), 0) AS total
        FROM Pagos p
        JOIN Reservas r ON p.reserva_id = r.reserva_id
        WHERE r.cliente_id = %s
        """,
        (cliente_id,), fetchone=True
    )['total']

    return render_template('admin/clientes/detalle.html',
                           cliente=cliente,
                           reservas=reservas,
                           total_gastado=total_gastado)


# ─────────────────────────────────────────
#  ELIMINAR CLIENTE
# ─────────────────────────────────────────
@clientes_bp.route('/admin/clientes/<int:cliente_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(cliente_id):
    try:
        execute_db("DELETE FROM Clientes WHERE cliente_id = %s", (cliente_id,))
        flash('Cliente eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar cliente: {e}', 'danger')
    return redirect(url_for('clientes.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_cliente(cliente_id):
    nombre    = request.form.get('nombre', '').strip()
    apellido  = request.form.get('apellido', '').strip()
    email     = request.form.get('email', '').strip()
    telefono  = request.form.get('telefono', '').strip()
    direccion = request.form.get('direccion', '').strip()
    fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()

    errores = recolectar_errores(
        validar_texto(nombre,   'Nombre',   min_len=2, max_len=50),
        validar_texto(apellido, 'Apellido', min_len=2, max_len=50),
        validar_email(email),
        validar_telefono(telefono)
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        if cliente_id is None:
            execute_db(
                """
                INSERT INTO Clientes
                    (nombre, apellido, email, telefono, direccion, fecha_nacimiento)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (nombre, apellido, email or None, telefono or None,
                 direccion or None, fecha_nacimiento or None)
            )
            flash('Cliente registrado correctamente.', 'success')
        else:
            execute_db(
                """
                UPDATE Clientes
                SET nombre=%s, apellido=%s, email=%s,
                    telefono=%s, direccion=%s, fecha_nacimiento=%s
                WHERE cliente_id=%s
                """,
                (nombre, apellido, email or None, telefono or None,
                 direccion or None, fecha_nacimiento or None, cliente_id)
            )
            flash('Cliente actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar cliente: {e}', 'danger')

    return redirect(url_for('clientes.listar'))