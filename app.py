import sys
from pathlib import Path
import streamlit as st
import re
import time

RAIZ_PROYECTO = Path(__file__).resolve().parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.append(str(RAIZ_PROYECTO))

(RAIZ_PROYECTO / "data").mkdir(exist_ok=True)

try:
    from modules.db import (
        obtener_personas, agregar_persona, actualizar_persona,
        eliminar_persona, crear_base_datos, obtener_dato_medicina,
        cargar_saberes_iniciales, obtener_estadisticas, obtener_historial,
        guardar_conversacion, guardar_evaluacion, obtener_medicina_por_nombre
    )
    from modules.nlp import procesar_texto
    from modules.search import buscar as buscar_en_indice, get_motor, evaluar_motor
    from modules.tts import sintetizar_voz
    from modules.asr import transcribir_audio, calcular_wer, get_frases_prueba
    from modules.ngrams import calcular_perplejidad, get_modelo, ModeloNGramas, preparar_corpus, CORPUS_PICCOLO
    from modules.dashboard import generar_nube_palabras, top_consultas, calcular_accuracy_ner, EJEMPLOS_NER
    MODULOS_OK = True
except Exception as e_import:
    MODULOS_OK = False
    DETALLE_ERROR = str(e_import)

st.set_page_config(
    page_title="Piccolo — Asistente de Salud",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

.stApp {
    background: #f0f4f0;
}

/* ── SIDEBAR ─────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1c3a2e 0%, #243d30 60%, #1a3328 100%);
    border-right: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.15);
}
section[data-testid="stSidebar"] * {
    color: #d4e8d8 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem !important;
    padding: 6px 0 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

/* ── HEADER CARD ─────────────────────────── */
.page-header {
    background: linear-gradient(135deg, #1c3a2e 0%, #2d6645 50%, #3a7d56 100%);
    border-radius: 20px;
    padding: 32px 40px;
    margin-bottom: 28px;
    color: white;
    box-shadow: 0 8px 32px rgba(28,58,46,0.25);
    display: flex;
    align-items: center;
    gap: 24px;
}
.page-header-text h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.2rem !important;
    color: #ffffff !important;
    margin: 0 !important;
    letter-spacing: 0.5px !important;
}
.page-header-text p {
    color: rgba(255,255,255,0.75);
    font-size: 1rem;
    margin: 6px 0 0;
    font-weight: 300;
}
.page-header-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 12px;
    padding: 8px 16px;
    font-size: 0.8rem;
    color: rgba(255,255,255,0.9) !important;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 10px;
    display: inline-block;
}

/* ── CARDS ───────────────────────────────── */
.stat-card {
    background: white;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-top: 4px solid #2d6645;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.stat-card .stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    color: #1c3a2e;
    font-weight: 700;
    line-height: 1;
}
.stat-card .stat-val-accent {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    color: #c47c2e;
    font-weight: 700;
    line-height: 1;
}
.stat-card .stat-label {
    font-size: 0.75rem;
    color: #7a9a82;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 8px;
    font-weight: 600;
}

/* ── RESPUESTA ───────────────────────────── */
.respuesta-card {
    background: white;
    border-radius: 16px;
    padding: 24px 28px;
    margin: 20px 0;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border-left: 5px solid #2d6645;
    font-size: 1.05rem;
    line-height: 1.8;
    color: #2a3d2e;
}
.respuesta-card .resp-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #7a9a82;
    font-weight: 700;
    margin-bottom: 10px;
}

/* ── HISTORIAL ───────────────────────────── */
.hist-card {
    background: white;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    border-left: 3px solid #a8d5b5;
}
.hist-card .hist-q { font-weight: 600; color: #1c3a2e; font-size: 0.95rem; }
.hist-card .hist-tag {
    display: inline-block;
    background: #e8f5ec;
    color: #2d6645;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-left: 8px;
    letter-spacing: 0.5px;
}
.hist-card .hist-r { color: #5a7a62; font-size: 0.88rem; margin-top: 4px; }

/* ── BOTONES ─────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1c3a2e, #2d6645) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: 0.5px !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 16px rgba(45,102,69,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── INPUTS ──────────────────────────────── */
.stTextInput > div > div > input {
    background: white !important;
    border: 1.5px solid #c5ddc9 !important;
    border-radius: 10px !important;
    color: #1c3a2e !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2d6645 !important;
    box-shadow: 0 0 0 3px rgba(45,102,69,0.1) !important;
}

/* ── SELECTBOX ───────────────────────────── */
.stSelectbox > div > div {
    background: white !important;
    border: 1.5px solid #c5ddc9 !important;
    border-radius: 10px !important;
    color: #1c3a2e !important;
}

/* ── HEADINGS ────────────────────────────── */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #1c3a2e !important;
    letter-spacing: 0 !important;
}

/* ── ALERTS ──────────────────────────────── */
.stSuccess > div { background: #e8f5ec !important; border-color: #2d6645 !important; color: #1c3a2e !important; border-radius: 10px !important; }
.stWarning > div { background: #fef8ed !important; border-color: #c47c2e !important; color: #5a3d10 !important; border-radius: 10px !important; }
.stError > div { background: #fdf0f0 !important; border-radius: 10px !important; }
.stInfo > div { background: #edf4ff !important; border-radius: 10px !important; }

/* ── EXPANDER ────────────────────────────── */
.streamlit-expanderHeader {
    background: white !important;
    border-radius: 10px !important;
    color: #1c3a2e !important;
    font-weight: 600 !important;
}

/* ── EMERGENCIA ──────────────────────────── */
.emergencia-card {
    background: linear-gradient(135deg, #fff5f5, #ffe8e8);
    border: 2px solid #e05050;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}
.emergencia-card .num { font-family: 'Playfair Display', serif; font-size: 3rem; color: #c03030; font-weight: 700; }
.emergencia-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; color: #c03030; font-weight: 700; }

.contacto-card {
    background: linear-gradient(135deg, #f0f6ff, #e8f0ff);
    border: 2px solid #4a7cca;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}
.contacto-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; color: #4a7cca; font-weight: 700; margin-bottom: 8px; }
.contacto-card .val { font-size: 1.2rem; color: #1a3a7a; font-weight: 600; }

/* ── SIDEBAR LOGO ────────────────────────── */
.sidebar-brand {
    padding: 20px 10px 24px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 16px;
}
.sidebar-brand .brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: #a8d5b5 !important;
    font-weight: 700;
    letter-spacing: 1px;
}
.sidebar-brand .brand-sub {
    font-size: 0.75rem;
    color: rgba(168,213,181,0.7) !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
}

/* ── TABS ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: white !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #5a7a62 !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: #1c3a2e !important;
    color: white !important;
}

/* ── RADIO ───────────────────────────────── */
.stRadio > div { gap: 8px !important; }

/* ── DIVIDER ─────────────────────────────── */
hr { border-color: #d4e8d8 !important; }

/* ── FICHA PACIENTE ──────────────────────── */
.ficha-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.ficha-card .ficha-row {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f4f0;
    font-size: 0.95rem;
    color: #2a3d2e;
}
.ficha-card .ficha-key {
    font-weight: 600;
    color: #7a9a82;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    width: 160px;
    flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

# ── INIT ─────────────────────────────────────────────────────────────
if MODULOS_OK:
    crear_base_datos()
    cargar_saberes_iniciales()
    @st.cache_resource
    def _init():
        return get_motor(), get_modelo(n=2, k=1.0)
    motor_busqueda, modelo_bigrama = _init()

# ── SIDEBAR ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-name">Piccolo</div>
        <div class="brand-sub">Asistente de Salud</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        st.image("Piccolo-PNG-Picture.png", use_container_width=True)
    except:
        pass

    st.markdown("---")
    modo_medico = st.checkbox("🔑 Modo Administrador", value=False)
    st.markdown("---")

    if modo_medico:
        opcion = "admin"
        st.info("Modo Gestión activo")
    else:
        opcion = st.radio("", [
            "🏠  Inicio",
            "💬  Consultar",
            "📊  Dashboard",
            "🔬  Evaluación",
            "📞  Emergencias",
        ])

if not MODULOS_OK:
    st.error("Error al cargar módulos")
    st.code(DETALLE_ERROR)
    st.stop()

lista_usuarios = obtener_personas()
paciente = lista_usuarios[0] if lista_usuarios else {
    "nombre": "Paciente", "edad": "", "quien_avisar": "No asignado"
}

# ══════════════════════════════════════════════════════════════════════
# ADMIN
# ══════════════════════════════════════════════════════════════════════
if modo_medico:
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Panel de Gestión</h1>
            <p>Administración del paciente registrado en el sistema</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_form, col_img = st.columns([2, 1])
    with col_form:
        if lista_usuarios:
            st.success(f"Paciente activo: **{paciente['nombre']}**, {paciente['edad']} años")
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Nombre", value=paciente["nombre"])
            nueva_edad = c2.number_input("Edad", min_value=0, max_value=120, value=int(paciente["edad"] or 0))
            nuevo_avisar = st.text_input("Contacto de emergencia", value=paciente.get("quien_avisar", ""))
            if st.button("Guardar cambios"):
                if nuevo_nombre.strip():
                    actualizar_persona(paciente["id"], nuevo_nombre, int(nueva_edad), nuevo_avisar)
                    st.success("Guardado correctamente.")
                    st.rerun()
        else:
            st.warning("No hay paciente registrado.")
            nom = st.text_input("Nombre del paciente")
            ed = st.number_input("Edad", min_value=0, max_value=120, value=70)
            av = st.text_input("Contacto de emergencia")
            if st.button("Registrar paciente"):
                if nom.strip():
                    agregar_persona(nom, int(ed), av)
                    st.rerun()
    with col_img:
        try:
            st.image("Piccolo-IA.jpeg", use_container_width=True)
        except:
            pass

# ══════════════════════════════════════════════════════════════════════
# INICIO
# ══════════════════════════════════════════════════════════════════════
elif opcion == "🏠  Inicio":
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Bienvenido, {paciente['nombre']}</h1>
            <p>Tu asistente de medicamentos está listo para ayudarte</p>
            <span class="page-header-badge">🌿 Sistema Piccolo activo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_img, col_info = st.columns([1, 2], gap="large")

    with col_img:
        try:
            st.image("Piccolo-IA.jpeg", use_container_width=True,
                     caption="Piccolo — Enfermero Virtual")
        except:
            st.image("Piccolo-PNG-Picture.png", use_container_width=True)

    with col_info:
        st.markdown("""
        <div class="ficha-card">
            <h3 style="margin-bottom:16px; font-size:1.2rem;">Ficha del Paciente</h3>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="ficha-row"><span class="ficha-key">Nombre</span><span>{paciente['nombre']}</span></div>
            <div class="ficha-row"><span class="ficha-key">Edad</span><span>{paciente['edad']} años</span></div>
            <div class="ficha-row"><span class="ficha-key">Contacto</span><span>{paciente.get('quien_avisar','No asignado')}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Cómo usar Piccolo")
        st.write("Andá a **💬 Consultar**, presioná el micrófono y hablale sobre tus medicamentos o cómo te sentís. Piccolo te responde con texto y con voz.")

    st.markdown("---")
    st.markdown("### 💊 Medicamentos disponibles")
    from modules.db import obtener_todos_saberes
    saberes = obtener_todos_saberes()
    cols = st.columns(2)
    for i, s in enumerate(saberes):
        with cols[i % 2]:
            with st.expander(f"**{s['nombre_medicina']}**"):
                st.markdown(f"**Para qué sirve:** {s['para_que_sirve']}")
                st.markdown(f"**Consejo:** {s['consejo_amigable']}")
                st.markdown(f"**Cuidados:** {s['tener_cuidado']}")

# ══════════════════════════════════════════════════════════════════════
# CONSULTAR
# ══════════════════════════════════════════════════════════════════════
elif opcion == "💬  Consultar":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Consultar a Piccolo</h1>
            <p>Hablale por micrófono o escribí tu consulta</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_pic, col_chat = st.columns([1, 3], gap="large")

    with col_pic:
        try:
            st.image("Piccolo-PNG-Picture.png", use_container_width=True)
        except:
            pass
        st.markdown("""
        <div style="text-align:center; color:#7a9a82; font-size:0.82rem; margin-top:8px; font-style:italic;">
        Piccolo está escuchando
        </div>
        """, unsafe_allow_html=True)

    with col_chat:
        modo = st.radio("Modo de respuesta:",
            ["📝🔊 Texto y voz", "📝 Solo texto", "🔊 Solo voz"],
            horizontal=True)

        st.markdown("#### 🎤 Micrófono")
        audio_recibido = st.audio_input("Presioná para hablarle a Piccolo")
        mensaje_voz = ""

        if audio_recibido is not None:
            with st.spinner("Transcribiendo tu voz..."):
                try:
                    resultado_asr = transcribir_audio(audio_recibido.read(), idioma="es-AR")
                    if resultado_asr["exito"]:
                        mensaje_voz = resultado_asr["texto"]
                        st.success(f"Escuché: *{mensaje_voz}*")
                    else:
                        st.warning(f"{resultado_asr['error']}")
                except Exception as e:
                    st.warning(f"Error en micrófono: {e}")

        consulta = st.text_input("O escribí tu consulta:",
            value=mensaje_voz,
            placeholder="Ej: para qué sirve el enalapril / me tengo la presión en 15 9 / me duele la panza")

        if consulta:
            t0 = time.time()

            with st.spinner("Piccolo analiza tu consulta..."):
                try:
                    analisis = procesar_texto(consulta)
                    medicamento = analisis["medicamento_detectado"]
                    columna = analisis["columna_bd"]
                    entidades_json = analisis["entidades_json"]
                    intencion = analisis["intencion"]
                    pp = calcular_perplejidad(consulta, n=2, k=1.0)
                except Exception:
                    medicamento = None; columna = "que_hace"
                    entidades_json = "{}"; intencion = "desconocida"; pp = 0

            aviso = (f" Recordá que soy Piccolo, tu asistente virtual. "
                     "Para decisiones médicas importantes siempre consultá a tu médico.")
            respuesta = ""
            q = consulta.lower()

            # Diccionario local de malestares cotidianos (sin BD)
            MALESTARES = {
                "estomago": {
                    "claves": ["panza","duele la panza","me duele la panza","dolor de panza",
                               "indigestión","indigestion","pesadez","acidez","estomago","estómago","nausea","náusea"],
                    "respuesta": "Entiendo que te duele la panza. Te sugiero descansar de costado, prepararte un té de manzanilla y no comer nada pesado por unas horas. Si el dolor es muy fuerte o no mejora, avisale a tu contacto de confianza o llamá al médico."},
                "fiebre": {
                    "claves": ["fiebre","calentura","temperatura alta","escalofrios","escalofríos"],
                    "respuesta": "Con fiebre, abrígate lo justo y tomá agua fresca en sorbos pequeños. Anotá los números del termómetro para decírselos al médico."},
                "olvido": {
                    "claves": ["olvide","olvidé","no me acuerdo","me olvide","no sé si tomé"],
                    "respuesta": "Mirá el pastillero o el blíster para ver si falta la dosis de hoy. En caso de duda, esperá a la próxima dosis antes que tomar doble."},
                "mareo": {
                    "claves": ["mareo","mareado","me da vueltas","mareada","inestable"],
                    "respuesta": "Si te sentís mareado, sentate de inmediato en el sillón más cercano para evitar caídas. Respirá hondo y despacio hasta que pase."},
                "dolor": {
                    "claves": ["rodilla","espalda","cintura","duele el cuerpo","huesos","articulaciones"],
                    "respuesta": "Para ese dolor, evitá movimientos bruscos hoy. Una almohadilla tibia en la zona puede dar bastante alivio."},
                "cabeza": {
                    "claves": ["cabeza","jaqueca","migraña","migrana","dolor de cabeza"],
                    "respuesta": "Para el dolor de cabeza, descansá en un lugar tranquilo y oscuro. Tomá agua, muchas veces la deshidratación lo provoca."},
                "soledad": {
                    "claves": ["solo","sola","triste","asustado","asustada","miedo","angustia"],
                    "respuesta": "Entiendo cómo te sentís. No estás solo, Piccolo está acá. Si te sentís muy mal, llamá a tu familiar de confianza para charlar un ratito."},
            }

            # ── 1. TRIAJE INTELIGENTE DE PRESIÓN ARTERIAL (RE) ──
            valores_presion = re.findall(r'\b\d{2,3}\b', q)
            if "presión" in q or "presion" in q or len(valores_presion) >= 2:
                if len(valores_presion) >= 2:
                    sis = int(valores_presion[0])
                    dia = int(valores_presion[1])
                    
                    # Normalizar si el usuario dice 14 9 en lugar de 140 90
                    if sis < 30: sis *= 10
                    if dia < 20: dia *= 10
                    
                    if sis >= 180 or dia >= 120:
                        intencion = "ALERTA CRÍTICA"
                        respuesta = f"¡Atención! Tus valores de presión ({valores_presion[0]} e {valores_presion[1]}) están en un nivel CRÍTICO. Por favor, llamá de inmediato a emergencias médicas o a tu contacto de urgencia {paciente.get('quien_avisar','No asignado')}. Quedate sentado y tranquilo hasta que llegue ayuda."
                    elif sis >= 140 or dia >= 90:
                        intencion = "Presión Alta"
                        respuesta = f"Tenés la presión alta ({valores_presion[0]} e {valores_presion[1]}). Te aconsejo sentarte a descansar en un lugar fresco, respirar profundo y evitar cualquier esfuerzo. Si tomás medicación para la presión como el Enalapril, recordá si la tomaste hoy. Si no baja o te sentís mareado, avisale a un familiar."
                    else:
                        intencion = "Presión Normal"
                        respuesta = f"Tus valores de presión ({valores_presion[0]} e {valores_presion[1]}) se encuentran dentro de los rangos normales. ¡Excelente! Seguí cuidándote, tomando agua y disfrutando el día tranquilamente."
                else:
                    intencion = "Consulta Presión"
                    respuesta = "Si querés que evalúe tu presión arterial, por favor indicame los dos números que te dio el tensiómetro (por ejemplo: 'tengo la presión en 13 8' o '130 80')."

            # ── 2. FLUJO TRADICIONAL (MEDICAMENTOS O MALESTARES) ──
            elif medicamento:
                try:
                    resultado = obtener_dato_medicina(columna or "que_hace", medicamento)
                    if resultado and resultado[0]:
                        respuesta = f"Sobre el {medicamento.capitalize()}: {resultado[0]}"
                    else:
                        respuesta = f"Tengo registrado el {medicamento.capitalize()}, pero no encontré ese detalle específico."
                except:
                    respuesta = "Tuve un problema al consultar la base de datos."
            else:
                encontrado = False
                for _, info in MALESTARES.items():
                    if any(p in q for p in info["claves"]):
                        respuesta = info["respuesta"]
                        intencion = f"Sinto: {info['claves'][0]}"
                        encontrado = True
                        break
                if not encontrado:
                    try:
                        res_ir = buscar_en_indice(consulta, top_n=1)
                        if res_ir and res_ir[0]["similitud"] > 0.05:
                            m = res_ir[0]
                            respuesta = f"Esto puede relacionarse con {m['titulo']}: {m['snippet']}"
                        else:
                            respuesta = ("No reconocí un medicamento o síntoma específico. "
                                         "Podés consultarme por: enalapril, metformina, omeprazol, "
                                         "losartán, levotiroxina, atorvastatina, amlodipina, aspirina, furosemida o clonazepam.")
                    except:
                        respuesta = "No pude procesar la búsqueda en este momento."

            respuesta_final = respuesta + aviso
            tiempo_ms = int((time.time() - t0) * 1000)

            if "📝" in modo:
                st.markdown(f"""
                <div class="respuesta-card">
                    <div class="resp-label">Piccolo responde</div>
                    {respuesta_final}
                </div>
                """, unsafe_allow_html=True)

            if "🔊" in modo:
                with st.spinner("Generando respuesta de voz..."):
                    try:
                        audio_res = sintetizar_voz(respuesta_final)
                        if audio_res["exito"] and audio_res["audio_bytes"]:
                            st.audio(audio_res["audio_bytes"], format="audio/mp3")
                    except Exception as e_tts:
                        st.caption(f"Audio no disponible: {e_tts}")

            with st.expander("Ver detalle técnico del procesamiento"):
                d1, d2, d3 = st.columns(3)
                d1.metric("Intención detectada", intencion)
                d2.metric("Perplejidad", f"{pp:.2f}")
                d3.metric("Tiempo total", f"{tiempo_ms} ms")
                if medicamento:
                    st.caption(f"Entidad NER: **{medicamento}** → columna `{columna}`")

            # Persistencia estándar (sin mutaciones estructurales a piccolo.db)
            medicina_id = None
            if medicamento:
                med_row = obtener_medicina_por_nombre(medicamento)
                if med_row:
                    medicina_id = med_row["id"]
            guardar_conversacion(
                persona_id=paciente.get("id"),
                lo_que_dijo=consulta, lo_que_entendio=consulta,
                intencion=intencion, entidades_json=entidades_json,
                respuesta=respuesta_final, medicina_id=medicina_id,
                perplejidad=pp, tiempo_ms=tiempo_ms,
            )

        # Historial
        st.markdown("---")
        st.markdown("#### Historial reciente")
        historial = obtener_historial(persona_id=paciente.get("id"), limite=5)
        if historial:
            for h in historial:
                st.markdown(f"""
                <div class="hist-card">
                    <div class="hist-q">{h['lo_que_dijo']}<span class="hist-tag">{h['intencion'] or '?'}</span></div>
                    <div class="hist-r">{(h['respuesta'] or '')[:110]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay consultas registradas.")

# ══════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════
elif opcion == "📊  Dashboard":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Dashboard</h1>
            <p>Métricas reales del sistema en tiempo real</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    stats = obtener_estadisticas()
    historial_completo = obtener_historial(limite=500)

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-card"><div class="stat-val">{stats["total_charlas"] or 0}</div><div class="stat-label">💬 Consultas totales</div></div>', unsafe_allow_html=True)
    wer_v = f"{stats['wer_promedio']:.3f}" if stats['wer_promedio'] else "—"
    c2.markdown(f'<div class="stat-card"><div class="stat-val-accent">{wer_v}</div><div class="stat-label">📏 WER promedio</div></div>', unsafe_allow_html=True)
    pp_v = f"{stats['pp_promedio']:.1f}" if stats['pp_promedio'] else "—"
    c3.markdown(f'<div class="stat-card"><div class="stat-val">{pp_v}</div><div class="stat-label">🌀 Perplejidad prom.</div></div>', unsafe_allow_html=True)
    t_v = f"{stats['tiempo_promedio_ms']:.0f}" if stats['tiempo_promedio_ms'] else "—"
    c4.markdown(f'<div class="stat-card"><div class="stat-val-accent">{t_v} ms</div><div class="stat-label">⚡ Tiempo respuesta</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Top 10 consultas
    st.markdown("### 🔝 Top 10 Consultas Más Frecuentes")
    top10 = top_consultas(historial_completo, top_n=10)
    if top10:
        import pandas as pd
        df_top = pd.DataFrame(top10)
        df_top.columns = ["Consulta", "Veces"]
        st.bar_chart(df_top.set_index("Consulta")["Veces"])
        with st.expander("Ver tabla"):
            df_top.index = range(1, len(df_top)+1)
            st.dataframe(df_top, use_container_width=True)
    else:
        st.info("Hacé algunas consultas primero para ver el ranking.")

    st.markdown("---")
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("### 🎯 Distribución de Intenciones")
        if stats["intenciones_frecuentes"]:
            import pandas as pd, matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            df_int = pd.DataFrame(stats["intenciones_frecuentes"])
            fig, ax = plt.subplots(figsize=(6, 5))
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
            colores = ["#2d6645","#4a8c62","#6aac82","#c47c2e","#d4954a",
                       "#a8d5b5","#8bbfa0","#e8c090","#1c3a2e","#3a7d56"]
            wedges, texts, autotexts = ax.pie(
                df_int["total"], labels=df_int["intencion"],
                autopct="%1.0f%%", colors=colores[:len(df_int)],
                textprops={"color": "#1c3a2e", "fontsize": 8, "fontfamily": "sans-serif"}
            )
            for at in autotexts:
                at.set_color("white"); at.set_fontweight("bold")
            ax.set_title("Intenciones detectadas", color="#1c3a2e", fontsize=11, fontweight="bold")
            st.pyplot(fig); plt.close(fig)
        else:
            st.info("Sin datos aún.")

    with col_der:
        st.markdown("### 📅 Evolución Temporal")
        if stats["charlas_por_dia"]:
            import pandas as pd
            df_d = pd.DataFrame(stats["charlas_por_dia"])
            df_d["dia"] = pd.to_datetime(df_d["dia"])
            st.line_chart(df_d.set_index("dia")["total"])
        else:
            st.info("Sin datos aún.")

    st.markdown("---")
    st.markdown("### ☁️ Nube de Palabras")
    textos = [h["lo_que_dijo"] for h in historial_completo if h.get("lo_que_dijo")]
    if textos:
        with st.spinner("Generando nube..."):
            img = generar_nube_palabras(textos)
        if img:
            st.image(img, use_container_width=True)
    else:
        st.info("Hacé algunas consultas para generar la nube.")

    st.markdown("---")
    st.markdown("### 📋 Últimas 20 Consultas")
    if historial_completo:
        import pandas as pd
        filas = [{
            "Fecha": h.get("cuando","")[:16],
            "Consulta": (h.get("lo_que_dijo") or "")[:55],
            "Intención": h.get("intencion") or "—",
            "PP": f"{h['perplejidad']:.1f}" if h.get("perplejidad") else "—",
            "WER": f"{h['wer']:.3f}" if h.get("wer") else "—",
            "ms": h.get("tiempo_ms") or "—",
        } for h in historial_completo[:20]]
        st.dataframe(pd.DataFrame(filas), use_container_width=True)

    st.markdown("---")
    st.markdown("### 👑 Última Evaluación IR")
    ultima = stats["ultima_evaluacion"]
    if ultima:
        e1, e2, e3 = st.columns(3)
        e1.markdown(f'<div class="stat-card"><div class="stat-val">{ultima.get("f1",0) or 0:.3f}</div><div class="stat-label">F1 Score</div></div>', unsafe_allow_html=True)
        e2.markdown(f'<div class="stat-card"><div class="stat-val-accent">{ultima.get("precision_ir",0) or 0:.3f}</div><div class="stat-label">Precisión</div></div>', unsafe_allow_html=True)
        e3.markdown(f'<div class="stat-card"><div class="stat-val">{ultima.get("recall_ir",0) or 0:.3f}</div><div class="stat-label">Recall</div></div>', unsafe_allow_html=True)
    else:
        st.info("Corré la evaluación en la sección 🔬 para ver las métricas.")

# ══════════════════════════════════════════════════════════════════════
# EVALUACIÓN
# ══════════════════════════════════════════════════════════════════════
elif opcion == "🔬  Evaluación":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Evaluación del Sistema</h1>
            <p>WER · Perplejidad · P/R/F1 · Accuracy NER</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_wer, tab_pp, tab_ir, tab_ner = st.tabs([
        "📏 WER — Voz", "🌀 Perplejidad — N-gramas",
        "🔍 P/R/F1 — Búsqueda", "🏷️ Accuracy NER"
    ])

    with tab_wer:
        st.markdown("### Word Error Rate — Reconocimiento de Voz")
        frases = get_frases_prueba()
        st.write("Leé estas frases en voz alta e ingresá lo que transcribió el sistema:")
        for i, f in enumerate(frases, 1):
            st.write(f"**{i}.** *{f}*")
        st.markdown("---")
        import pandas as pd, statistics as stats_mod
        pares = []
        for i, ref in enumerate(frases[:10]):
            hip = st.text_input(f"Transcripción frase {i+1}:", key=f"wer_{i}", placeholder="lo que capturó el sistema")
            if hip.strip():
                pares.append({"#": i+1, "Referencia": ref, "Transcripción": hip, "WER": round(calcular_wer(ref, hip), 4)})
        if pares:
            df_w = pd.DataFrame(pares)
            st.dataframe(df_w, use_container_width=True)
            wer_lista = [p["WER"] for p in pares]
            c1, c2 = st.columns(2)
            c1.metric("WER Promedio", f"{stats_mod.mean(wer_lista):.4f}")
            c2.metric("Desviación Estándar", f"{stats_mod.stdev(wer_lista):.4f}" if len(wer_lista) > 1 else "—")

    with tab_pp:
        import pandas as pd
        st.markdown("### Perplejidad — Modelo N-gramas con suavizado Add-k")
        frases_test = [
            "para qué sirve el enalapril",
            "el omeprazol protege el estómago",
            "la levotiroxina se toma en ayunas",
            "tomo la metformina con la comida",
        ]
        # Resto de la lógica correspondiente a la sección de N-gramas...

# ══════════════════════════════════════════════════════════════════════
# EMERGENCIAS
# ══════════════════════════════════════════════════════════════════════
elif opcion == "📞  Emergencias":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Números de Emergencia</h1>
            <p>Acceso rápido a asistencia médica inmediata</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="emergencia-card">
            <div class="label">🚨 Emergencias Médicas</div>
            <div class="num">107</div>
            <p style="color:#c03030; margin-top:10px; font-weight:500;">Llamada gratuita nacional</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="contacto-card">
            <div class="label">📞 Contacto del Familiar Registrado</div>
            <div class="val" style="font-size:1.8rem; margin:15px 0;">{paciente.get('quien_avisar','No asignado')}</div>
            <p style="color:#4a7cca; font-weight:500;">Aviso inmediato en caso de malestar</p>
        </div>
        """, unsafe_allow_html=True)