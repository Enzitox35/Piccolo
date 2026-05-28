import streamlit as st
from gtts import gTTS
import sqlite3

# Importamos las funciones con sus nombres actualizados del Sistema Piccolo
from database import (
    obtener_personas, 
    agregar_persona, 
    actualizar_persona, 
    eliminar_persona,
    crear_base_datos,
    obtener_todos_saberes  # Asegúrate de tener esta o la función equivalente para consultar medicinas
)

# 💻 CONFIGURACIÓN DE LA PÁGINA (De la versión entrante de main)
st.set_page_config(
    page_title="Sistema Piccolo", 
    page_icon="https://www.pngall.com/wp-content/uploads/15/Piccolo-PNG-Images-HD.png", 
    layout="wide"
)

# Inicializamos la base de datos oficial del equipo
crear_base_datos()

# Conexión limpia a la base de datos
conexion = sqlite3.connect("piccolo.db")
cursor = conexion.cursor()

# Menú Lateral
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["Inicio", "Recordatorios", "Contactos", "Configuración"])

if opcion == "Inicio":
    st.title("☀️ ¡Buen día!")
    st.write("Bienvenido al *Sistema Piccolo*. ¿En qué puedo ayudarte hoy?")
    
    # 🖼️ Imagen con ruta relativa
    try:
        st.image("Piccolo-IA.jpeg", use_container_width=True)
    except:
        st.warning("No se pudo cargar la imagen Piccolo-IA.jpeg. Verifica que el archivo esté en la carpeta.")

    # 🔽 MENÚ INTERNO DE USUARIOS
    st.divider()
    st.subheader("👤 Gestión de usuarios")

    accion = st.radio(
        "Seleccionar acción",
        ["➕ Registrar", "✏️ Editar", "🗑️ Eliminar"],
        horizontal=True
    )

    # Llamamos a la función para traer la lista actualizada de personas
    usuarios = obtener_personas()

    # =========================
    # ➕ REGISTRAR
    # =========================
    if accion == "➕ Registrar":
        nombre = st.text_input("Nombre", key="crear_nombre")
        edad = st.number_input("Edad", min_value=0, key="crear_edad")

        if st.button("Guardar", key="btn_guardar"):
            if nombre.strip() == "":
                st.warning("El nombre no puede estar vacío")
            else:
                # Corregido: pasamos la variable 'nombre' en lugar del texto fijo "Nombre"
                agregar_persona(nombre, edad)
                st.success("Usuario guardado con éxito")
                st.rerun()

    # =========================
    # ✏️ EDITAR
    # =========================
    elif accion == "✏️ Editar":  # Corregido para que coincida exactamente con la opción del radio button
        if usuarios:
            opciones = {f"{u['nombre']} (ID: {u['id']})": u for u in usuarios}
            usuario_sel = st.selectbox("Seleccionar usuario", list(opciones.keys()), key="edit_select")

            user = opciones[usuario_sel]

            nuevo_nombre = st.text_input("Nuevo nombre", value=user["nombre"], key="edit_nombre")
            nueva_edad = st.number_input("Nueva edad", min_value=0, value=int(user["edad"] or 0), key="edit_edad")

            if st.button("Guardar cambios", key="btn_editar"):
                if nuevo_nombre.strip() == "":
                    st.warning("El nombre no puede estar vacío")
                else:
                    # Corregido: usamos el nombre de función importado 'actualizar_persona'
                    actualizar_persona(user["id"], nuevo_nombre, nueva_edad, user.get("quien_avisar", ""))
                    st.success("Usuario actualizado con éxito")
                    st.rerun()
        else:
            st.info("No hay usuarios registrados todavía.")

    # =========================
    # 🗑️ ELIMINAR
    # =========================
    elif accion == "🗑️ Eliminar":
        if usuarios:
            opciones = {f"{u['nombre']} (ID: {u['id']})": u['id'] for u in usuarios}
            usuario_sel = st.selectbox("Seleccionar usuario", list(opciones.keys()), key="del_select")

            confirmar = st.checkbox("Confirmo eliminación", key="del_check")

            if st.button("Eliminar", key="btn_eliminar"):
                if confirmar:
                    # Corregido: usamos el nombre de función importado 'eliminar_persona'
                    eliminar_persona(opciones[usuario_sel])
                    st.success("Usuario eliminado")
                    st.rerun()
                else:
                    st.warning("Tenés que confirmar la casilla de verificación primero.")
        else:
            st.info("No hay usuarios registrados todavía.")

elif opcion == "Recordatorios":
    st.title("📅 Mis Recordatorios")
    st.write("Aquí verás tus medicamentos y turnos médicos.")

elif opcion == "Contactos":
    st.title("📞 Contactos de Emergencia")
    st.write("Listado de personas a las que puedes llamar rápidamente.")

    st.title("Chat con voz")

    mensaje = st.text_input("Escribí algo")

    if mensaje:
        mensaje = mensaje.lower()

        # =========================
        # DETECTAR INTENCION
        # =========================
        if "sirve" in mensaje:
            columna = "para_que_sirve"
        elif "cuidado" in mensaje:
            columna = "tener_cuidado"
        elif "consejo" in mensaje:
            columna = "consejo_amigable"
        elif "tipo" in mensaje:
            columna = "tipo"
        else:
            columna = "que_hace"

        # =========================
        # DETECTAR MEDICAMENTO
        # =========================
        medicamentos = ["enalapril", "metformina", "omeprazol", "losartán", "clonazepam"]
        medicamento_detectado = None

        for med in medicamentos:
            if med in mensaje:
                medicamento_detectado = med
                break

        # =========================
        # CONSULTAR BASE
        # =========================
        if medicamento_detectado:
            # Nota técnica: Asegúrate de que la función 'obtener_dato_medicina' exista en tu base de datos,
            # o cámbiala por una consulta directa usando 'cursor' si es necesario.
            try:
                cursor.execute(f"SELECT {columna} FROM saberes_medicamentos WHERE LOWER(nombre_medicina) = ?", (medicamento_detectado,))
                resultado = cursor.fetchone()
                
                if resultado and resultado[0]:
                    respuesta = resultado[0]
                else:
                    respuesta = f"No encontré información específica sobre eso para el medicamento {medicamento_detectado}."
            except:
                respuesta = "Hubo un error al consultar la base de datos de medicamentos."
        else:
            respuesta = "No reconocí el medicamento en tu mensaje. Probá mencionando enalapril, metformina, omeprazol, losartán o clonazepam."

        # =========================
        # TEXTO Y AUDIO OUTPUT
        # =========================
        st.write(respuesta)

        try:
            tts = gTTS(text=respuesta, lang="es")
            tts.save("respuesta.mp3")
            st.audio("respuesta.mp3")
        except Exception as e:
            st.error("No se pudo generar el audio de respuesta.")