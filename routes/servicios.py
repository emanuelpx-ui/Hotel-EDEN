from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_db, execute_db
from routes.auth_helpers import staff_required
from routes.validators import (validar_texto, validar_numero_positivo,
                                recolectar_errores)

servicios_bp = Blueprint('servicios', __name__)

TIPOS_SERVICIO = [
    'spa', 'restaurante', 'bar', 'transporte',
    'lavandería', 'gimnasio', 'room service', 'Guarderia'
]

# ─────────────────────────────────────────
#  LISTAR SERVICIOS
# ─────────────────────────────────────────
@servicios_bp.route('/admin/servicios')
@staff_required
def listar():
    servicios = query_db(
        """
        SELECT s.*,
               COUNT(c.consumo_id)        AS total_consumos,
               COALESCE(SUM(c.subtotal), 0) AS ingresos_total
        FROM Servicios s
        LEFT JOIN Consumos c ON s.servicio_id = c.servicio_id
        GROUP BY s.servicio_id
        ORDER BY ingresos_total DESC
        """
    )

    # Servicio más popular
    mas_popular = query_db(
        """
        SELECT s.nombre, COUNT(c.consumo_id) AS total
        FROM Consumos c
        JOIN Servicios s ON c.servicio_id = s.servicio_id
        GROUP BY s.nombre
        ORDER BY total DESC
        LIMIT 1
        """,
        fetchone=True
    )

    # Total ingresos por servicios
    total_ingresos = query_db(
        "SELECT COALESCE(SUM(subtotal), 0) AS total FROM Consumos",
        fetchone=True
    )['total']

    return render_template(
        'admin/servicios/listar.html',
        servicios      = servicios,
        mas_popular    = mas_popular,
        total_ingresos = total_ingresos,
        tipos          = TIPOS_SERVICIO
    )


# ─────────────────────────────────────────
#  NUEVO SERVICIO
# ─────────────────────────────────────────
@servicios_bp.route('/admin/servicios/nuevo', methods=['GET', 'POST'])
@staff_required
def nuevo():
    if request.method == 'POST':
        return _guardar_servicio(None)
    return render_template(
        'admin/servicios/form.html',
        servicio = None,
        tipos    = TIPOS_SERVICIO
    )


# ─────────────────────────────────────────
#  EDITAR SERVICIO
# ─────────────────────────────────────────
@servicios_bp.route('/admin/servicios/<int:servicio_id>/editar', methods=['GET', 'POST'])
@staff_required
def editar(servicio_id):
    servicio = query_db(
        "SELECT * FROM Servicios WHERE servicio_id = %s",
        (servicio_id,), fetchone=True
    )
    if not servicio:
        flash('Servicio no encontrado.', 'danger')
        return redirect(url_for('servicios.listar'))

    if request.method == 'POST':
        return _guardar_servicio(servicio_id)

    return render_template(
        'admin/servicios/form.html',
        servicio = servicio,
        tipos    = TIPOS_SERVICIO
    )


# ─────────────────────────────────────────
#  ELIMINAR SERVICIO
# ─────────────────────────────────────────
@servicios_bp.route('/admin/servicios/<int:servicio_id>/eliminar', methods=['POST'])
@staff_required
def eliminar(servicio_id):
    try:
        execute_db("DELETE FROM Servicios WHERE servicio_id = %s", (servicio_id,))
        flash('Servicio eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'danger')
    return redirect(url_for('servicios.listar'))


# ─────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────
def _guardar_servicio(servicio_id):
    nombre      = request.form.get('nombre')
    descripcion = request.form.get('descripcion', '').strip()
    precio      = request.form.get('precio', 0)

    errores = recolectar_errores(
        None if nombre else 'El tipo de servicio es obligatorio.',
        validar_numero_positivo(precio, 'Precio')
    )

    if errores:
        for e in errores:
            flash(e, 'warning')
        return redirect(request.referrer)

    try:
        if servicio_id is None:
            execute_db(
                """
                INSERT INTO Servicios (nombre, descripcion, precio)
                VALUES (%s, %s, %s)
                """,
                (nombre, descripcion or None, precio)
            )
            flash('Servicio registrado correctamente.', 'success')
        else:
            execute_db(
                """
                UPDATE Servicios
                SET nombre=%s, descripcion=%s, precio=%s
                WHERE servicio_id=%s
                """,
                (nombre, descripcion or None, precio, servicio_id)
            )
            flash('Servicio actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al guardar servicio: {e}', 'danger')

    return redirect(url_for('servicios.listar'))