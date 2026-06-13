"""
modules/db.py — Capa de persistencia SQLite
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Versión corregida y completa que:
- Arregla el bug de nombre de tabla (era 'saberes_medicamentos', es 'saberes_piccolo')
- Agrega funciones para guardar/recuperar métricas de evaluación
- Incluye función para obtener estadísticas del dashboard
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "piccolo.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def probar_conexion():
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return True, "¡Piccolo está listo para ayudar!"
    except Exception as e:
        return False, str(e)


def crear_base_datos():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre           TEXT NOT NULL,
            edad             INTEGER,
            quien_avisar     TEXT,
            fecha_bienvenida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saberes_piccolo (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_medicina  TEXT NOT NULL,
            para_que_sirve   TEXT,
            tipo             TEXT,
            que_hace         TEXT,
            tener_cuidado    TEXT,
            para_quien       TEXT,
            consejo_amigable TEXT,
            fecha_carga      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarmas_piccolo (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id INTEGER NOT NULL,
            medicina   TEXT NOT NULL,
            horario    TEXT NOT NULL,
            repetir    TEXT,
            activa     INTEGER DEFAULT 1,
            FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cuando          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            persona_id      INTEGER,
            archivo_audio   TEXT,
            lo_que_dijo     TEXT,
            lo_que_entendio TEXT,
            intencion       TEXT,
            entidades_json  TEXT,
            respuesta       TEXT,
            medicina_id     INTEGER,
            wer             REAL,
            perplejidad     REAL,
            similitud       REAL,
            tiempo_ms       INTEGER,
            FOREIGN KEY (persona_id) REFERENCES personas (id),
            FOREIGN KEY (medicina_id) REFERENCES saberes_piccolo (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS como_le_fue (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_charlas      INTEGER DEFAULT 0,
            wer_promedio       REAL,
            perplejidad_promedio REAL,
            f1                 REAL,
            precision_ir       REAL,
            recall_ir          REAL,
            aciertos_ner       REAL,
            tiempo_promedio_ms INTEGER
        )
    """)

    conn.commit()
    conn.close()
    migrar_base_datos()  # agrega columnas faltantes si la BD ya existía con versión vieja


def migrar_base_datos():
    """
    Agrega columnas faltantes a tablas existentes (ALTER TABLE).
    Se ejecuta automáticamente en cada inicio — es idempotente (no rompe nada si ya están).
    Necesario cuando piccolo.db fue creado con una versión anterior de este archivo.
    """
    conn = get_connection()

    # Columnas requeridas por tabla: {tabla: [(columna, tipo_sql)]}
    migraciones = {
        "como_le_fue": [
            ("total_charlas",        "INTEGER DEFAULT 0"),
            ("wer_promedio",         "REAL"),
            ("perplejidad_promedio", "REAL"),
            ("f1",                   "REAL"),
            ("precision_ir",         "REAL"),
            ("recall_ir",            "REAL"),
            ("aciertos_ner",         "REAL"),
            ("tiempo_promedio_ms",   "INTEGER"),
        ],
        "conversaciones": [
            ("wer",       "REAL"),
            ("perplejidad","REAL"),
            ("similitud",  "REAL"),
            ("tiempo_ms",  "INTEGER"),
        ],
    }

    for tabla, columnas in migraciones.items():
        # Obtener columnas actuales de la tabla
        existentes = {
            row[1]
            for row in conn.execute(f"PRAGMA table_info({tabla})").fetchall()
        }
        for columna, tipo in columnas:
            if columna not in existentes:
                conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")

    conn.commit()
    conn.close()


def cargar_saberes_iniciales():
    conn = get_connection()
    ya_sabe = conn.execute("SELECT COUNT(*) FROM saberes_piccolo").fetchone()[0]
    if ya_sabe > 0:
        conn.close()
        return

    saberes = [
        ("Enalapril", "Ayuda a bajar la presión de la sangre", "Antihipertensivo",
         "Relaja los vasos sanguíneos para que el corazón trabaje con más calma",
         "Mejor no tomarlo si estás embarazada", "Presión alta",
         "Tomalo siempre a la misma hora del día, como un ritual."),
        ("Metformina", "Ayuda a controlar el azúcar en la sangre", "Antidiabético",
         "Le dice al cuerpo cómo usar mejor el azúcar",
         "Avisale al médico si tenés problemas de riñón", "Diabetes tipo 2",
         "Tomala con la comida, así el estómago lo agradece."),
        ("Atorvastatina", "Baja el colesterol malo", "Hipolipemiante",
         "Limpia las grasas que se acumulan en la sangre",
         "No tomar con jugo de pomelo", "Colesterol alto",
         "La noche es el mejor momento para tomarla."),
        ("Omeprazol", "Protege el estómago y calma la acidez", "Gastroprotector",
         "Reduce el ácido que produce el estómago",
         "Si lo tomás mucho tiempo, hablá con tu médico", "Acidez / Gastritis / Reflujo",
         "Tomalo media hora antes del desayuno, con un vasito de agua."),
        ("Losartán", "Baja la presión y cuida los riñones", "Antihipertensivo",
         "Relaja los vasos sanguíneos",
         "No tomarlo durante el embarazo", "Presión alta",
         "Tomá agua seguido y controlate la presión de vez en cuando."),
        ("Levotiroxina", "Reemplaza la hormona que la tiroides no produce", "Hormona tiroidea",
         "Ayuda al metabolismo a funcionar bien",
         "No mezclar con calcio ni hierro", "Tiroides baja (hipotiroidismo)",
         "Tomala en ayunas, al menos 30 minutos antes de desayunar."),
        ("Amlodipina", "Baja la presión y alivia la angina de pecho", "Antihipertensivo",
         "Abre los vasos sanguíneos para que la sangre fluya mejor",
         "A veces hincha un poco los tobillos", "Presión alta / Angina",
         "Se puede tomar con o sin comida, lo importante es la misma hora siempre."),
        ("Aspirina 100mg", "Evita que se formen coágulos en la sangre", "Antiagregante",
         "Hace que la sangre fluya sin pegarse",
         "No tomar si tenés úlcera o tomás anticoagulantes", "Cuidado del corazón",
         "Tomala con comida para proteger el estómago."),
        ("Furosemida", "Elimina el líquido que se acumula en el cuerpo", "Diurético",
         "Le ayuda al riñón a sacar el agua de más",
         "Puede bajar el potasio, comer banana ayuda", "Retención de líquido / Corazón",
         "Tomala a la mañana para no levantarte de noche."),
        ("Clonazepam", "Calma la ansiedad y ayuda con las convulsiones", "Ansiolítico",
         "Tranquiliza el sistema nervioso",
         "No dejarlo de golpe, hay que ir bajando de a poco", "Ansiedad / Epilepsia",
         "No manejes después de tomarlo. Avisale a alguien de confianza que lo tomás."),
    ]

    conn.executemany("""
        INSERT INTO saberes_piccolo
            (nombre_medicina, para_que_sirve, tipo, que_hace,
             tener_cuidado, para_quien, consejo_amigable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, saberes)
    conn.commit()
    conn.close()


# =========================
# PERSONAS
# =========================

def obtener_personas():
    conn = get_connection()
    rows = conn.execute("SELECT id, nombre, edad, quien_avisar FROM personas").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agregar_persona(nombre, edad, quien_avisar=""):
    conn = get_connection()
    conn.execute("INSERT INTO personas (nombre, edad, quien_avisar) VALUES (?, ?, ?)",
                 (nombre, edad, quien_avisar))
    conn.commit()
    conn.close()


def actualizar_persona(persona_id, nombre, edad, quien_avisar=""):
    conn = get_connection()
    conn.execute("UPDATE personas SET nombre = ?, edad = ?, quien_avisar = ? WHERE id = ?",
                 (nombre, edad, quien_avisar, persona_id))
    conn.commit()
    conn.close()


def eliminar_persona(persona_id):
    conn = get_connection()
    conn.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
    conn.commit()
    conn.close()


# =========================
# MEDICAMENTOS
# =========================

def obtener_dato_medicina(columna: str, medicamento: str):
    """
    Consulta un campo específico de saberes_piccolo para un medicamento.
    FIX: antes usaba 'saberes_medicamentos' (tabla inexistente).
    """
    columnas_validas = [
        "para_que_sirve", "tipo", "que_hace",
        "tener_cuidado", "para_quien", "consejo_amigable"
    ]
    if columna not in columnas_validas:
        return None

    conn = get_connection()
    query = f"SELECT {columna} FROM saberes_piccolo WHERE lower(nombre_medicina) = ?"
    resultado = conn.execute(query, (medicamento.lower(),)).fetchone()
    conn.close()
    return resultado


def obtener_todos_saberes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM saberes_piccolo ORDER BY nombre_medicina").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_medicina_por_nombre(nombre: str) -> dict | None:
    """Devuelve el registro completo de un medicamento o None si no existe."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM saberes_piccolo WHERE lower(nombre_medicina) = ?",
        (nombre.lower(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# =========================
# ALARMAS
# =========================

def obtener_alarmas(persona_id=None):
    conn = get_connection()
    if persona_id:
        rows = conn.execute(
            "SELECT * FROM alarmas_piccolo WHERE persona_id = ? AND activa = 1 ORDER BY horario",
            (persona_id,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM alarmas_piccolo WHERE activa = 1 ORDER BY horario").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agregar_alarma(persona_id, medicina, horario, repetir):
    conn = get_connection()
    conn.execute(
        "INSERT INTO alarmas_piccolo (persona_id, medicina, horario, repetir) VALUES (?, ?, ?, ?)",
        (persona_id, medicina, horario, repetir))
    conn.commit()
    conn.close()


def desactivar_alarma(alarma_id):
    conn = get_connection()
    conn.execute("UPDATE alarmas_piccolo SET activa = 0 WHERE id = ?", (alarma_id,))
    conn.commit()
    conn.close()


# =========================
# CONVERSACIONES
# =========================

def guardar_conversacion(
    persona_id, lo_que_dijo, lo_que_entendio,
    intencion=None, entidades_json=None, respuesta=None,
    archivo_audio=None, medicina_id=None,
    wer=None, perplejidad=None, similitud=None, tiempo_ms=None
):
    conn = get_connection()
    conn.execute("""
        INSERT INTO conversaciones (
            persona_id, archivo_audio, lo_que_dijo, lo_que_entendio,
            intencion, entidades_json, respuesta, medicina_id,
            wer, perplejidad, similitud, tiempo_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (persona_id, archivo_audio, lo_que_dijo, lo_que_entendio,
          intencion, entidades_json, respuesta, medicina_id,
          wer, perplejidad, similitud, tiempo_ms))
    conn.commit()
    conn.close()


def obtener_historial(persona_id=None, limite=20):
    conn = get_connection()
    if persona_id:
        rows = conn.execute(
            "SELECT * FROM conversaciones WHERE persona_id = ? ORDER BY cuando DESC LIMIT ?",
            (persona_id, limite)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM conversaciones ORDER BY cuando DESC LIMIT ?",
            (limite,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================
# ESTADÍSTICAS PARA DASHBOARD
# =========================

def obtener_estadisticas():
    """Devuelve todas las estadísticas necesarias para el dashboard."""
    conn = get_connection()
    stats = {}

    stats["total_charlas"] = conn.execute(
        "SELECT COUNT(*) FROM conversaciones").fetchone()[0]

    stats["wer_promedio"] = conn.execute(
        "SELECT AVG(wer) FROM conversaciones WHERE wer IS NOT NULL").fetchone()[0]

    stats["pp_promedio"] = conn.execute(
        "SELECT AVG(perplejidad) FROM conversaciones WHERE perplejidad IS NOT NULL").fetchone()[0]

    stats["tiempo_promedio_ms"] = conn.execute(
        "SELECT AVG(tiempo_ms) FROM conversaciones WHERE tiempo_ms IS NOT NULL").fetchone()[0]

    stats["similitud_promedio"] = conn.execute(
        "SELECT AVG(similitud) FROM conversaciones WHERE similitud IS NOT NULL").fetchone()[0]

    stats["intenciones_frecuentes"] = [dict(r) for r in conn.execute("""
        SELECT intencion, COUNT(*) as total FROM conversaciones
        WHERE intencion IS NOT NULL
        GROUP BY intencion ORDER BY total DESC LIMIT 10
    """).fetchall()]

    stats["charlas_por_dia"] = [dict(r) for r in conn.execute("""
        SELECT DATE(cuando) as dia, COUNT(*) as total
        FROM conversaciones GROUP BY dia ORDER BY dia DESC LIMIT 14
    """).fetchall()]

    stats["medicamentos_consultados"] = [dict(r) for r in conn.execute("""
        SELECT s.nombre_medicina, COUNT(*) as total
        FROM conversaciones c
        JOIN saberes_piccolo s ON c.medicina_id = s.id
        GROUP BY s.nombre_medicina ORDER BY total DESC LIMIT 10
    """).fetchall()]

    ultima_eval = conn.execute(
        "SELECT * FROM como_le_fue ORDER BY fecha DESC LIMIT 1").fetchone()
    stats["ultima_evaluacion"] = dict(ultima_eval) if ultima_eval else None

    conn.close()
    return stats


def guardar_evaluacion(
    total_charlas=0, wer_promedio=None, perplejidad_promedio=None,
    f1=None, precision_ir=None, recall_ir=None,
    aciertos_ner=None, tiempo_promedio_ms=None
):
    """Guarda una sesión de evaluación en como_le_fue."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO como_le_fue (
            total_charlas, wer_promedio, perplejidad_promedio,
            f1, precision_ir, recall_ir, aciertos_ner, tiempo_promedio_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (total_charlas, wer_promedio, perplejidad_promedio,
          f1, precision_ir, recall_ir, aciertos_ner, tiempo_promedio_ms))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    crear_base_datos()  # incluye migrar_base_datos() internamente
    cargar_saberes_iniciales()
    exito, mensaje = probar_conexion()
    print(f"Estado: {mensaje}")
    saberes = obtener_todos_saberes()
    print(f"Medicamentos cargados: {len(saberes)}")
    for s in saberes:
        print(f"  - {s['nombre_medicina']}: {s['para_que_sirve']}")
