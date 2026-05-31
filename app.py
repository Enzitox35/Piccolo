import sys
from pathlib import Path
import streamlit as st

# ==========================================
# 🗺️ CONTROL DE RUTAS E INICIALIZACIÓN
# ==========================================
RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.append(str(RAIZ_PROYECTO))

(RAIZ_PROYECTO / "data").mkdir(exist_ok=True)

# ==========================================
# IMPORTACIONES DEL SISTEMA PICCOLO
# ==========================================
try:
    from modules.db import (
        obtener_personas, agregar_persona, actualizar_persona,
        eliminar_persona, crear_base_datos, obtener_dato_medicina,
        cargar_saberes_iniciales
    )
    from modules.nlp import procesar_texto
    from modules.search import buscar as buscar_en_indice
    from modules.tts import sintetizar_voz
    from modules.asr import transcribir_audio
    MODULOS_OK = True
except Exception as e_import:
    MODULOS_OK = False
    DETALLE_ERROR = str(e_import)

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema Piccolo — Asistente de Salud",
    page_icon="💊",
    layout="wide"
)

# ==========================================
# CSS DRAGON BALL TEMÁTICO
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
    background-color: #0a0a0a;
    color: #e8e8e8;
}

.stApp {
    background: linear-gradient(160deg, #0a0a0a 0%, #0f1a0f 50%, #0a0a0a 100%);
}

.piccolo-header {
    background: linear-gradient(135deg, #000000 0%, #0d2e0d 40%, #1a5c1a 70%, #2d8a2d 100%);
    border: 2px solid #39ff14;
    border-radius: 16px;
    padding: 30px 40px;
    margin-bottom: 24px;
    box-shadow: 0 0 30px rgba(57,255,20,0.3), inset 0 0 60px rgba(0,0,0,0.5);
    text-align: center;
}
.piccolo-header h1 {
    font-family: 'Bangers', cursive;
    font-size: 3.2rem;
    color: #39ff14;
    letter-spacing: 4px;
    margin: 0;
    text-shadow: 0 0 20px rgba(57,255,20,0.8), 3px 3px 0px #000;
}
.piccolo-header p {
    font-size: 1.1rem;
    color: #a8d8a8;
    margin: 8px 0 0;
    font-style: italic;
}
.piccolo-header .subtitulo {
    font-family: 'Bangers', cursive;
    font-size: 1.4rem;
    color: #ff8c00;
    letter-spacing: 2px;
    margin-top: 4px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050f05 0%, #0a1a0a 100%);
    border-right: 2px solid #39ff14;
}
section[data-testid="stSidebar"] * {
    color: #c8f0c8 !important;
}

.respuesta-box {
    background: linear-gradient(135deg, #0d1f0d, #0f2a0f);
    border-left: 5px solid #39ff14;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 16px 0;
    font-size: 1.1rem;
    line-height: 1.8;
    color: #d4f5d4;
    box-shadow: 0 0 20px rgba(57,255,20,0.1);
}

.stButton > button {
    background: linear-gradient(135deg, #1a5c1a, #2d8a2d) !important;
    color: #39ff14 !important;
    border: 1px solid #39ff14 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'Bangers', cursive !important;
    letter-spacing: 2px !important;
    font-size: 1rem !important;
}

.stTextInput > div > div > input {
    background-color: #0d1f0d !important;
    border: 1px solid #39ff14 !important;
    color: #d4f5d4 !important;
}

h1, h2, h3 {
    color: #39ff14 !important;
    font-family: 'Bangers', cursive !important;
    letter-spacing: 2px !important;
}

.sidebar-logo {
    text-align: center;
    padding: 10px 0 20px;
}
.sidebar-logo h2 {
    font-family: 'Bangers', cursive !important;
    color: #39ff14 !important;
    font-size: 1.8rem !important;
}

.emergencia-box {
    background: linear-gradient(135deg, #2e0000, #1a0000);
    border: 2px solid #ff0000;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    font-family: 'Bangers', cursive;
    font-size: 1.3rem;
    color: #ff4444;
}
.contacto-box {
    background: linear-gradient(135deg, #001a2e, #00102e);
    border: 2px solid #00bfff;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    font-family: 'Bangers', cursive;
    font-size: 1.3rem;
    color: #00bfff;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACIÓN DE LA BASE DE DATOS
# ==========================================
if MODULOS_OK:
    crear_base_datos()
    cargar_saberes_iniciales()

# ==========================================
# ⚡ SIDEBAR CON ENFOQUE DE DOS PERFILES
# ==========================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>⚡ PICCOLO ⚡</h2>
        <p>Asistente Médico Personalizado</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        st.image("Piccolo-PNG-Picture.png", use_container_width=True)
    except:
        pass

    st.markdown("---")
    
    st.markdown("### 👨‍⚕️ PANEL MÉDICO")
    modo_medico = st.checkbox("🔑 Ingresar como Administrador", value=False, key="check_medico")
    
    st.markdown("---")
    
    if modo_medico:
        opcion = "⚙️ Panel de Gestión de Paciente"
        st.info("🛠️ Modo Administrador Activo")
    else:
        st.markdown("### 👤 PANEL DEL PACIENTE")
        opcion = st.radio("", ["🏠 Mi Muro de Bienestar", "💬 Consultar a Piccolo", "📞 Auxilio Inmediato"])

# ==========================================
# CONTROL DE ERRORES MÓDULOS
# ==========================================
if not MODULOS_OK:
    st.error("🚨 Error al cargar los módulos de IA")
    st.info(f"**Detalle:** {DETALLE_ERROR}")
    st.stop()

# Recuperamos los datos del paciente único registrado
lista_usuarios = obtener_personas()
paciente_unico = lista_usuarios[0] if lista_usuarios else {"nombre": "Guerrero", "edad": "", "quien_avisar": "Familiar de confianza"}

# ==========================================
# 👨‍⚕️ ⚙️ PANEL DE GESTIÓN (ADMINISTRADOR)
# ==========================================
if modo_medico:
    st.markdown("<h2>👨‍⚕️ PANEL DE CONTROL DE ASISTENCIA MÉDICA</h2>", unsafe_allow_html=True)
    st.write("Configurá los datos del paciente único para personalizar las respuestas de la IA de Piccolo.")
    
    st.divider()
    
    st.markdown("### 👤 Ficha Clínica del Paciente Registrado")
    
    if lista_usuarios:
        st.success(f"Paciente activo en el sistema: **{paciente_unico['nombre']}** ({paciente_unico['edad']} años)")
        
        col1, col2 = st.columns(2)
        with col1:
            nuevo_nombre = st.text_input("Nombre Completo del Paciente", value=paciente_unico["nombre"])
        with col2:
            nueva_edad = st.number_input("Edad del Paciente", min_value=0, max_value=120, value=int(paciente_unico["edad"] or 0))
        nuevo_avisar = st.text_input("Contacto de Emergencia Asignado", value=paciente_unico.get("quien_avisar", ""))
        
        if st.button("⚡ ACTUALIZAR FICHA ÚNICA"):
            if nuevo_nombre.strip() == "":
                st.warning("El nombre no puede quedar vacío.")
            else:
                actualizar_persona(paciente_unico["id"], nuevo_nombre, int(nueva_edad), nuevo_avisar)
                st.success("✅ Configuración guardada correctamente.")
                st.rerun()
    else:
        st.warning("No hay ningún paciente configurado en el sistema.")
        st.markdown("#### Registrar Paciente Principal")
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nombre del paciente")
        with col2:
            ed = st.number_input("Edad", min_value=0, max_value=120, value=70)
        av = st.text_input("¿A quién avisar?")
        if st.button("⚡ CREAR PACIENTE ÚNICO"):
            if nom.strip() != "":
                agregar_persona(nom, int(ed), av)
                st.success("✅ Paciente registrado.")
                st.rerun()

# ==========================================
# 👤 🏠 INICIO (PACIENTE) - ESTABLE (SIN CHOQUES DE DOM)
# ==========================================
elif opcion == "🏠 Mi Muro de Bienestar":
    st.markdown("""
    <div class="piccolo-header">
        <h1>⚡ BIENVENIDO A TU MURO DE BIENESTAR ⚡</h1>
        <div class="subtitulo">SISTEMA INTELIGENTE DE ASISTENCIA PERSONAL</div>
        <p>"Estoy analizando tus parámetros de salud en tiempo real. ¡Consultame cualquier duda!"</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    col_img, col_info = st.columns([1, 2])
    with col_img:
        try:
            st.image("Piccolo-IA.jpeg", use_container_width=True)
        except:
            st.info("🖼️ Espacio para Piccolo-IA.jpeg")

    with col_info:
        st.markdown(f"## Ficha de Cuidado Activa")
        st.markdown(f"Aquí podés ver un resumen de tu perfil configurado por tu médico:")
        
        st.markdown(f"* 👤 **Paciente Protegido:** {paciente_unico['nombre']}")
        st.markdown(f"* ⏳ **Edad Registrada:** {paciente_unico['edad']} años")
        st.markdown(f"* 📞 **Contacto ante eventualidades:** {paciente_unico.get('quien_avisar', 'No asignado')}")
        
        st.markdown("---")
        st.markdown("### 💡 ¿Cómo hablar con Piccolo?")
        st.write("Andá a la pestaña **'💬 Consultar a Piccolo'** del menú lateral, presioná el gran botón blanco del micrófono y contale qué te pasa o consultale por tus remedios. Él te va a responder hablando con su propia voz.")

# ==========================================
# 👤 💬 CONSULTAR A PICCOLO (PACIENTE) - CORREGIDO Y INTEGRADO
# ==========================================
elif opcion == "💬 Consultar a Piccolo":
    st.markdown("""
    <div class="piccolo-header">
        <h1>💬 CONSULTÁ A PICCOLO</h1>
        <p>"Hablame fuerte y claro. Estoy listo para asistirte."</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col_pic, col_chat = st.columns([1, 3])

    with col_pic:
        try:
            st.image("Piccolo-PNG-Picture.png", use_container_width=True)
        except:
            pass

    with col_chat:
        st.markdown("### 🎤 Grabá tu consulta")
        
        audio_recibido = st.audio_input("Presioná para hablarle a Piccolo:", key="mic_piccolo")
        mensaje_voz = ""

        if audio_recibido is not None:
            with st.spinner("⚡ Piccolo está procesando tu voz..."):
                try:
                    bytes_audio = audio_recibido.read()
                    resultado_asr = transcribir_audio(bytes_audio, idioma="es-AR")
                    if resultado_asr["exito"]:
                        mensaje_voz = resultado_asr["texto"]
                        st.success(f"🎤 Escuché: *{mensaje_voz}*")
                    else:
                        st.warning("No capté bien el audio. Intentá de nuevo o escribilo abajo.")
                except Exception as e:
                    st.warning(f"Aviso del micrófono: {e}")

        mensaje_teclado = st.text_input("O escribí tu consulta acá:",
            value=mensaje_voz, placeholder="¿Para qué sirve el enalapril?",
            key="chat_piccolo")

        consulta_final = mensaje_voz if mensaje_voz else mensaje_teclado

        if consulta_final:
            with st.spinner("⚡ Piccolo analiza tu consulta..."):
                try:
                    analisis = procesar_texto(consulta_final)
                    medicamento = analisis["medicamento_detectado"]
                    columna = analisis["columna_bd"]
                except Exception:
                    medicamento = None
                    columna = "que_hace"

                aviso = (f" Recordá, {paciente_unico['nombre']}, que soy Piccolo tu asistente. "
                         "Para decisiones de medicación importantes, consultá siempre a tu médico.")
                respuesta = ""
                
                consulta_lower = consulta_final.lower()

                # Diccionario flexible de síntomas (Reglas de empatía)
                MALESTARES_BIENESTAR = {
                    "estomago": {
                        "claves": ["panza", "indigestion", "indigestión", "pesadez", "pancita", "estomago", "estómago", "acidez", "duele la panza"],
                        "respuesta": "Para esa pesadez o malestar de panza, te sugiero descansar un ratito de costado, ponerte cómodo y quizás prepararte un té de manzanilla natural para asentar el estómago de a poco. Tratá de no comer nada pesado por unas horas."
                    },
                    "fiebre": {
                        "claves": ["fiebre", "calentura", "volando de fiebre", "temperatura", "chuchos de frio"],
                        "respuesta": "Entiendo, la fiebre es una señal de cuidado en nuestro cuerpo. Te sugiero abrigarte lo justo, tomar agua fresca en pequeños sorbos para no deshidratarte y registrar los números con el termómetro."
                    },
                    "olvido": {
                        "claves": ["olvide", "olvidé", "no me acuerdo", "pastilla", "tome la", "tomé la"],
                        "respuesta": "No te preocupes. Mirá el pastillero o el blíster para ver si falta la dosis de hoy. Si tenés mucha duda, es preferible esperar al horario de la próxima dosis antes que tomar doble."
                    },
                    "articulaciones": {
                        "claves": ["rodilla", "huesos", "articulaciones", "espalda", "cintura", "duele el cuerpo"],
                        "respuesta": "Esos dolores de huesos o rodillas suelen aparecer por esfuerzo o humedad. Intentá no hacer movimientos bruscos hoy. Aplicar una almohadilla tibia en la zona te puede aliviar bastante."
                    },
                    "mareo": {
                        "claves": ["mareo", "mareado", "me da vueltas", "inestable", "mareada"],
                        "respuesta": "Si te sentís mareado o sentís que todo da vueltas, por favor sentate de inmediato en el sillón más cercano para evitar caídas. Respirá hondo y despacio hasta que se pase."
                    }
                }

                if medicamento:
                    try:
                        resultado = obtener_dato_medicina(columna or "que_hace", medicamento)
                        if resultado and resultado[0]:
                            respuesta = f"Sobre el **{medicamento.capitalize()}**: {resultado[0]}"
                        else:
                            respuesta = f"Tengo registrado el {medicamento.capitalize()}, pero no encontré ese detalle en la base de datos."
                    except:
                        respuesta = "Tuve un inconveniente técnico al consultar los saberes médicos."

                else:
                    regla_encontrada = False
                    for malestar, info in MALESTARES_BIENESTAR.items():
                        if any(palabra in consulta_lower for palabra in info["claves"]):
                            respuesta = info["respuesta"]
                            regla_encontrada = True
                            break

                    if not regla_encontrada:
                        try:
                            resultados_ir = buscar_en_indice(consulta_final, top_n=1)
                            if resultados_ir and resultados_ir[0]["similitud"] > 0.05:
                                match = resultados_ir[0]
                                respuesta = f"Esto puede relacionarse con **{match['titulo']}**: {match['snippet']}"
                            else:
                                respuesta = ("No reconocí un medicamento o síntoma específico. "
                                             "Podés consultarme por: enalapril, metformina, omeprazol, losartán o clonazepam.")
                        except:
                            respuesta = "No pude procesar la consulta en el índice de búsqueda."

                respuesta_final = respuesta + aviso

                st.markdown(f"""
                <div class="respuesta-box">
                    ⚡ <strong>Piccolo dice:</strong><br><br>{respuesta_final}
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("Piccolo prepara su voz..."):
                    try:
                        audio_res = sintetizar_voz(respuesta_final)
                        if audio_res["exito"] and audio_res["audio_bytes"]:
                            st.audio(audio_res["audio_bytes"], format="audio/mp3")
                        else:
                            st.caption("⚠️ El sintetizador de voz no generó salida.")
                    except Exception as e_tts:
                        st.caption(f"Audio no disponible temporalmente: {e_tts}")

# ==========================================
# 👤 📞 AUXILIO (PACIENTE)
# ==========================================
elif opcion == "📞 Auxilio Inmediato":
    st.markdown("""
    <div class="piccolo-header">
        <h1>📞 AUXILIO INMEDIATO</h1>
        <p>"No estás solo. Aquí tenés los accesos rápidos de asistencia."</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="emergencia-box">
            🚨 EMERGENCIAS MÉDICAS<br>
            <span style="font-size:2.5rem;">107</span><br>
            <span style="font-size:0.9rem; font-family:'Nunito';">Servicio de Ambulancia (SAME)</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="contacto-box">
            ☎️ CONTACTO DE ASISTENCIA FAMILIAR<br>
            <span style="font-size:1.5rem;">{paciente_unico.get('quien_avisar', 'Familiar Directo')}</span><br>
            <span style="font-size:0.9rem; font-family:'Nunito';">Tu red de apoyo registrada</span>
        </div>
        """, unsafe_allow_html=True)