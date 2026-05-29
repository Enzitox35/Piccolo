import streamlit as st
from gtts import gTTS
import sqlite3

# ==========================================
# IMPORTACIONES DEL SISTEMA PICCOLO (CORREGIDO)
# ==========================================
from database import (
    obtener_personas, 
    agregar_persona, 
    actualizar_persona, 
    eliminar_persona,
    crear_base_datos,
    buscar_medicina_por_dolencia,  # <-- Agregado correctamente
    obtener_dato_medicina         # <-- Agregado correctamente
)

# 💻 CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Sistema Piccolo", 
    page_icon="https://www.pngall.com/wp-content/uploads/15/Piccolo-PNG-Images-HD.png", 
    layout="wide"
)

# Inicializamos la base de datos oficial
crear_base_datos()

# Menú Lateral de Navegación
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
                agregar_persona(nombre, edad)
                st.success("Usuario guardado con éxito")
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
            nueva_edad = st.number_input("Nueva edad", min_value=0, value=int(user["edad"] or 0), key="edit_edad")

            if st.button("Guardar cambios", key="btn_editar"):
                if nuevo_nombre.strip() == "":
                    st.warning("El nombre no puede estar vacío")
                else:
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
    st.title("📞 Mi Compañero de Emergencias y Asistencia")
    st.write("Acá tenés tus contactos rápidos y podés charlar con Piccolo sobre cómo te sentís.")

    # Tarjetas de asistencia rápida en pantalla grande para el abuelo
    col1, col2 = st.columns(2)
    with col1:
        st.error("🚨 EMERGENCIAS (Ambulancia): Llamar al 107")
    with col2:
        st.info("☎️ Mi Contacto de Confianza: (Hijo / Vecino / Familiar)")

    st.divider()
    st.title("🗣️ Charlá con Piccolo")
    st.subheader("Hola, acá estoy para acompañarte. Contame, ¿cómo te sentís hoy? ¿Te duele algo?")

    # Guía visual amigable para el usuario mayor
    st.info("Ejemplos de cómo podés hablarle a Piccolo: \n* *'Me duele mucho la panza'* \n* *'Me siento mareado y me duele la cabeza'* \n* *'¿Para qué sirve el Enalapril?'*")

    mensaje = st.text_input("Escribí acá tu dolencia o consulta:", key="chat_asistencia_sola")

    if mensaje:
        mensaje_limpio = mensaje.lower()
        
        # 1. Intentamos buscar por dolencia general (dolor de panza, cabeza, etc.)
        medicina_encontrada = buscar_medicina_por_dolencia(mensaje_limpio)

        if medicina_encontrada:
            nombre = medicina_encontrada["nombre_medicina"]
            sirve = medicina_encontrada["para_que_sirve"]
            consejo = medicina_encontrada["consejo_amigable"]
            cuidado = medicina_encontrada.get("tener_cuidado", "")
            
            respuesta = (
                f"Te escucho con atención. Para eso que me contás de que te sentís así, "
                f"acordate que tenés recetado tomar {nombre}, que justamente {sirve}. "
                f"Mi consejo amigable de hoy: {consejo}. "
            )
            if cuidado:
                respuesta += f" Eso sí, recordá tener este cuidado: {cuidado}."
                
            st.success(f"💊 Inteligencia de Síntomas - Medicación: {nombre}")
            
        else:
            # 2. Si no es un síntoma, evaluamos si preguntó por un nombre directo de medicamento
            medicamentos = ["enalapril", "metformina", "omeprazol", "losartán", "losartan", "clonazepam", "atorvastatina", "levotiroxina", "amlodipina", "aspirina", "furosemida"]
            medicamento_detectado = None

            for med in medicamentos:
                if med in mensaje_limpio:
                    medicamento_detectado = med
                    break

            if medicamento_detectado:
                # Detectamos qué columna quiere saber
                if "sirve" in mensaje_limpio or "para que" in mensaje_limpio:
                    columna = "para_que_sirve"
                elif "cuidado" in mensaje_limpio or "peligro" in mensaje_limpio:
                    columna = "tener_cuidado"
                elif "consejo" in mensaje_limpio or "tip" in mensaje_limpio:
                    columna = "consejo_amigable"
                elif "tipo" in mensaje_limpio or "clase" in mensaje_limpio:
                    columna = "tipo"
                else:
                    columna = "que_hace"

                try:
                    resultado = obtener_dato_medicina(columna, medicamento_detectado)
                    if resultado and resultado[0]:
                        respuesta = f"Sobre el {medicamento_detectado.capitalize()}: {resultado[0]}"
                    else:
                        respuesta = f"Encontré el medicamento {medicamento_detectado.capitalize()}, pero no tengo detalles sobre {columna.replace('_', ' ')}."
                except Exception as e:
                    respuesta = "Hubo un problema al consultar el saber de Piccolo en la base de datos."
                
                st.info(f"🔍 Consulta directa de Medicamento")
            else:
                # 3. Si no es síntoma ni remedio conocido, alerta protectora de soledad
                respuesta = (
                    "Es un dolor o malestar que no tengo registrado en tu listado de remedios habituales, "
                    "y como estás solito, no quiero que pases un mal momento. Si el dolor es muy fuerte o seguís mal, "
                    "por favor descansá un poquito, avisale a tu contacto de confianza o llamá al médico. "
                    "¿Querés que volvamos a intentar explicarlo con otras palabras?"
                )
                st.warning("⚠️ Consejo de cuidado")

        # =========================
        # OUTPUT: TEXTO Y AUDIO CONVERTIDO (Unificado)
        # =========================
        st.markdown(f"### 🤖 Piccolo te acompaña y te dice:")
        st.write(respuesta)

        try:
            tts = gTTS(text=respuesta, lang="es")
            tts.save("respuesta.mp3")
            st.audio("respuesta.mp3")
        except Exception as e:
            st.error("No pude hablarte en este momento, pero podés leer mi mensaje acá arriba.")

elif opcion == "Configuración":
    st.title("⚙️ Configuración")
    st.write("Ajustes internos del Sistema Piccolo.")