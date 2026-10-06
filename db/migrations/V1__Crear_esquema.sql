-- ENUMs
CREATE TYPE tipo_habitacion AS ENUM (
  'individual', 'doble estándar', 'doble twin', 'triple', 
  'cuadruple', 'suite junior', 'suite ejecutiva', 'apartamento'
);

CREATE TYPE estado_habitacion AS ENUM (
  'disponible', 'ocupada', 'reservada', 'mantenimiento', 
  'limpieza', 'bloqueada'
);

CREATE TYPE estado_reserva AS ENUM (
  'pendiente', 'confirmada', 'cancelada', 'check-in', 
  'check-out', 'finalizada', 'no-show'        
);

CREATE TYPE tipo_mascota AS ENUM (
  'perro', 'gato', 'ave', 'conejo', 'reptil', 'otro'
);

CREATE TYPE metodo_pago AS ENUM (
  'efectivo', 'tarjeta débito', 'tarjeta crédito', 
  'transferencia bancaria', 'paypal'
);

CREATE TYPE tipo_servicio AS ENUM (
  'spa', 'restaurante', 'bar', 'transporte', 'lavandería', 
  'gimnasio', 'room service', 'Guarderia'
);

CREATE TYPE rol_empleado AS ENUM (
  'recepción', 'limpieza', 'mantenimiento', 'administración', 
  'gerencia', 'seguridad', 'concierge', 'cocina', 
  'atención al cliente', 'cliente'
);

-- Tablas
CREATE TABLE Hoteles (
    hotel_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    direccion TEXT,
    ciudad VARCHAR(50),
    pais VARCHAR(50),
    telefono VARCHAR(20),
    email_contacto VARCHAR(100),
    categoria VARCHAR(20)
);

CREATE TABLE Clientes (
    cliente_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50),
    apellido VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    telefono VARCHAR(20),
    direccion TEXT,
    fecha_registro DATE DEFAULT CURRENT_DATE,
    fecha_nacimiento DATE
);

CREATE TABLE Habitaciones (
    habitacion_id SERIAL PRIMARY KEY,
    hotel_id INT REFERENCES Hoteles(hotel_id) ON DELETE CASCADE,
    numero VARCHAR(10),
    tipo tipo_habitacion,
    capacidad_adultos INT,
    capacidad_menores INT,
    permite_mascotas BOOLEAN,
    precio_base NUMERIC(10,2),
    estado estado_habitacion,
    piso INT,
    CONSTRAINT unique_habitacion_por_hotel UNIQUE (hotel_id, numero)
);

CREATE TABLE Reservas (
    reserva_id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES Clientes(cliente_id),
    habitacion_id INT REFERENCES Habitaciones(habitacion_id),
    fecha_inicio DATE,
    fecha_fin DATE,
    num_adultos INT,
    num_menores INT,
    num_mascotas INT,
    estado estado_reserva,
    total NUMERIC(10,2),
    CONSTRAINT chk_fechas_reserva CHECK (fecha_fin > fecha_inicio)
);

CREATE TABLE Mascotas (
    mascota_id SERIAL PRIMARY KEY,
    reserva_id INT REFERENCES Reservas(reserva_id) ON DELETE CASCADE,
    tipo tipo_mascota,
    nombre VARCHAR(50),
    peso NUMERIC(5,2),
    observaciones TEXT
);

CREATE TABLE Pagos (
    pago_id SERIAL PRIMARY KEY,
    reserva_id INT REFERENCES Reservas(reserva_id) ON DELETE CASCADE,
    monto NUMERIC(10,2),
    fecha_pago DATE,
    metodo metodo_pago,
    tipo VARCHAR(20) DEFAULT 'pago' CHECK (tipo IN ('pago', 'reembolso')),
    notas TEXT,
    CONSTRAINT chk_monto_pago CHECK (monto > 0)
);

CREATE TABLE Servicios (
    servicio_id SERIAL PRIMARY KEY,
    nombre tipo_servicio,
    descripcion TEXT,
    precio NUMERIC(10,2)
);

CREATE TABLE Consumos (
    consumo_id SERIAL PRIMARY KEY,
    reserva_id INT REFERENCES Reservas(reserva_id) ON DELETE CASCADE,
    servicio_id INT REFERENCES Servicios(servicio_id),
    cantidad INT,
    fecha DATE,
    subtotal NUMERIC(10,2)
);

CREATE TABLE Promociones (
    promo_id SERIAL PRIMARY KEY,
    hotel_id INT REFERENCES Hoteles(hotel_id),
    descripcion TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    descuento NUMERIC(5,2)
);

CREATE TABLE OpinionesClientes (
    opinion_id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES Clientes(cliente_id),
    hotel_id INT REFERENCES Hoteles(hotel_id),
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    comentario TEXT,
    fecha DATE
);

CREATE TABLE Roles (
    rol_id SERIAL PRIMARY KEY,
    nombre rol_empleado UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE Empleados (
    empleado_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    rol_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_rol_empleado FOREIGN KEY (rol_id)
        REFERENCES Roles(rol_id) ON DELETE CASCADE
);

CREATE TABLE Turnos (
    turno_id SERIAL PRIMARY KEY,
    empleado_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    fecha_fin DATE NOT NULL,
    hora_fin TIME NOT NULL,
    CONSTRAINT chk_turno_valido CHECK (
        (fecha_fin > fecha_inicio)
        OR (fecha_fin = fecha_inicio AND hora_fin > hora_inicio)
    ),
    CONSTRAINT fk_empleado_turno FOREIGN KEY (empleado_id)
        REFERENCES Empleados(empleado_id) ON DELETE CASCADE
);

CREATE TABLE UsuariosSistema (
    usuario_id SERIAL PRIMARY KEY,
    empleado_id INT NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_empleado_usuario FOREIGN KEY (empleado_id)
        REFERENCES Empleados(empleado_id) ON DELETE CASCADE,
    CONSTRAINT fk_rol_usuario FOREIGN KEY (rol_id)
        REFERENCES Roles(rol_id) ON DELETE CASCADE
);

CREATE TABLE LogsAcceso (
    log_id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    accion TEXT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origen VARCHAR(45),
    exitoso BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_usuario_log FOREIGN KEY (usuario_id)
        REFERENCES UsuariosSistema(usuario_id) ON DELETE CASCADE
);

CREATE TABLE IntentosLogin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    ip_origen VARCHAR(45),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(10) DEFAULT 'cliente'
);