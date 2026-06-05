# 🟠 Sistema Piccolo — Asistente de Medicamentos por Voz

> *"El conocimiento es poder. Y Piccolo tiene todo el conocimiento que necesitás sobre tus medicamentos."*

Asistente virtual de medicamentos orientado a adultos mayores, con interfaz de voz y texto, desarrollado con Python y Streamlit.

---

## 📋 Descripción del Proyecto

**Piccolo** es un asistente inteligente inspirado en el personaje de Dragon Ball que actúa como enfermero virtual. Permite a adultos mayores consultar información sobre sus medicamentos usando la voz, recibir respuestas habladas y gestionar recordatorios de dosis.

El sistema integra tres bloques de Procesamiento del Lenguaje Natural:
- **Bloque 1 — NLP:** Tokenización, POS tagging y NER (entidades: MEDICAMENTO, DOSIS, FRECUENCIA)
- **Bloque 2 — Modelos de Lenguaje:** N-gramas con suavizado Add-k y cálculo de perplejidad
- **Bloque 3 — Recuperación de Información:** Índice invertido con TF-IDF y similitud coseno

---

## 🗂️ Estructura del Proyecto

```
PICCOLO/
├── app.py                      ← Aplicación principal Streamlit
├── piccolo.db                  ← Base de datos SQLite (se crea automáticamente)
├── requirements.txt            ← Dependencias
├── README.md                   ← Este archivo
├── Piccolo-IA.jpeg             ← Imagen portada
├── Piccolo-PNG-Picture.png     ← Logo del personaje
│
├── modules/                    ← Módulos del sistema
│   ├── __init__.py
│   ├── db.py                   ← Capa de persistencia SQLite
│   ├── nlp.py                  ← Tokenización, NER, POS, intenciones
│   ├── ngrams.py               ← Modelo N-gramas + perplejidad
│   ├── search.py               ← Índice invertido TF-IDF + P/R/F1
│   ├── asr.py                  ← Reconocimiento de voz + WER
│   ├── tts.py                  ← Síntesis de voz (gTTS)
│   └── dashboard.py            ← Nube de palabras, top consultas, NER eval
│
├── data/                       ← Modelos persistidos (se genera automáticamente)
│   ├── ngram_bigrama.json
│   ├── ngram_trigrama.json
│   └── indice_invertido.json
│
└── tests/                      ← Scripts de evaluación
    ├── eval_wer.py             ← Evaluación WER del ASR
    ├── eval_search.py          ← Evaluación P/R/F1 del motor de búsqueda
    ├── eval_ner.py             ← Evaluación Accuracy del NER
    ├── resultados_wer.txt      ← Generado al correr eval_wer.py
    ├── resultados_search.txt   ← Generado al correr eval_search.py
    └── resultados_ner.txt      ← Generado al correr eval_ner.py
```

---

## ⚙️ Instalación

### Requisitos previos
- Python 3.10 o superior
- ffmpeg instalado en el sistema (necesario para el micrófono)

### Instalar ffmpeg (Windows)
```bash
winget install ffmpeg
```
Verificar con:
```bash
ffmpeg -version
```

### Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### Descargar modelo de spaCy en español
```bash
python -m spacy download es_core_news_sm
```

---

## ▶️ Cómo ejecutar

```bash
streamlit run app.py
```

La aplicación se abre en el navegador en `http://localhost:8501`

---

## 🔬 Correr las evaluaciones

Desde la carpeta raíz del proyecto:

```bash
# Evaluación WER (reconocimiento de voz)
python tests/eval_wer.py

# Evaluación P/R/F1 (motor de búsqueda)
python tests/eval_search.py

# Evaluación Accuracy NER (entidades)
python tests/eval_ner.py
```

Cada script genera un archivo `.txt` con los resultados detallados en la carpeta `tests/`.

---

## 🧠 Módulos del Sistema

### `modules/nlp.py` — Procesamiento del Lenguaje Natural
- **Tokenización** con spaCy (`es_core_news_sm`) o regex como fallback
- **POS tagging** con etiquetas Universal Dependencies
- **NER** — 3 entidades del dominio:
  - `MEDICAMENTO`: detectado por diccionario de 15 fármacos
  - `DOSIS`: patrón regex (`\d+ mg/ml/gr...`)
  - `FRECUENCIA`: patrón regex (`cada N horas`, `a la mañana`, etc.)
- **Detección de intención**: 8 intenciones clasificadas por palabras clave

### `modules/ngrams.py` — Modelo de Lenguaje N-gramas
- Entrena bigramas y trigramas sobre corpus del dominio (65 frases)
- **Suavizado Add-k** configurable (k = 0.01 a 5.0)
- Calcula **perplejidad** como métrica de adecuación al dominio
- Persiste el modelo entrenado en JSON

### `modules/search.py` — Motor de Recuperación de Información
- **Índice invertido** sobre 10 documentos (uno por medicamento)
- Pesos **TF-IDF** con suavizado logarítmico
- **Similitud coseno** para rankear resultados
- Evaluación con **P/R/F1** sobre 10 consultas etiquetadas
- Generación de **snippets** relevantes

### `modules/asr.py` — Reconocimiento de Voz
- Captura audio desde `st.audio_input()` (formato WebM/OGG)
- Convierte a WAV con `pydub` + `ffmpeg`
- Transcribe con **Google Web Speech API** vía `SpeechRecognition`
- Calcula **WER** con distancia de edición a nivel de palabras

### `modules/tts.py` — Síntesis de Voz
- Convierte texto a audio MP3 con **gTTS** en español argentino
- Devuelve bytes para reproducir directamente en Streamlit

---

## 🗄️ Base de Datos

SQLite con 5 tablas:

| Tabla | Descripción |
|---|---|
| `personas` | Pacientes registrados |
| `saberes_piccolo` | Conocimiento sobre 10 medicamentos |
| `alarmas_piccolo` | Recordatorios de dosis |
| `conversaciones` | Historial completo con métricas |
| `como_le_fue` | Sesiones de evaluación del sistema |

---

## 📊 Dashboard

El dashboard muestra en tiempo real:
- Métricas globales: consultas totales, WER, perplejidad, tiempo de respuesta
- Top 10 consultas más frecuentes
- Distribución de intenciones (gráfico de torta)
- Evolución temporal de consultas (líneas)
- Métricas P/R/F1 de la última evaluación
- Nube de palabras de términos más buscados
- Tabla de las últimas 20 consultas con detalle

---

## 💊 Medicamentos disponibles

| Medicamento | Condición |
|---|---|
| Enalapril | Presión alta |
| Metformina | Diabetes tipo 2 |
| Atorvastatina | Colesterol alto |
| Omeprazol | Acidez / Gastritis |
| Losartán | Presión alta |
| Levotiroxina | Hipotiroidismo |
| Amlodipina | Presión alta / Angina |
| Aspirina 100mg | Cuidado del corazón |
| Furosemida | Retención de líquido |
| Clonazepam | Ansiedad / Epilepsia |

---

## 👥 Integrantes del equipo

> Completar con los nombres del grupo

---

## 📚 Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.10+ | Lenguaje principal |
| Streamlit | Interfaz web |
| SQLite | Base de datos |
| spaCy | NLP (tokenización, POS) |
| SpeechRecognition | ASR (Google Speech API) |
| pydub + ffmpeg | Conversión de audio |
| gTTS | Text-to-Speech |
| wordcloud | Nube de palabras |
| matplotlib | Gráficos |
| pandas | Manejo de datos |


