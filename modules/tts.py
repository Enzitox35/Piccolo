"""
modules/tts.py — Síntesis de Voz (TTS)
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Implementa:
- Síntesis de texto a voz con gTTS en español
- Opciones de salida: texto, audio, o ambas
- Generación de bytes de audio para reproducir en Streamlit
"""

import io
import time
from gtts import gTTS


def sintetizar_voz(texto: str, idioma: str = "es") -> dict:
    """
    Convierte texto a audio MP3 usando gTTS.
    
    Args:
        texto: Texto a sintetizar
        idioma: Código de idioma (default: 'es' para español)
    
    Returns:
        dict con 'audio_bytes' (bytes MP3), 'exito', 'error', 'tiempo_ms'
    """
    resultado = {
        "audio_bytes": None,
        "exito": False,
        "error": None,
        "tiempo_ms": 0,
    }

    inicio = time.time()

    try:
        # Limpiar el texto un poco para mejor pronunciación
        texto_limpio = _limpiar_texto_para_tts(texto)

        tts = gTTS(text=texto_limpio, lang=idioma, slow=False, tld="com.ar")

        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)

        resultado["audio_bytes"] = buffer.read()
        resultado["exito"] = True

    except Exception as e:
        resultado["error"] = f"No se pudo generar el audio: {e}"
    finally:
        resultado["tiempo_ms"] = int((time.time() - inicio) * 1000)

    return resultado


def _limpiar_texto_para_tts(texto: str) -> str:
    """Preprocesa el texto para mejor pronunciación."""
    # Reemplazos básicos para mejor pronunciación en español
    reemplazos = {
        "WER": "W E R",
        "TTS": "T T S",
        "ASR": "A S R",
        "NLP": "N L P",
        "NER": "N E R",
        "mg": "miligramos",
        "ml": "mililitros",
    }
    for clave, valor in reemplazos.items():
        texto = texto.replace(clave, valor)
    return texto


def texto_a_bytes(texto: str) -> bytes | None:
    """
    Wrapper simple: devuelve bytes de audio o None si falla.
    Útil para llamadas rápidas desde la interfaz.
    """
    resultado = sintetizar_voz(texto)
    return resultado["audio_bytes"] if resultado["exito"] else None


if __name__ == "__main__":
    res = sintetizar_voz("Hola, soy Piccolo. ¿En qué puedo ayudarte hoy?")
    if res["exito"]:
        with open("/tmp/test_tts.mp3", "wb") as f:
            f.write(res["audio_bytes"])
        print(f"Audio generado en {res['tiempo_ms']}ms")
    else:
        print(f"Error: {res['error']}")
