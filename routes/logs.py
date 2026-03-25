from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from db import query_db, execute_db
from routes.auth_helpers import staff_required
import csv
import io

logs_bp = Blueprint('logs', __name__)

# ─────────────────────────────────────────
#  LISTAR LOGS
# ─────────────────────────────────────────
@logs_bp.route('/admin/logs')
@staff_required
def listar():
    usuario_id = request.args.get('usuario_id', '')
    fecha      = request.args.get('fecha', '')
    exitoso    = request.args.get('exitoso', '')

    sql = """
        SELECT l.*, u.username
        FROM LogsAcceso l
        JOIN UsuariosSistema u ON l.usuario_id = u.usuario_id
        WHERE 1=1
    """
    params = []

    if usuario_id:
        sql += " AND l.usuario_id = %s"
        params.append(usuario_id)
    if fecha:
        sql += " AND DATE(l.fecha_hora) = %s"
        params.append(fecha)
    if exitoso != '':
        sql += " AND l.exitoso = %s"
        params.append(exitoso == 'true')

    sql += " ORDER BY l.fecha_hora DESC"

    logs     = query_db(sql, params)
    usuarios = query_db(
        "SELECT usuario_id, username FROM UsuariosSistema ORDER BY username"
    )

    # Resumen del día
    resumen_hoy = query_db(
        """
        SELECT
            COUNT(*) FILTER (WHERE exitoso = TRUE)  AS exitosos,
            COUNT(*) FILTER (WHERE exitoso = FALSE) AS fallidos,
            COUNT(*) AS total
        FROM LogsAcceso
        WHERE DATE(fecha_hora) = CURRENT_DATE
        """,
        fetchone=True
    )

    # Últimos 5 accesos
    ultimos = query_db(
        """
        SELECT l.*, u.username
        FROM LogsAcceso l
        JOIN UsuariosSistema u ON l.usuario_id = u.usuario_id
        ORDER BY l.fecha_hora DESC
        LIMIT 5
        """
    )

    return render_template(
        'admin/logs/listar.html',
        logs           = logs,
        usuarios       = usuarios,
        filtro_usuario = usuario_id,
        filtro_fecha   = fecha,
        filtro_exitoso = exitoso,
        resumen_hoy    = resumen_hoy,
        ultimos        = ultimos
    )


# ─────────────────────────────────────────
#  LIMPIAR LOGS ANTIGUOS
# ─────────────────────────────────────────
@logs_bp.route('/admin/logs/limpiar', methods=['POST'])
@staff_required
def limpiar():
    dias = int(request.form.get('dias', 30))
    try:
        execute_db(
            "DELETE FROM LogsAcceso WHERE fecha_hora < NOW() - INTERVAL '%s days'",
            (dias,)
        )
        flash(f'Logs de más de {dias} días eliminados correctamente.', 'success')
    except Exception as e:
        flash(f'Error al limpiar logs: {e}', 'danger')
    return redirect(url_for('logs.listar'))


# ─────────────────────────────────────────
#  EXPORTAR A CSV
# ─────────────────────────────────────────
@logs_bp.route('/admin/logs/exportar')
@staff_required
def exportar():
    logs = query_db(
        """
        SELECT l.log_id, u.username, l.accion, l.fecha_hora,
               l.ip_origen, l.exitoso
        FROM LogsAcceso l
        JOIN UsuariosSistema u ON l.usuario_id = u.usuario_id
        ORDER BY l.fecha_hora DESC
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Encabezados
    writer.writerow(['ID', 'Usuario', 'Acción', 'Fecha y Hora', 'IP Origen', 'Exitoso'])

    # Filas
    for log in logs:
        writer.writerow([
            log['log_id'],
            log['username'],
            log['accion'],
            log['fecha_hora'],
            log['ip_origen'] or '—',
            'Sí' if log['exitoso'] else 'No'
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=logs_acceso.csv'
        }
    )