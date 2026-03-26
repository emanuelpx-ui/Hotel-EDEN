from flask import Flask, redirect, url_for, session
from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv(encoding='utf-8')

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.clientes import clientes_bp
from routes.habitaciones import habitaciones_bp
from routes.reservas import reservas_bp
from routes.pagos import pagos_bp
from routes.servicios import servicios_bp
from routes.consumos import consumos_bp
from routes.empleados import empleados_bp
from routes.turnos import turnos_bp
from routes.logs import logs_bp
from routes.public import public_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret_key')

# Sesión expira en X minutos de inactividad
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    minutes=int(os.getenv('SESSION_TIMEOUT', 30))
)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CSRF Protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

from flask import g
import secrets

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(habitaciones_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(pagos_bp)
app.register_blueprint(servicios_bp)
app.register_blueprint(consumos_bp)
app.register_blueprint(empleados_bp)
app.register_blueprint(turnos_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(public_bp)

@app.route('/')
def index():
    return redirect('public/index')

if __name__ == '__main__':
    app.run(debug=True)
