# Hotel EDEN - Sistema de Gestión Hotelera

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Flask](https://img.shields.io/badge/Flask-Backend-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)
![Flyway](https://img.shields.io/badge/Flyway-Migrations-CC0200)



## Características Principales

* **Arquitectura MVC:** Separación clara entre rutas (controladores), modelos de base de datos y vistas (plantillas Jinja2).
* **Control de Acceso Basado en Roles (RBAC):** Vistas y permisos diferenciados para Administración, Recepción, Gerencia y Clientes mediante decoradores personalizados (`@staff_required`, `@cliente_required`).
* **Seguridad Avanzada:**
  * Hasheo seguro de contraseñas utilizando `Werkzeug.security`.
  * Prevención de ataques de fuerza bruta (bloqueo automático de IP y usuario tras múltiples intentos fallidos).
  * Control estricto de sesiones con expiración diferenciada por tipo de usuario.
* **Trazabilidad:** Registro automatizado de accesos y movimientos (logs) en la base de datos.
* **Base de Datos Normalizada:** Esquema relacional robusto en PostgreSQL con triggers y restricciones de integridad.

## Stack Tecnológico

* **Backend:** Python, Flask
* **Base de Datos:** PostgreSQL 17
* **Frontend:** HTML5, CSS3, Jinja2
* **Infraestructura:** Docker, Docker Compose
* **Migraciones de BD:** Flyway

## Credenciales de Prueba (Accesos al Sistema)

Una vez levantado el proyecto, puedes ingresar al panel administrativo (`http://localhost:5000/`) utilizando cualquiera de los siguientes usuarios de prueba. Cada uno tiene un nivel de acceso diferente configurado mediante decoradores de roles:

| Rol | Usuario | Contraseña | Permisos / Nivel de Acceso |
| :--- | :--- | :--- | :--- |
| **Administración** | `admin` | `admin123` | Acceso total al sistema, configuraciones y todos los módulos. |
| **Usuario** | `carlos_r` | `hash123` | Cliente

*Nota: Todas las contraseñas están encriptadas en la base de datos utilizando `Werkzeug.security` para simular un entorno de producción real.*