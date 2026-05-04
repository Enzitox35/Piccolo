import streamlit as st

import sqlite3

from database import *
crear_base_datos()


# Configuración de la página
st.set_page_config(page_title="Sistema Piccolo", page_icon="https://www.pngall.com/wp-content/uploads/15/Piccolo-PNG-Images-HD.png", layout="wide") #👴

# 🔹 1. Conexión a la base (arriba de todo)
conn = sqlite3.connect("mi_base.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    edad INTEGER
)
""")
conn.commit()

# Menú Lateral
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["Inicio", "Recordatorios", "Contactos", "Configuración"])

if opcion == "Inicio":
    st.title("☀️ ¡Buen día!")
    st.write("Bienvenido al *Sistema Piccolo*. ¿En qué puedo ayudarte hoy?")
    # Aquí puedes poner la imagen que mencionamos antes
    st.image(r"C:\Users\usuario\Piccolo\Piccolo-IA.jpeg", caption="Asistente para Adultos Mayores")

 # 🔽 MENÚ INTERNO DE USUARIOS
    st.divider()
    st.subheader("👤 Gestión de usuarios")

    accion = st.radio(
        "Seleccionar acción",
        ["➕ Registrar", "✏️ Editar", "🗑️ Eliminar"],
        horizontal=True
    )

    usuarios = obtener_usuarios()

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
                insertar_usuario(nombre, edad)
                st.success("Usuario guardado")
                st.rerun()

    # =========================
    # ✏️ EDITAR
    # =========================
    elif accion == "✏️ Editar":
        if usuarios:
            opciones = {f"{u['nombre']} (ID: {u['id']})": u for u in usuarios}
            usuario_sel = st.selectbox("Seleccionar usuario", list(opciones.keys()), key="edit_select")

            user = opciones[usuario_sel]

            nuevo_nombre = st.text_input("Nuevo nombre", value=user["nombre"], key="edit_nombre")
            nueva_edad = st.number_input("Nueva edad", min_value=0, value=user["edad"], key="edit_edad")

            if st.button("Guardar cambios", key="btn_editar"):
                if nuevo_nombre.strip() == "":
                    st.warning("El nombre no puede estar vacío")
                else:
                    actualizar_usuario(user["id"], nuevo_nombre, nueva_edad)
                    st.success("Usuario actualizado")
                    st.rerun()
        else:
            st.info("No hay usuarios")

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
                    eliminar_usuario(opciones[usuario_sel])
                    st.success("Usuario eliminado")
                    st.rerun()
                else:
                    st.warning("Tenés que confirmar")
        else:
            st.info("No hay usuarios")

elif opcion == "Recordatorios":
    st.title("📅 Mis Recordatorios")
    st.write("Aquí verás tus medicamentos y turnos médicos.")
    # Próximamente: Conexión a SQLite

elif opcion == "Contactos":
    st.title("📞 Contactos de Emergencia")
    st.write("Listado de personas a las que puedes llamar rápidamente.")