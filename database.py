import sqlite3
from pathlib import Path

# =========================
# RUTA BASE DE DATOS (Integrada y limpia)
# =========================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "piccolo.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Esto permite acceder a las columnas por su nombre como un diccionario
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

    # Las personas que cuidamos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre           TEXT NOT NULL,
            edad             INTEGER,
            quien_avisar     TEXT,
            fecha_bienvenida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Lo que Piccolo sabe sobre cada medicina (Formato SQLite corregido)
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

    # Las alarmas de cada persona
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

    # Cada vez que alguien le habla a Piccolo
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

    # Cómo le fue a Piccolo en cada sesión
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS como_le_fue (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_charlas      INTEGER DEFAULT 0,
            wer                REAL,
            perplejidad        REAL,
            f1                 REAL,
            precision          REAL,
            recall             REAL,
            aciertos_ner       REAL,
            tiempo_promedio_ms INTEGER
        )
    """)

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
# GESTIÓN DE PERSONAS (USUARIOS)
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
# CONSULTAS DE MEDICAMENTOS
# =========================
def obtener_dato_medicina(columna, medicamento):
    conn = get_connection()
    cursor = conn.cursor()
    # Sanitización básica del nombre de columna válido
    columnas_validas = ["para_que_sirve", "tipo", "que_hace", "tener_cuidado", "para_quien", "consejo_amigable"]
    if columna not in columnas_validas:
        conn.close()
        return None

    query = f"SELECT {columna} FROM saberes_piccolo WHERE lower(nombre_medicina) = ?"
    cursor.execute(query, (medicamento.lower(),))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def obtener_todos_saberes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM saberes_piccolo ORDER BY nombre_medicina").fetchall()
    conn.close()
    return [dict(r) for r in rows]

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
    conn.execute("INSERT INTO alarmas_piccolo (persona_id, medicina, horario, repetir) VALUES (?, ?, ?, ?)",
                 (persona_id, medicina, horario, repetir))
    conn.commit()
    conn.close()

def desactivar_alarma(alarma_id):
    conn = get_connection()
    conn.execute("UPDATE alarmas_piccolo SET activa = 0 WHERE id = ?", (alarma_id,))
    conn.commit()
    conn.close()

# =========================
# HISTORIAL Y ESTADÍSTICAS
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

def obtener_estadisticas():
    conn = get_connection()
    stats = {}
    stats["total_charlas"] = conn.execute("SELECT COUNT(*) FROM conversaciones").fetchone()[0]
    stats["wer_promedio"] = conn.execute("SELECT AVG(wer) FROM conversaciones WHERE wer IS NOT NULL").fetchone()[0]
    stats["pp_promedio"] = conn.execute("SELECT AVG(perplejidad) FROM conversaciones WHERE perplejidad IS NOT NULL").fetchone()[0]
    stats["tiempo_promedio_ms"] = conn.execute("SELECT AVG(tiempo_ms) FROM conversaciones WHERE tiempo_ms IS NOT NULL").fetchone()[0]
    
    stats["intenciones_frecuentes"] = [dict(r) for r in conn.execute("""
        SELECT intencion, COUNT(*) as total FROM conversaciones
        WHERE intencion IS NOT NULL GROUP BY intencion ORDER BY total DESC LIMIT 10
    """).fetchall()]
    
    stats["charlas_por_dia"] = [dict(r) for r in conn.execute("""
        SELECT DATE(cuando) as dia, COUNT(*) as total
        FROM conversaciones GROUP BY dia ORDER BY dia DESC LIMIT 14
    """).fetchall()]
    
    ultima_eval = conn.execute("SELECT * FROM como_le_fue ORDER BY fecha DESC LIMIT 1").fetchone()
    stats["ultima_evaluacion"] = dict(ultima_eval) if ultima_eval else None
    
    conn.close()
    return stats

if __name__ == "__main__":
    crear_base_datos()
    cargar_saberes_iniciales()
    exito, mensaje = probar_conexion()
    print(f"Estado: {mensaje}")
