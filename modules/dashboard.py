"""
modules/dashboard.py — Visualizaciones del Dashboard
Sistema Piccolo

Genera todos los gráficos del dashboard con datos reales de la BD:
1. Métricas globales (tarjetas)
2. Top 10 consultas más frecuentes
3. Distribución de tipos de consulta (torta)
4. Evolución temporal (líneas)
5. Métricas P/R/F1 del motor de búsqueda
6. Nube de palabras de términos más buscados
7. Últimas consultas con detalle
"""

import io
import re
from collections import Counter
from pathlib import Path


def generar_nube_palabras(textos: list[str]) -> bytes | None:
    """
    Genera una nube de palabras a partir de una lista de textos.
    Devuelve los bytes de la imagen PNG o None si falla.
    """
    try:
        from wordcloud import WordCloud
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Stopwords en español
        STOPWORDS_ES = {
            "de", "la", "el", "en", "y", "a", "los", "del", "las", "un", "una",
            "con", "para", "por", "es", "se", "que", "al", "su", "lo", "le",
            "no", "más", "o", "si", "sus", "ya", "hay", "me", "mi", "te",
            "como", "qué", "que", "cuando", "cuándo", "cómo", "cual", "tengo",
            "que", "sirve", "hace", "tomar", "tomo", "puedo", "debo",
        }

        texto_completo = " ".join(textos).lower()
        tokens = re.findall(r'\b[a-záéíóúüñ]{3,}\b', texto_completo)
        tokens_filtrados = [t for t in tokens if t not in STOPWORDS_ES]

        if not tokens_filtrados:
            return None

        texto_limpio = " ".join(tokens_filtrados)

        wc = WordCloud(
            width=800,
            height=400,
            background_color="#0a0a0a",
            colormap="Greens",
            max_words=60,
            prefer_horizontal=0.8,
            min_font_size=12,
        ).generate(texto_limpio)

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0a0a0a")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout(pad=0)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight",
                    facecolor="#0a0a0a", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        print(f"Error generando nube: {e}")
        return None


def top_consultas(historial: list[dict], top_n: int = 10) -> list[dict]:
    """
    Extrae las top_n consultas más frecuentes del historial.
    Agrupa por texto normalizado (minúsculas, sin espacios extra).
    """
    conteo = Counter()
    for h in historial:
        texto = (h.get("lo_que_dijo") or "").strip().lower()
        if texto:
            conteo[texto] += 1

    return [
        {"consulta": consulta, "veces": veces}
        for consulta, veces in conteo.most_common(top_n)
    ]


def calcular_accuracy_ner(ejemplos: list[dict]) -> dict:
    """
    Calcula la accuracy del NER sobre ejemplos anotados manualmente.

    Cada ejemplo es un dict:
        {
            "texto": "para qué sirve el enalapril",
            "entidades_esperadas": {"MEDICAMENTO": ["enalapril"]}
        }

    Returns:
        dict con accuracy global y por tipo de entidad
    """
    from modules.nlp import extraer_entidades

    total = 0
    correctos = 0
    por_tipo = {}

    for ej in ejemplos:
        texto = ej["texto"]
        esperadas = ej["entidades_esperadas"]
        obtenidas = extraer_entidades(texto)

        for tipo, valores_esperados in esperadas.items():
            if tipo not in por_tipo:
                por_tipo[tipo] = {"total": 0, "correctos": 0}

            for val in valores_esperados:
                total += 1
                por_tipo[tipo]["total"] += 1
                # Verificar si el valor esperado está en las obtenidas
                obtenidas_tipo = [v.lower() for v in obtenidas.get(tipo, [])]
                if val.lower() in obtenidas_tipo:
                    correctos += 1
                    por_tipo[tipo]["correctos"] += 1

    accuracy_global = round(correctos / total, 4) if total > 0 else 0.0
    accuracy_por_tipo = {
        tipo: round(v["correctos"] / v["total"], 4) if v["total"] > 0 else 0.0
        for tipo, v in por_tipo.items()
    }

    return {
        "accuracy_global": accuracy_global,
        "correctos": correctos,
        "total": total,
        "accuracy_por_tipo": accuracy_por_tipo,
    }


# =========================
# 20 EJEMPLOS ANOTADOS PARA EVAL NER
# (mínimo obligatorio según rúbrica)
# =========================
EJEMPLOS_NER = [
    {"texto": "para qué sirve el enalapril",
     "entidades_esperadas": {"MEDICAMENTO": ["enalapril"]}},
    {"texto": "qué cuidados tengo con el omeprazol de 20 mg",
     "entidades_esperadas": {"MEDICAMENTO": ["omeprazol"], "DOSIS": ["20 mg"]}},
    {"texto": "cuándo tomo la metformina",
     "entidades_esperadas": {"MEDICAMENTO": ["metformina"]}},
    {"texto": "la levotiroxina se toma en ayunas cada día",
     "entidades_esperadas": {"MEDICAMENTO": ["levotiroxina"], "FRECUENCIA": ["cada día"]}},
    {"texto": "qué hace el losartán en el cuerpo",
     "entidades_esperadas": {"MEDICAMENTO": ["losartán"]}},
    {"texto": "para qué es la atorvastatina",
     "entidades_esperadas": {"MEDICAMENTO": ["atorvastatina"]}},
    {"texto": "tengo que tomar la aspirina 100 mg con comida",
     "entidades_esperadas": {"MEDICAMENTO": ["aspirina"], "DOSIS": ["100 mg"]}},
    {"texto": "qué tipo de medicamento es el clonazepam",
     "entidades_esperadas": {"MEDICAMENTO": ["clonazepam"]}},
    {"texto": "para quién es la furosemida",
     "entidades_esperadas": {"MEDICAMENTO": ["furosemida"]}},
    {"texto": "qué cuidados tiene la amlodipina",
     "entidades_esperadas": {"MEDICAMENTO": ["amlodipina"]}},
    {"texto": "tomo el enalapril dos veces por día",
     "entidades_esperadas": {"MEDICAMENTO": ["enalapril"], "FRECUENCIA": ["dos veces"]}},
    {"texto": "la metformina 500 mg con la comida",
     "entidades_esperadas": {"MEDICAMENTO": ["metformina"], "DOSIS": ["500 mg"]}},
    {"texto": "cuándo tomo la levotiroxina antes de desayunar",
     "entidades_esperadas": {"MEDICAMENTO": ["levotiroxina"], "FRECUENCIA": ["antes de comer"]}},
    {"texto": "el omeprazol sirve para la acidez del estómago",
     "entidades_esperadas": {"MEDICAMENTO": ["omeprazol"]}},
    {"texto": "puedo tomar la aspirina todos los días",
     "entidades_esperadas": {"MEDICAMENTO": ["aspirina"], "FRECUENCIA": ["todos los días"]}},
    {"texto": "consejo para tomar el clonazepam",
     "entidades_esperadas": {"MEDICAMENTO": ["clonazepam"]}},
    {"texto": "la furosemida 40 mg a la mañana",
     "entidades_esperadas": {"MEDICAMENTO": ["furosemida"], "DOSIS": ["40 mg"], "FRECUENCIA": ["a la mañana"]}},
    {"texto": "para qué sirve la amlodipina",
     "entidades_esperadas": {"MEDICAMENTO": ["amlodipina"]}},
    {"texto": "el losartán relaja los vasos sanguíneos",
     "entidades_esperadas": {"MEDICAMENTO": ["losartán"]}},
    {"texto": "tomo atorvastatina una vez por día a la noche",
     "entidades_esperadas": {"MEDICAMENTO": ["atorvastatina"], "FRECUENCIA": ["una vez por día"]}},
]
