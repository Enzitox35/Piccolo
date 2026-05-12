import sqlite3

DB_PATH = "piccolo.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crear_base_datos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            edad INTEGER,
            contacto_emergencia TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            medicamento TEXT NOT NULL,
            horario TEXT NOT NULL,
            frecuencia TEXT,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def obtener_usuarios():
    conn = get_connection()
    rows = conn.execute("SELECT id, nombre, edad FROM usuarios").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insertar_usuario(nombre, edad):
    conn = get_connection()
    conn.execute(
        "INSERT INTO usuarios (nombre, edad) VALUES (?, ?)",
        (nombre, edad),
    )
    conn.commit()
    conn.close()


def actualizar_usuario(usuario_id, nombre, edad):
    conn = get_connection()
    conn.execute(
        "UPDATE usuarios SET nombre = ?, edad = ? WHERE id = ?",
        (nombre, edad, usuario_id),
    )
    conn.commit()
    conn.close()


def eliminar_usuario(usuario_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    crear_base_datos()