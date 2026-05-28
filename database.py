import sqlite3
from pathlib import Path
DB_PATH = "piccolo.db"

# =========================
# RUTA BASE DATOS
# =========================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "piccolo.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saberes_piccolo (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    nombre_medicina  VARCHAR(100) NOT NULL,
    para_que_sirve   TEXT,
    tipo             VARCHAR(100),
    que_hace         TEXT,
    tener_cuidado    TEXT,
    para_quien       VARCHAR(200),
    consejo_amigable TEXT,
    fecha_carga      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"""
    )

    cursor.executescript("""
    INSERT INTO saberes_piccolo
    (nombre_medicina, para_que_sirve, tipo, que_hace, tener_cuidado, para_quien, consejo_amigable)
    VALUES
    ('Enalapril',
     'Ayuda a bajar la presión de la sangre',
     'Antihipertensivo',
     'Relaja los vasos sanguíneos para que el corazón trabaje con más calma',
     'Mejor no tomarlo si estás embarazada',
     'Presión alta',
     'Tomalo siempre a la misma hora del día, como un ritual.'),

    ('Metformina',
     'Ayuda a controlar el azúcar en la sangre',
     'Antidiabético',
     'Le dice al cuerpo cómo usar mejor el azúcar',
     'Avisale al médico si tenés problemas de riñón',
     'Diabetes tipo 2',
     'Tomala con la comida, así el estómago lo agradece.'),

    ('Atorvastatina',
     'Baja el colesterol malo',
     'Hipolipemiante',
     'Limpia las grasas que se acumulan en la sangre',
     'No tomar con jugo de pomelo',
     'Colesterol alto',
     'La noche es el mejor momento para tomarla.'),

    ('Omeprazol',
     'Protege el estómago y calma la acidez',
     'Gastroprotector',
     'Reduce el ácido que produce el estómago',
     'Si lo tomás mucho tiempo, hablá con tu médico',
     'Acidez / Gastritis / Reflujo',
     'Tomalo media hora antes del desayuno, con un vasito de agua.'),

    ('Losartán',
     'Baja la presión y cuida los riñones',
     'Antihipertensivo',
     'Relaja los vasos sanguíneos',
     'No tomarlo durante el embarazo',
     'Presión alta',
     'Tomá agua seguido y controlate la presión de vez en cuando.'),

    ('Levotiroxina',
     'Reemplaza la hormona que la tiroides no produce',
     'Hormona tiroidea',
     'Ayuda al metabolismo a funcionar bien',
     'No mezclar con calcio ni hierro',
     'Tiroides baja (hipotiroidismo)',
     'Tomala en ayunas, al menos 30 minutos antes de desayunar.'),

    ('Amlodipina',
     'Baja la presión y alivia la angina de pecho',
     'Antihipertensivo',
     'Abre los vasos sanguíneos para que la sangre fluya mejor',
     'A veces hincha un poco los tobillos',
     'Presión alta / Angina',
     'Se puede tomar con o sin comida, lo importante es la misma hora siempre.'),

    ('Aspirina 100mg',
     'Evita que se formen coágulos en la sangre',
     'Antiagregante',
     'Hace que la sangre fluya sin pegarse',
     'No tomar si tenés úlcera o tomás anticoagulantes',
     'Cuidado del corazón',
     'Tomala con comida para proteger el estómago.'),

    ('Furosemida',
     'Elimina el líquido que se acumula en el cuerpo',
     'Diurético',
     'Le ayuda al riñón a sacar el agua de más',
     'Puede bajar el potasio, comer banana ayuda',
     'Retención de líquido / Corazón',
     'Tomala a la mañana para no levantarte de noche.'),

    ('Clonazepam',
     'Calma la ansiedad y ayuda con las convulsiones',
     'Ansiolítico',
     'Tranquiliza el sistema nervioso',
     'No dejarlo de golpe, hay que ir bajando de a poco',
     'Ansiedad / Epilepsia',
     'No manejes después de tomarlo. Avisale a alguien de confianza que lo tomás.');
     """
    )
    conn.commit()
    conn.close()

def obtener_usuarios():
    conn = get_connection()
    rows = conn.execute("SELECT id, nombre, edad FROM usuarios").fetchall()
    conn.close()
    return rows


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

def buscar_respuesta(pregunta):

    conexion = get_connection()
    cursor = conexion.cursor()
    
    cursor.execute(
        """
        SELECT para_que_sirve
        FROM saberes_piccolo
        WHERE nombre_medicina = ?
        """,
        (pregunta,)
    )
    resultado = cursor.fetchone()

    conexion.close()

    return resultado

def obtener_dato_medicina(columna, medicamento):

    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
    SELECT {columna}
    FROM saberes_piccolo
    WHERE lower(nombre_medicina) = ?
    """

    cursor.execute(query, (medicamento.lower(),))

    resultado = cursor.fetchone()

    conn.close()

    return resultado

if __name__ == "__main__":
    crear_base_datos()