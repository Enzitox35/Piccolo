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

/* ── Paleta PowerPoint Piccolo ──────────────────────────────
   Verde oscuro  #1C3A2E   (base sidebar / headers)
   Verde medio   #2D6645   (accents, bordes)
   Verde PPT     #70AD47   (accent6)
   Naranja PPT   #ED7D31   (accent2)
   Dorado PPT    #FFC000   (accent4)
   Gris azulado  #44546A   (dk2)
   ──────────────────────────────────────────────────────── */

*, html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background: #f2f5f2; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1C3A2E 0%, #243d30 60%, #1a3328 100%);
    border-right: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.18);
}
section[data-testid="stSidebar"] * { color: #d4e8d8 !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem !important; padding: 6px 0 !important; font-weight: 500 !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }

/* ── PAGE HEADER ── */
.page-header {
    background: linear-gradient(135deg, #1C3A2E 0%, #2D6645 55%, #3a7d56 100%);
    border-radius: 20px; padding: 32px 40px; margin-bottom: 28px; color: white;
    box-shadow: 0 8px 32px rgba(28,58,46,0.25);
    border-left: 6px solid #ED7D31;
}
.page-header-text h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.2rem !important; color: #ffffff !important;
    margin: 0 !important; letter-spacing: 0.5px !important;
}
.page-header-text p { color: rgba(255,255,255,0.75); font-size: 1rem; margin: 6px 0 0; font-weight: 300; }
.page-header-badge {
    background: rgba(237,125,49,0.25); border: 1px solid #ED7D31;
    border-radius: 12px; padding: 8px 16px; font-size: 0.8rem;
    color: #FFD09B !important; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; margin-top: 10px; display: inline-block;
}

/* ── FICHA DEL PACIENTE ── */
.ficha-wrapper {
    background: white;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(28,58,46,0.10);
    overflow: hidden;
}
.ficha-header {
    background: linear-gradient(135deg, #1C3A2E 0%, #2D6645 100%);
    padding: 18px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.ficha-header-icon {
    background: rgba(237,125,49,0.25);
    border: 2px solid #ED7D31;
    border-radius: 50%;
    width: 46px; height: 46px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
}
.ficha-header-title {
    font-size: 1.1rem;
    color: #ffffff;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.3px;
}
.ficha-header-sub {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.55);
    margin: 3px 0 0;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.ficha-body { padding: 0; }
.ficha-row {
    display: flex;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #f0f4f0;
    gap: 16px;
    transition: background 0.15s;
}
.ficha-row:last-child { border-bottom: none; }
.ficha-row:nth-child(even) { background: #fafcfa; }
.ficha-icon-col {
    width: 38px; height: 38px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
}
.ficha-icon-verde   { background: #e8f5e0; }
.ficha-icon-naranja { background: #fff0e6; }
.ficha-icon-dorado  { background: #fff8e1; }
.ficha-text-col { flex: 1; min-width: 0; }
.ficha-key {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #7a9a82;
    margin-bottom: 4px;
}
.ficha-val {
    font-size: 1.05rem;
    font-weight: 600;
    color: #1C3A2E;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.ficha-badge {
    display: inline-block;
    background: linear-gradient(135deg, #ED7D31, #FFC000);
    color: white;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-left: 8px;
    vertical-align: middle;
}

/* ── STAT CARDS ── */
.stat-card {
    background: white; border-radius: 16px; padding: 24px 20px;
    text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-top: 4px solid #70AD47;
}
.stat-card .stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem; color: #1C3A2E; font-weight: 700; line-height: 1;
}
.stat-card .stat-val-accent {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem; color: #ED7D31; font-weight: 700; line-height: 1;
}
.stat-card .stat-label {
    font-size: 0.75rem; color: #7a9a82; text-transform: uppercase;
    letter-spacing: 1.5px; margin-top: 8px; font-weight: 600;
}

/* ── RESPUESTA CARD ── */
.respuesta-card {
    background: white; border-radius: 16px; padding: 24px 28px; margin: 20px 0;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07); border-left: 5px solid #2D6645;
    font-size: 1.05rem; line-height: 1.8; color: #2a3d2e;
}
.respuesta-card .resp-label {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px;
    color: #ED7D31; font-weight: 700; margin-bottom: 10px;
}

/* ── HIST CARD ── */
.hist-card {
    background: white; border-radius: 12px; padding: 14px 18px;
    margin: 8px 0; box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    border-left: 3px solid #70AD47;
}
.hist-card .hist-q { font-weight: 600; color: #1C3A2E; font-size: 0.95rem; }
.hist-card .hist-tag {
    display: inline-block; background: #fff0e6; color: #ED7D31;
    border-radius: 20px; padding: 2px 10px; font-size: 0.72rem;
    font-weight: 700; margin-left: 8px; border: 1px solid #ED7D31;
}
.hist-card .hist-r { color: #5a7a62; font-size: 0.88rem; margin-top: 4px; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #1C3A2E, #2D6645) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #ED7D31, #FFC000) !important;
    transform: translateY(-1px) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input {
    background: white !important; border: 1.5px solid #c5ddc9 !important;
    border-radius: 10px !important; color: #1C3A2E !important;
}

/* ── HEADINGS ── */
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #1C3A2E !important; }

/* ── SIDEBAR BRAND ── */
.sidebar-brand {
    padding: 20px 10px 24px; text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 16px;
}
.sidebar-brand .brand-name {
    font-family: 'Playfair Display', serif; font-size: 1.8rem;
    color: #a8d5b5 !important; font-weight: 700;
}
.sidebar-brand .brand-sub {
    font-size: 0.75rem; color: rgba(168,213,181,0.7) !important;
    text-transform: uppercase; letter-spacing: 2px; margin-top: 4px;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: white !important; border-radius: 10px !important; padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; color: #5a7a62 !important; font-weight: 600 !important;
}
.stTabs [aria-selected="true"] { background: #1C3A2E !important; color: white !important; }

/* ── EMERGENCIAS ── */
.emergencia-card {
    background: linear-gradient(135deg, #fff5f5, #ffe8e8);
    border: 2px solid #e05050; border-radius: 16px; padding: 24px; text-align: center;
}
.emergencia-card .num {
    font-family: 'Playfair Display', serif; font-size: 3rem; color: #c03030; font-weight: 700;
}
.emergencia-card .label {
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px;
    color: #c03030; font-weight: 700;
}
.contacto-card {
    background: linear-gradient(135deg, #fff8f0, #fff0e6);
    border: 2px solid #ED7D31; border-radius: 16px; padding: 24px; text-align: center;
}
.contacto-card .label {
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px;
    color: #ED7D31; font-weight: 700; margin-bottom: 8px;
}
.contacto-card .val { font-size: 1.2rem; color: #1C3A2E; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── INIT ─────────────────────────────────────────────────────────────
if MODULOS_OK:
    crear_base_datos()
    cargar_saberes_iniciales()

    @st.cache_resource
    def _init_recursos():
        motor = get_motor()
        modelo = get_modelo(n=2, k=1.0)
        return motor, modelo

    motor_busqueda, modelo_bigrama = _init_recursos()

# ══════════════════════════════════════════════════════════════════════
# BARRA LATERAL (SIDEBAR)
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <span style="font-size: 40px; font-weight: bold; color: #a8d5b5; vertical-align: middle;">Piccolo</span>
    </div>
    """, unsafe_allow_html=True)
    # 🏛️ DESCARGO DE RESPONSABILIDAD PEDIDO POR EL PROFESOR
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(237,125,49,0.12) 0%, rgba(255,192,0,0.08) 100%);
        border: 1px solid rgba(237,125,49,0.45);
        border-left: 4px solid #ED7D31;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 6px 0 14px;
    ">
        <div style="
            font-size: 0.65rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #FFC000 !important;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        ">🏛️ Trabajo Institucional Académico</div>
        <div style="
            font-size: 0.78rem;
            color: rgba(212,232,216,0.9) !important;
            line-height: 1.55;
        ">
            Proyecto de práctica educativa. La información es de uso
            <strong style='color:#FFD09B !important;'>exclusivamente académico</strong>
            y <strong style='color:#FFD09B !important;'>no tiene fines médicos.</strong>
        </div>
        <div style="
            margin-top: 10px;
            padding-top: 9px;
            border-top: 1px solid rgba(237,125,49,0.25);
            font-size: 0.72rem;
            color: rgba(212,232,216,0.65) !important;
            font-style: italic;
        ">
            No reemplaza diagnóstico ni prescripción profesional.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

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
        opcion = st.radio(
            "Menú de navegación",
            ["🏠  Inicio", "💬  Consultar", "📊  Dashboard", "🔬  Evaluación", "📞  Emergencias"],
            label_visibility="collapsed"
        )

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
            st.image("Piccolo-IA.jpeg", use_container_width=True, caption="Piccolo — Enfermero Virtual")
        except:
            try:
                st.image("Piccolo-PNG-Picture.png", use_container_width=True)
            except:
                pass

    with col_info:
        edad_val = paciente.get('edad', '') or ''
        contacto_val = paciente.get('quien_avisar', 'No asignado') or 'No asignado'
        st.markdown(f"""
        <div class="ficha-wrapper">
            <div class="ficha-header">
                <div class="ficha-header-icon">🧑‍⚕️</div>
                <div>
                    <div class="ficha-header-title">Ficha del Paciente</div>
                    <div class="ficha-header-sub">Datos registrados en el sistema</div>
                </div>
            </div>
            <div class="ficha-body">
                <div class="ficha-row">
                    <div class="ficha-icon-col ficha-icon-verde">👤</div>
                    <div class="ficha-text-col">
                        <div class="ficha-key">Nombre completo</div>
                        <div class="ficha-val">{paciente['nombre']}</div>
                    </div>
                </div>
                <div class="ficha-row">
                    <div class="ficha-icon-col ficha-icon-naranja">🎂</div>
                    <div class="ficha-text-col">
                        <div class="ficha-key">Edad</div>
                        <div class="ficha-val">
                            {edad_val} años &nbsp;<span class="ficha-badge">Adulto Mayor</span>
                        </div>
                    </div>
                </div>
                <div class="ficha-row">
                    <div class="ficha-icon-col ficha-icon-dorado">📞</div>
                    <div class="ficha-text-col">
                        <div class="ficha-key">Contacto de emergencia</div>
                        <div class="ficha-val">{contacto_val}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Cómo usar Piccolo")
        st.write("Andá a **💬 Consultar**, presioná el micrófono y hablale sobre tus medicamentos o cómo te sentís.")

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
        st.markdown('<div style="text-align:center; color:#7a9a82; font-size:0.82rem; margin-top:8px; font-style:italic;">Piccolo está escuchando</div>', unsafe_allow_html=True)

    with col_chat:
        modo = st.radio("Modo de respuesta:", ["📝🔊 Texto y voz", "📝 Solo texto", "🔊 Solo voz"], horizontal=True)

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

        consulta = st.text_input("O escribí tu consulta:", value=mensaje_voz,
            placeholder="Ej: para qué sirve el enalapril / me tengo la presión en 15 9")

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

            aviso = " Recordá que soy Piccolo, tu asistente virtual. Para decisiones médicas importantes siempre consultá a tu médico."
            respuesta = ""
            q = consulta.lower()

            MALESTARES = {
                "estomago": {"claves": ["panza","duele la panza","me duele la panza","dolor de panza","indigestión","acidez","estomago","estómago","nausea","náusea"], "respuesta": "Entiendo que te duele la panza. Te sugiero descansar de costado, prepararte un té de manzanilla y no comer nada pesado por unas horas."},
                "fiebre": {"claves": ["fiebre","calentura","temperatura alta","escalofrios"], "respuesta": "Con fiebre, abrígate lo justo y tomá agua fresca en sorbos pequeños."},
                "olvido": {"claves": ["olvide","olvidé","no me acuerdo","me olvide","no sé si tomé"], "respuesta": "Mirá el pastillero o el blíster para ver si falta la dosis de hoy. En caso de duda, esperá a la próxima dosis antes que tomar doble."},
                "mareo": {"claves": ["mareo","mareado","me da vueltas","mareada"], "respuesta": "Si te sentís mareado, sentate de inmediato en el sillón más cercano para evitar caídas."},
                "dolor": {"claves": ["rodilla","espalda","cintura","duele el cuerpo","huesos"], "respuesta": "Para ese dolor, evitá movimientos bruscos hoy. Una almohadilla tibia en la zona puede dar bastante alivio."},
                "cabeza": {"claves": ["cabeza","jaqueca","migraña","dolor de cabeza"], "respuesta": "Para el dolor de cabeza, descansá en un lugar tranquilo y oscuro. Tomá agua."},
                "soledad": {"claves": ["solo","sola","triste","asustado","asustada","miedo","angustia"], "respuesta": "Entiendo cómo te sentís. No estás solo, Piccolo está acá."},
            }

            valores_presion = re.findall(r'\b\d{2,3}\b', q)
            if "presión" in q or "presion" in q or len(valores_presion) >= 2:
                if len(valores_presion) >= 2:
                    sis = int(valores_presion[0])
                    dia = int(valores_presion[1])
                    if sis < 30: sis *= 10
                    if dia < 20: dia *= 10
                    if sis >= 180 or dia >= 120:
                        intencion = "ALERTA CRÍTICA"
                        respuesta = f"¡Atención! Tus valores de presión están en un nivel CRÍTICO. Por favor, llamá de inmediato a emergencias médicas o a tu contacto de urgencia {paciente.get('quien_avisar','No asignado')}."
                    elif sis >= 140 or dia >= 90:
                        intencion = "Presión Alta"
                        respuesta = f"Tenés la presión alta ({valores_presion[0]}/{valores_presion[1]}). Te aconsejo sentarte a descansar en un lugar fresco y respirar profundo."
                    else:
                        intencion = "Presión Normal"
                        respuesta = f"Tus valores de presión ({valores_presion[0]}/{valores_presion[1]}) se encuentran dentro de los rangos normales. ¡Excelente!"
                else:
                    intencion = "Consulta Presión"
                    respuesta = "Si querés que evalúe tu presión, indicame los dos números del tensiómetro (ej: '130 80')."
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
                            respuesta = "No reconocí un medicamento o síntoma específico. Podés consultarme por: enalapril, metformina, omeprazol, losartán, levotiroxina, atorvastatina, amlodipina, aspirina, furosemida o clonazepam."
                    except:
                        respuesta = "No pude procesar la búsqueda en este momento."

            respuesta_final = respuesta + aviso
            tiempo_ms = int((time.time() - t0) * 1000)

            if "📝" in modo:
                st.markdown(f'<div class="respuesta-card"><div class="resp-label">🌿 Piccolo responde</div>{respuesta_final}</div>', unsafe_allow_html=True)

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

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-card"><div class="stat-val">{stats["total_charlas"] or 0}</div><div class="stat-label">💬 Consultas totales</div></div>', unsafe_allow_html=True)
    wer_v = f"{stats['wer_promedio']:.3f}" if stats['wer_promedio'] else "—"
    c2.markdown(f'<div class="stat-card"><div class="stat-val-accent">{wer_v}</div><div class="stat-label">📏 WER promedio</div></div>', unsafe_allow_html=True)
    pp_v = f"{stats['pp_promedio']:.1f}" if stats['pp_promedio'] else "—"
    c3.markdown(f'<div class="stat-card"><div class="stat-val">{pp_v}</div><div class="stat-label">🌀 Perplejidad prom.</div></div>', unsafe_allow_html=True)
    t_v = f"{stats['tiempo_promedio_ms']:.0f}" if stats['tiempo_promedio_ms'] else "—"
    c4.markdown(f'<div class="stat-card"><div class="stat-val-accent">{t_v} ms</div><div class="stat-label">⚡ Tiempo respuesta</div></div>', unsafe_allow_html=True)

    st.markdown("---")
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
            colores = ["#2D6645","#70AD47","#ED7D31","#FFC000","#1C3A2E","#44546A","#a8d5b5","#FFD09B","#3a7d56","#6aac82"]
            wedges, texts, autotexts = ax.pie(
                df_int["total"], labels=df_int["intencion"],
                autopct="%1.0f%%", colors=colores[:len(df_int)],
                textprops={"color": "#1C3A2E", "fontsize": 8}
            )
            for at in autotexts:
                at.set_color("white"); at.set_fontweight("bold")
            ax.set_title("Intenciones detectadas", color="#1C3A2E", fontsize=11, fontweight="bold")
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
            "ms": h.get("tiempo_ms") or "—",
        } for h in historial_completo[:20]]
        st.dataframe(pd.DataFrame(filas), use_container_width=True)

    st.markdown("---")
    st.markdown("### 👑 Última Evaluación del Motor de Búsqueda (IR)")
    ultima = stats.get("ultima_evaluacion")
    if ultima:
        e1, e2, e3 = st.columns(3)
        e1.markdown(f'<div class="stat-card"><div class="stat-val">{ultima.get("f1",0):.3f}</div><div class="stat-label">F1 Score</div></div>', unsafe_allow_html=True)
        e2.markdown(f'<div class="stat-card"><div class="stat-val-accent">{ultima.get("precision_ir",0):.3f}</div><div class="stat-label">Precisión</div></div>', unsafe_allow_html=True)
        e3.markdown(f'<div class="stat-card"><div class="stat-val">{ultima.get("recall_ir",0):.3f}</div><div class="stat-label">Recall</div></div>', unsafe_allow_html=True)
    else:
        st.info("No hay evaluaciones guardadas todavía. Podés correr una desde la pestaña Evaluación.")

# ══════════════════════════════════════════════════════════════════════
# EVALUACIÓN DEL SISTEMA
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
        "📏 WER — Voz",
        "🌀 Perplejidad — N-gramas",
        "🔍 P/R/F1 — Búsqueda",
        "🏷️ Accuracy NER",
    ])

    with tab_wer:
        st.markdown("### Word Error Rate — Reconocimiento de Voz")
        frases = get_frases_prueba()
        st.write("Leé estas frases en voz alta e ingresá lo que transcribió el sistema:")
        for i, f in enumerate(frases, 1):
            st.write(f"**{i}.** *{f}*")
        st.markdown("---")

        import pandas as pd
        import statistics as stats_mod

        pares = []
        for i, ref in enumerate(frases[:10]):
            hip = st.text_input(
                f"Transcripción frase {i+1}:",
                key=f"wer_{i}",
                placeholder="lo que capturó el sistema"
            )
            if hip.strip():
                pares.append({
                    "#": i+1,
                    "Referencia": ref,
                    "Transcripción": hip,
                    "WER": round(calcular_wer(ref, hip), 4)
                })

        if pares:
            df_w = pd.DataFrame(pares)
            st.dataframe(df_w, use_container_width=True)
            wer_lista = [p["WER"] for p in pares]
            c1, c2 = st.columns(2)
            c1.metric("WER Promedio", f"{stats_mod.mean(wer_lista):.4f}")
            c2.metric("Desviación Estándar",
                      f"{stats_mod.stdev(wer_lista):.4f}" if len(wer_lista) > 1 else "—")
        else:
            st.info("💡 Escribí una transcripción arriba para calcular el WER.")

    with tab_pp:
        st.markdown("### Perplejidad — Modelo N-gramas con suavizado Add-k")

        import pandas as pd
        import statistics as stats_mod

        try:
            modelo_pp = get_modelo(n=2, k=1.0)
            modelo_ok = modelo_pp.entrenado
        except Exception as e_mod:
            modelo_ok = False
            st.error(f"Error cargando modelo: {e_mod}")

        if not modelo_ok:
            st.warning("El modelo no está entrenado. Entrenando ahora...")
            try:
                from modules.ngrams import reentrenar
                modelo_pp, _ = reentrenar(k=1.0)
                modelo_ok = True
                st.success("Modelo entrenado correctamente.")
            except Exception as e_train:
                st.error(f"No se pudo entrenar: {e_train}")

        if modelo_ok:
            frases_test = [
                "para qué sirve el enalapril",
                "el omeprazol protege el estómago",
                "la levotiroxina se toma en ayunas",
                "tomo la metformina con la comida",
                "hoy hace mucho calor afuera",
                "el gato subió al árbol del parque",
            ]

            st.write("**Frases del dominio vs fuera del dominio:**")
            resultados_pp = []
            for f in frases_test:
                try:
                    pp_val = modelo_pp.perplejidad(f)
                except Exception:
                    pp_val = 9999.0
                resultados_pp.append({
                    "Frase": f,
                    "Perplejidad": round(pp_val, 2),
                    "¿Del dominio?": "✅ Sí" if pp_val < 200 else "❌ No"
                })

            df_pp = pd.DataFrame(resultados_pp)
            st.dataframe(df_pp, use_container_width=True)

            pp_valores = [r["Perplejidad"] for r in resultados_pp]
            st.metric("Perplejidad Promedio", f"{stats_mod.mean(pp_valores):.2f}")

            st.markdown("---")
            st.markdown("**Top-10 bigramas para 'enalapril':**")
            try:
                top = modelo_pp.top_bigramas_por_contexto("enalapril", top_n=10)
                if top:
                    st.dataframe(
                        pd.DataFrame(top)[["contexto", "siguiente", "conteo", "probabilidad"]],
                        use_container_width=True
                    )
                else:
                    st.info("No se encontraron bigramas para 'enalapril'.")
            except Exception as e_top:
                st.warning(f"Error obteniendo bigramas: {e_top}")

            st.markdown("---")
            st.markdown("**Probar con otra frase:**")
            frase_custom = st.text_input("Escribí una frase para calcular su perplejidad:",
                                          placeholder="Ej: para qué sirve el omeprazol")
            if frase_custom:
                try:
                    pp_custom = modelo_pp.perplejidad(frase_custom)
                    dominio = "✅ Del dominio" if pp_custom < 200 else "❌ Fuera del dominio"
                    st.metric(f"Perplejidad de '{frase_custom}'", f"{pp_custom:.2f}", delta=dominio)
                except Exception as e_custom:
                    st.error(f"Error: {e_custom}")

            st.markdown("---")
            k_val = st.slider("Probar suavizado Add-k con k =", 0.01, 5.0, 1.0, 0.01)
            if st.button("Calcular perplejidad con este k", key="btn_pp_k"):
                try:
                    m_temp = ModeloNGramas(n=2, k=k_val)
                    m_temp.entrenar(preparar_corpus(CORPUS_PICCOLO))
                    frase_d = "para qué sirve el enalapril"
                    pp_k = m_temp.perplejidad(frase_d)
                    st.metric(f"PP de '{frase_d}' con k={k_val}", f"{pp_k:.4f}")
                except Exception as e_k:
                    st.error(f"Error: {e_k}")

    with tab_ir:
        st.markdown("### Evaluación del Motor de Búsqueda — P / R / F1")
        st.write("Presioná el botón para evaluar el motor sobre las consultas de prueba etiquetadas.")

        if st.button("▶ Ejecutar Evaluación IR", key="btn_evaluar_ir"):
            with st.spinner("Calculando precisión, recall y F1-score..."):
                try:
                    if not motor_busqueda.construido:
                        motor_busqueda.construir_indice()
                    eval_res = evaluar_motor(motor_busqueda, top_n=3)
                    st.session_state["ultima_eval_ir"] = eval_res
                    stats_act = obtener_estadisticas()
                    guardar_evaluacion(
                        total_charlas=stats_act["total_charlas"],
                        f1=eval_res["f1_promedio"],
                        precision_ir=eval_res["precision_promedio"],
                        recall_ir=eval_res["recall_promedio"],
                    )
                    st.success("✅ Evaluación completada y guardada.")
                except Exception as e_ir:
                    st.error(f"Error en evaluación IR: {e_ir}")

        if "ultima_eval_ir" in st.session_state:
            ev = st.session_state["ultima_eval_ir"]
            ir1, ir2, ir3 = st.columns(3)
            ir1.metric("Precisión", f"{ev['precision_promedio']:.4f}")
            ir2.metric("Recall", f"{ev['recall_promedio']:.4f}")
            ir3.metric("F1-Score", f"{ev['f1_promedio']:.4f}")

            import pandas as pd
            st.dataframe(pd.DataFrame(ev["detalle"]), use_container_width=True)
        else:
            st.info("💡 Presioná el botón para calcular las métricas.")

    with tab_ner:
        st.markdown("### Accuracy NER — Reconocimiento de Entidades")
        st.write("Evaluación sobre 20 ejemplos anotados manualmente (MEDICAMENTO, DOSIS, FRECUENCIA).")

        if st.button("▶ Evaluar NER", key="btn_evaluar_ner"):
            with st.spinner("Calculando accuracy..."):
                try:
                    resultado_ner = calcular_accuracy_ner(EJEMPLOS_NER)
                    st.session_state["resultado_ner"] = resultado_ner
                except Exception as e_ner:
                    st.error(f"Error en evaluación NER: {e_ner}")

        if "resultado_ner" in st.session_state:
            resultado_ner = st.session_state["resultado_ner"]

            st.metric("Accuracy Global NER", f"{resultado_ner['accuracy_global']:.1%}")
            st.write(f"Correctas: **{resultado_ner['correctos']}** / {resultado_ner['total']} entidades")

            import pandas as pd
            filas_tipo = [
                {"Tipo de Entidad": tipo, "Accuracy": f"{acc:.1%}"}
                for tipo, acc in resultado_ner["accuracy_por_tipo"].items()
            ]
            st.dataframe(pd.DataFrame(filas_tipo), use_container_width=True)

            from modules.nlp import extraer_entidades
            with st.expander("Ver detalle de los 20 ejemplos"):
                det = [{
                    "Texto": e["texto"],
                    "Esperadas": str(e["entidades_esperadas"]),
                    "Obtenidas": str({k: v for k, v in extraer_entidades(e["texto"]).items() if v})
                } for e in EJEMPLOS_NER]
                st.dataframe(pd.DataFrame(det), use_container_width=True)
        else:
            st.info("💡 Presioná el botón para calcular la accuracy NER.")

# ══════════════════════════════════════════════════════════════════════
# EMERGENCIAS
# ══════════════════════════════════════════════════════════════════════
elif opcion == "📞  Emergencias":
    st.markdown("""
    <div class="page-header">
        <div class="page-header-text">
            <h1>Contactos de Emergencia</h1>
            <p>Asistencia inmediata ante situaciones críticas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="emergencia-card">
            <div class="num">107</div>
            <div class="label">Emergencias Médicas (SAME)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="contacto-card">
            <div class="label">Contacto de Confianza Guardado</div>
            <div class="val">{paciente.get('quien_avisar','No asignado')}</div>
        </div>
        """, unsafe_allow_html=True)
