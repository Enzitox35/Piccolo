import sqlite3

conn = sqlite3.connect('data/piccolo.db')
cursor = conn.cursor()

print("--- REVISANDO BASE DE DATOS ---")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = [t[0] for t in cursor.fetchall()]
print("Tablas encontradas:", tablas)

tabla_eval = 'como_le_fue' 

if tabla_eval in tablas:
    columnas_a_agregar = ['wer_promedio', 'precision_ir', 'recall_ir', 'f1']
    
    cursor.execute(f"PRAGMA table_info({tabla_eval});")
    columnas_actuales = [info[1] for info in cursor.fetchall()]
    
    for col in columnas_a_agregar:
        if col not in columnas_actuales:
            try:
                cursor.execute(f"ALTER TABLE {tabla_eval} ADD COLUMN {col} REAL;")
                print(f"Columna {col} agregada con exito")
            except Exception as e:
                print(f"Error al agregar {col}: {e}")
        else:
            print(f"La columna {col} ya existia")
else:
    print(f"Alerta: La tabla {tabla_eval} no se encontro")

conn.commit()
conn.close()
print("--- PROCESO TERMINADO ---")
