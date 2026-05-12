import sqlite3

DB_PATH = "sistema_piccolo.db"


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

    # Lo que Piccolo sabe sobre cada medicina (corpus para TF-IDF)
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

    # Cada vez que alguien le habla a Piccolo (obligatorio según la guía)
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

    # Como le fue a Piccolo en cada sesion
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
        ("Enalapril",
         "Ayuda a bajar la presion de la sangre", "Antihipertensivo",
         "Relaja los vasos sanguineos para que el corazon trabaje con mas calma",
         "Mejor no tomarlo si estas embarazada", "Presion alta",
         "Tomalo siempre a la misma hora del dia, como un ritual."),
        ("Metformina",
         "Ayuda a controlar el azucar en la sangre", "Antidiabetico",
         "Le dice al cuerpo como usar mejor el azucar",
         "Avisale al medico si tenes problemas de rinon", "Diabetes tipo 2",
         "Tomala con la comida, asi el estomago lo agradece."),
        ("Atorvastatina",
         "Baja el colesterol malo", "Hipolipemiante",
         "Limpia las grasas que se acumulan en la sangre",
         "No tomar con jugo de pomelo", "Colesterol alto",
         "La noche es el mejor momento para tomarla."),
        ("Omeprazol",
         "Protege el estomago y calma la acidez", "Gastroprotector",
         "Reduce el acido que produce el estomago",
         "Si lo tomas mucho tiempo, habla con tu medico", "Acidez / Gastritis / Reflujo",
         "Tomalo media hora antes del desayuno, con un vasito de agua."),
        ("Losartan",
         "Baja la presion y cuida los rinones", "Antihipertensivo",
         "Relaja los vasos sanguineos",
         "No tomarlo durante el embarazo", "Presion alta",
         "Toma agua seguido y controlate la presion de vez en cuando."),
        ("Levotiroxina",
         "Reemplaza la hormona que la tiroides no produce", "Hormona tiroidea",
         "Ayuda al metabolismo a funcionar bien",
         "No mezclar con calcio ni hierro", "Tiroides baja (hipotiroidismo)",
         "Tomala en ayunas, al menos 30 minutos antes de desayunar."),
        ("Amlodipina",
         "Baja la presion y alivia la angina de pecho", "Antihipertensivo",
         "Abre los vasos sanguineos para que la sangre fluya mejor",
         "A veces hincha un poco los tobillos", "Presion alta / Angina",
         "Se puede tomar con o sin comida, lo importante es la misma hora siempre."),
        ("Aspirina 100mg",
         "Evita que se formen coagulos en la sangre", "Antiagregante",
         "Hace que la sangre fluya sin pegarse",
         "No tomar si tenes ulcera o tomas anticoagulantes", "Cuidado del corazon",
         "Tomala con comida para proteger el estomago."),
        ("Furosemida",
         "Elimina el liquido que se acumula en el cuerpo", "Diuretico",
         "Le ayuda al rinon a sacar el agua de mas",
         "Puede bajar el potasio, comer banana ayuda", "Retencion de liquido / Corazon",
         "Tomala a la manana para no levantarte de noche."),
        ("Clonazepam",
         "Calma la ansiedad y ayuda con las convulsiones", "Ansiolitico",
         "Tranquiliza el sistema nervioso",
         "No dejarlo de golpe, hay que ir bajando de a poco", "Ansiedad / Epilepsia",
         "No manejes despues de tomarlo. Avisale a alguien de confianza que lo tomas."),
    ]

    conn.executemany("""
        INSERT INTO saberes_piccolo
            (nombre_medicina, para_que_sirve, tipo, que_hace,
             tener_cuidado, para_quien, consejo_amigable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, saberes)
    conn.commit()
    conn.close()


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


def obtener_todos_saberes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM saberes_piccolo ORDER BY nombre_medicina").fetchall()
    conn.close()
    return [dict(r) for r in rows]


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
    stats["ultima_evaluacion"] = conn.execute(
        "SELECT * FROM como_le_fue ORDER BY fecha DESC LIMIT 1").fetchone()
    if stats["ultima_evaluacion"]:
        stats["ultima_evaluacion"] = dict(stats["ultima_evaluacion"])
    conn.close()
    return stats


if __name__ == "__main__":
    crear_base_datos()
    cargar_saberes_iniciales()
    exito, mensaje = probar_conexion()
    print(f"Estado: {mensaje}")
