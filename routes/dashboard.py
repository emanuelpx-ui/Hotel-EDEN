from flask import Blueprint, render_template
from db import query_db
from routes.auth_helpers import staff_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin/dashboard')
@staff_required
def index():

    # Reservas de hoy
    reservas_hoy = query_db(
        "SELECT COUNT(*) AS total FROM Reservas WHERE fecha_inicio = CURRENT_DATE",
        fetchone=True
    )['total']

    # Reservas activas (confirmadas + check-in)
    reservas_activas = query_db(
        """
        SELECT COUNT(*) AS total FROM Reservas
        WHERE estado IN ('confirmada', 'check-in')
        """,
        fetchone=True
    )['total']

    # Clientes hospedados ahora (estado check-in)
    hospedados_ahora = query_db(
        """
        SELECT COUNT(*) AS total FROM Reservas
        WHERE estado = 'check-in'
        """,
        fetchone=True
    )['total']

    # Ingresos del mes
    ingresos_mes = query_db(
        """
        SELECT COALESCE(SUM(monto), 0) AS total FROM Pagos
        WHERE DATE_TRUNC('month', fecha_pago) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        fetchone=True
    )['total']

    # Total clientes registrados
    total_clientes = query_db(
        "SELECT COUNT(*) AS total FROM Clientes",
        fetchone=True
    )['total']

    # Cancelaciones del mes
    cancelaciones = query_db(
        """
        SELECT COUNT(*) AS total FROM Reservas
        WHERE estado = 'cancelada'
        AND DATE_TRUNC('month', fecha_inicio) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        fetchone=True
    )['total']

    # Total reservas del mes (para calcular porcentaje)
    total_reservas_mes = query_db(
        """
        SELECT COUNT(*) AS total FROM Reservas
        WHERE DATE_TRUNC('month', fecha_inicio) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        fetchone=True
    )['total']

    # Porcentaje de cancelaciones
    if total_reservas_mes > 0:
        porc_cancelaciones = round((cancelaciones / total_reservas_mes) * 100, 1)
    else:
        porc_cancelaciones = 0

    # Distribución de habitaciones para gráfica
    habitaciones = query_db(
        """
        SELECT estado, COUNT(*) AS total
        FROM Habitaciones
        GROUP BY estado
        """
    )

    # Convertir a formato para Chart.js
    labels_hab   = [row['estado'].capitalize() for row in habitaciones]
    valores_hab  = [row['total'] for row in habitaciones]

    return render_template(
        'admin/dashboard.html',
        reservas_hoy       = reservas_hoy,
        reservas_activas   = reservas_activas,
        hospedados_ahora   = hospedados_ahora,
        ingresos_mes       = ingresos_mes,
        total_clientes     = total_clientes,
        cancelaciones      = cancelaciones,
        porc_cancelaciones = porc_cancelaciones,
        labels_hab         = labels_hab,
        valores_hab        = valores_hab
    )