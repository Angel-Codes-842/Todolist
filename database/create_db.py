import sqlite3

# Conectar a la base de datos (o crearla)
conn = sqlite3.connect('tareas.db')

conn.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    contraseña TEXT NOT NULL,
    es_admin BOOLEAN DEFAULT FALSE
);
''')

# Crear la tabla de tareas
conn.execute('''
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha TEXT,
    completada BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);
''')

conn.close()
print("Base de datos creada y tabla 'tareas' lista.")