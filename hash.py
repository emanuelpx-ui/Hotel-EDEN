from werkzeug.security import generate_password_hash

hash_admin = generate_password_hash('admin123')
hash_carlos = generate_password_hash('hash123')
hash_ana = generate_password_hash('hash456')

print("-- UsuariosSistema (Con contraseñas hasheadas para Werkzeug)")
print("INSERT INTO UsuariosSistema (empleado_id, username, password_hash, rol_id, activo)")
print("VALUES")
print(f"       (1, 'admin', '{hash_admin}', 5, TRUE),")
print(f"       (2, 'carlos_r', '{hash_carlos}', 1, TRUE),")
print(f"       (3, 'ana_m', '{hash_ana}', 3, TRUE);")