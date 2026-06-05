"""
modules/asr.py — Reconocimiento Automático del Habla (ASR)
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Implementa:
- Captura de audio desde el micrófono (vía Streamlit st.audio_input)
- Transcripción con SpeechRecognition (Google Web Speech API)
- Medición de WER (Word Error Rate)
- Frases de prueba para evaluación
"""

import io
import time
import difflib
import speech_recognition as sr

# =========================
# FRASES DE REFERENCIA PARA MEDIR WER
# (10 frases de prueba del dominio medicamentos)
# =========================
FRASES_REFERENCIA = [
    "para qué sirve el enalapril",
    "cuándo tengo que tomar la metformina",
    "qué cuidados tengo que tener con el omeprazol",
    "qué hace el losartán en el cuerpo",
    "dame un consejo para tomar la levotiroxina",
    "para qué es la atorvastatina",
    "tengo que tomar la aspirina con comida",
    "qué tipo de medicamento es el clonazepam",
    "para quién es la furosemida",
    "qué cuidados tiene la amlodipina",
]


# =========================
# TRANSCRIPCIÓN DESDE BYTES DE AUDIO
# =========================
def transcribir_audio(audio_bytes: bytes, idioma: str = "es-AR") -> dict:
    """
    Recibe bytes de audio (WAV) y devuelve la transcripción.
    
    Returns:
        dict con 'texto', 'exito', 'error', 'tiempo_ms'
    """
    resultado = {
        "texto": "",
        "exito": False,
        "error": None,
        "tiempo_ms": 0,
    }

    recognizer = sr.Recognizer()
    inicio = time.time()

    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        texto = recognizer.recognize_google(audio_data, language=idioma)
        resultado["texto"] = texto.lower().strip()
        resultado["exito"] = True

    except sr.UnknownValueError:
        resultado["error"] = "No se pudo entender el audio. Hablá más cerca del micrófono."
    except sr.RequestError as e:
        resultado["error"] = f"Error al conectar con el servicio de reconocimiento: {e}"
    except Exception as e:
        resultado["error"] = f"Error inesperado: {e}"
    finally:
        resultado["tiempo_ms"] = int((time.time() - inicio) * 1000)

    return resultado


# =========================
# CÁLCULO DE WER
# =========================
def calcular_wer(referencia: str, hipotesis: str) -> float:
    """
    Calcula el Word Error Rate (WER) entre la transcripción de referencia
    y la hipótesis (lo que transcribió el ASR).
    
    WER = (S + D + I) / N
    S = sustituciones, D = eliminaciones, I = inserciones, N = palabras en referencia
    
    Implementado con distancia de edición a nivel de palabras.
    """
    ref_words = referencia.lower().strip().split()
    hyp_words = hipotesis.lower().strip().split()

    n = len(ref_words)
    if n == 0:
        return 0.0

    # Matriz de distancia de edición
    d = [[0] * (len(hyp_words) + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, len(hyp_words) + 1):
            costo = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,       # eliminación
                d[i][j - 1] + 1,       # inserción
                d[i - 1][j - 1] + costo  # sustitución
            )

    return round(d[n][len(hyp_words)] / n, 4)


def evaluar_wer_batch(pares: list[tuple]) -> dict:
    """
    Evalúa WER sobre una lista de (referencia, hipotesis).
    
    Returns:
        dict con 'wer_por_frase', 'wer_promedio', 'wer_std'
    """
    import statistics

    wer_lista = []
    detalle = []

    for ref, hip in pares:
        wer = calcular_wer(ref, hip)
        wer_lista.append(wer)
        detalle.append({
            "referencia": ref,
            "hipotesis": hip,
            "wer": wer
        })

    return {
        "wer_por_frase": detalle,
        "wer_promedio": round(statistics.mean(wer_lista), 4) if wer_lista else 0.0,
        "wer_std": round(statistics.stdev(wer_lista), 4) if len(wer_lista) > 1 else 0.0,
    }


# =========================
# FRASES DE PRUEBA PARA DEMO
# =========================
def get_frases_prueba() -> list[str]:
    """Devuelve las frases de referencia para que el usuario las lea en voz alta."""
    return FRASES_REFERENCIA


if __name__ == "__main__":
    # Test de WER
    ref = "para qué sirve el enalapril"
    hip = "para que sirve el enalapril"
    print(f"WER entre '{ref}' y '{hip}': {calcular_wer(ref, hip)}")

    ref2 = "para qué sirve el enalapril"
    hip2 = "para que sirbe el napril"
    print(f"WER entre '{ref2}' y '{hip2}': {calcular_wer(ref2, hip2)}")
