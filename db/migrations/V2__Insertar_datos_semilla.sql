-- Hoteles
INSERT INTO Hoteles (nombre, direccion, ciudad, pais, telefono, email_contacto, categoria)
VALUES ('Hotel Puebla Centro', 'Av. Reforma #123', 'Puebla', 'México', '2221234567', 'contacto@puebla.com', '4 estrellas'),
       ('Hotel Angelópolis', 'Blvd. Atlixco #456', 'Puebla', 'México', '2229876543', 'info@angelopolis.com', '5 estrellas');

-- Roles (Se corrigió error de sintaxis que existía aquí)
INSERT INTO Roles (nombre, descripcion)
VALUES ('recepción', 'Atiende clientes y gestiona reservas'),
       ('limpieza', 'Encargado de limpieza de habitaciones'),
       ('gerencia', 'Supervisa operaciones del hotel'),
       ('mantenimiento', 'Encargado de reparaciones y mantenimiento general'),
       ('administración', 'Rol con acceso total al sistema'),
       ('seguridad', 'Encargado de la seguridad del hotel'),
       ('concierge', 'Atiende solicitudes especiales de huéspedes'),
       ('cocina', 'Encargado de la preparación de alimentos'),
       ('atención al cliente', 'Brinda soporte y atención a los huéspedes'),
       ('cliente', 'Cliente del hotel con acceso a sus reservas');

-- Clientes
INSERT INTO Clientes (nombre, apellido, email, telefono, direccion)
VALUES ('Juan', 'Pérez', 'juan.perez@mail.com', '2221112233', 'Calle 5 de Mayo #10'),
       ('María', 'López', 'maria.lopez@mail.com', '2224445566', 'Av. Juárez #20');

-- Habitaciones
INSERT INTO Habitaciones (hotel_id, numero, tipo, capacidad_adultos, capacidad_menores, permite_mascotas, precio_base, estado)
VALUES (1, '101', 'doble estándar', 2, 2, TRUE, 1200.00, 'disponible'),
       (2, '102', 'suite ejecutiva', 2, 0, FALSE, 2500.00, 'ocupada'),
       (2, '201', 'individual', 1, 0, FALSE, 800.00, 'disponible');

-- Reservas
INSERT INTO Reservas (cliente_id, habitacion_id, fecha_inicio, fecha_fin, num_adultos, num_menores, num_mascotas, estado, total)
VALUES (1, 1, '2026-03-20', '2026-03-22', 2, 0, 0, 'confirmada', 2400.00),
       (2, 2, '2026-03-25', '2026-03-28', 1, 0, 1, 'pendiente', 2400.00);

-- Pagos
INSERT INTO Pagos (reserva_id, monto, fecha_pago, metodo)
VALUES (1, 2400.00, '2026-03-19', 'tarjeta crédito'),
       (2, 800.00, '2026-03-24', 'efectivo');

-- Servicios
INSERT INTO Servicios (nombre, descripcion, precio)
VALUES ('spa', 'Servicio de spa relajante', 500.00),
       ('restaurante', 'Cena buffet', 300.00);

-- Consumos
INSERT INTO Consumos (reserva_id, servicio_id, cantidad, fecha, subtotal)
VALUES (1, 1, 1, '2026-03-21', 500.00),
       (2, 2, 2, '2026-03-26', 600.00);

-- Mascotas
INSERT INTO Mascotas (reserva_id, tipo, nombre, peso, observaciones)
VALUES (2, 'perro', 'Firulais', 12.5, 'Perro pequeño, amigable');

-- OpinionesClientes
INSERT INTO OpinionesClientes (cliente_id, hotel_id, calificacion, comentario, fecha)
VALUES (1, 1, 5, 'Excelente servicio y atención', '2026-03-23'),
       (2, 2, 4, 'Muy buen hotel, pero el wifi lento', '2026-03-29');

-- Promociones
INSERT INTO Promociones (hotel_id, descripcion, fecha_inicio, fecha_fin, descuento)
VALUES (1, 'Promoción de primavera', '2026-03-01', '2026-03-31', 15.00),
       (2, 'Descuento por estancia larga', '2026-04-01', '2026-04-30', 20.00);

-- Empleados
INSERT INTO Empleados (nombre, apellido, email, telefono, rol_id)
VALUES ('Admin', 'Principal', 'admin@hotel.com', '555-0000', 5),
       ('Carlos', 'Ramírez', 'carlos.ramirez@mail.com', '2225556677', 1),
       ('Ana', 'Martínez', 'ana.martinez@mail.com', '2228889999', 3);

-- Turnos
INSERT INTO Turnos (empleado_id, fecha_inicio, hora_inicio, fecha_fin, hora_fin)
VALUES (1, '2026-03-20', '08:00', '2026-03-20', '16:00'),
       (2, '2026-03-21', '16:00', '2026-03-22', '00:00');

-- UsuariosSistema
INSERT INTO UsuariosSistema (empleado_id, username, password_hash, rol_id, activo)
VALUES  (1, 'admin', 'scrypt:32768:8:1$oS3MCQsAT438bwb1$8493a05ce636a591c796c27349d1451388d3e0d1ac8f8611e7e0d9d886f7a02922cc4bc357564512265a67da4c11dc2e556682bbb8e67d820512070fedddd59a', 5, TRUE),
       (2, 'carlos_r', 'scrypt:32768:8:1$zSyBcYCk3kb9JtEw$e231437c02ff8bd906c6f9ed289211a7abc35656cc37712139cd373a233d5bd1560cc28f466b86ba6cc16c4d45e8aee6a206f420b5e891c6f416c5d422d433d9', 1, TRUE),
       (3, 'ana_m', 'scrypt:32768:8:1$tXrMpTesoW35pZ9P$819c1c65c91736ee9f792ab8a2f681f47738b9f701947d24578f587506f867de5ba40d886dd7fbd7afd29f2eaf3a3189145e04f9019d6b2edc6ef79f25b53ea5', 3, TRUE);

-- LogsAcceso
INSERT INTO LogsAcceso (usuario_id, accion, ip_origen)
VALUES (1, 'Inicio de sesión', '192.168.1.10'),
       (1, 'Registro de reserva', '192.168.1.10');