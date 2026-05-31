"""
modules/nlp.py — Procesamiento del Lenguaje Natural (Bloque 1)
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Implementa:
- Tokenización con spaCy (modelo es_core_news_sm)
- NER: extracción de MEDICAMENTO, DOSIS, FRECUENCIA (3 entidades del dominio)
- POS tagging: filtrado por categorías gramaticales
- Detección de intención: 6 intenciones del dominio Piccolo
- Fallback sin spaCy: tokenización básica con regex
"""

import re
import json
import time
from typing import Optional

# Intentar cargar spaCy (puede no estar instalado en entorno sin internet)
try:
    import spacy
    _nlp = spacy.load("es_core_news_sm")
    SPACY_DISPONIBLE = True
except Exception:
    SPACY_DISPONIBLE = False
    _nlp = None


# =========================
# DICCIONARIOS DEL DOMINIO
# =========================

MEDICAMENTOS_CONOCIDOS = [
    "enalapril", "metformina", "atorvastatina", "omeprazol", "losartan",
    "losartán", "levotiroxina", "amlodipina", "aspirina", "furosemida",
    "clonazepam", "ibuprofeno", "paracetamol", "amoxicilina", "metoprolol",
]

# Patrones de dosis: "10 mg", "500 miligramos", "2 comprimidos"
PATRON_DOSIS = re.compile(
    r'\b(\d+[\.,]?\d*)\s*(mg|gr|ml|miligramos|microgramos|comprimidos?|pastillas?|gotas?|ampolla)\b',
    re.IGNORECASE
)

# Patrones de frecuencia: "cada 8 horas", "dos veces por día", "a la mañana"
PATRON_FRECUENCIA = re.compile(
    r'\b(cada\s+\d+\s+horas?|una\s+vez\s+(?:al?\s+)?d[íi]a|dos\s+veces|tres\s+veces|'
    r'a\s+la\s+ma[ñn]ana|a\s+la\s+noche|en\s+ayunas?|con\s+comida|antes\s+de\s+comer|'
    r'después\s+de\s+comer|diariamente|todos\s+los\s+d[íi]as)\b',
    re.IGNORECASE
)

# Mapeo intención → palabras clave
INTENCIONES = {
    "consultar_para_que_sirve": [
        "sirve", "para qué", "para que", "qué es", "que es",
        "qué trata", "que trata", "qué cura", "que cura", "indicación"
    ],
    "consultar_cuidados": [
        "cuidado", "precaución", "precaucion", "advertencia",
        "contraindicación", "contraindicacion", "peligro", "no puedo",
        "no debo", "evitar", "tener en cuenta"
    ],
    "consultar_consejo": [
        "consejo", "recomendación", "recomendacion", "tip",
        "mejor momento", "cuándo tomarlo", "cuando tomarlo", "cómo tomarlo", "como tomarlo"
    ],
    "consultar_tipo": [
        "tipo", "clase", "categoría", "categoria", "familia",
        "qué tipo", "que tipo"
    ],
    "consultar_que_hace": [
        "hace", "funciona", "mecanismo", "cómo actúa", "como actua",
        "qué efecto", "que efecto", "cómo funciona", "como funciona"
    ],
    "consultar_para_quien": [
        "para quién", "para quien", "quién lo toma", "quien lo toma",
        "qué enfermedad", "que enfermedad", "quién necesita", "quien necesita"
    ],
    "agregar_alarma": [
        "alarma", "recordatorio", "recordarme", "avisar", "avisame",
        "tomar a las", "recordar a las"
    ],
    "saludo": [
        "hola", "buenas", "buenos días", "buen día", "buenas tardes",
        "buenas noches", "hey", "hi"
    ],
}

# Columna de BD correspondiente a cada intención de consulta
INTENCION_A_COLUMNA = {
    "consultar_para_que_sirve": "para_que_sirve",
    "consultar_cuidados": "tener_cuidado",
    "consultar_consejo": "consejo_amigable",
    "consultar_tipo": "tipo",
    "consultar_que_hace": "que_hace",
    "consultar_para_quien": "para_quien",
}


# =========================
# TOKENIZACIÓN
# =========================

def tokenizar(texto: str) -> list[str]:
    """
    Tokeniza el texto. Usa spaCy si está disponible, regex como fallback.
    Devuelve lista de tokens en minúsculas, sin puntuación ni stopwords irrelevantes.
    """
    if SPACY_DISPONIBLE and _nlp:
        doc = _nlp(texto.lower())
        return [
            token.lemma_ for token in doc
            if not token.is_punct and not token.is_space
        ]
    else:
        # Fallback: regex simple
        tokens = re.findall(r'\b[a-záéíóúüñ]+\b', texto.lower())
        return tokens


def pos_tagging(texto: str) -> list[dict]:
    """
    Realiza POS tagging. Con spaCy devuelve etiquetas completas;
    sin spaCy hace una aproximación simple.
    
    Returns:
        Lista de dicts con 'token', 'pos', 'lemma'
    """
    if SPACY_DISPONIBLE and _nlp:
        doc = _nlp(texto)
        return [
            {"token": t.text, "pos": t.pos_, "lemma": t.lemma_}
            for t in doc if not t.is_space
        ]
    else:
        # Fallback simple: marca sustantivos conocidos
        tokens = texto.lower().split()
        resultado = []
        for t in tokens:
            if t in MEDICAMENTOS_CONOCIDOS:
                pos = "NOUN"
            elif re.match(r'\d+', t):
                pos = "NUM"
            elif t in ["para", "de", "con", "en", "el", "la", "los", "las", "un", "una"]:
                pos = "ADP"
            else:
                pos = "UNKN"
            resultado.append({"token": t, "pos": pos, "lemma": t})
        return resultado


# =========================
# NER: NAMED ENTITY RECOGNITION DEL DOMINIO
# =========================

def extraer_entidades(texto: str) -> dict:
    """
    Extrae entidades del dominio medicamentos:
    - MEDICAMENTO: nombre del medicamento detectado
    - DOSIS: cantidad y unidad (ej: "10 mg")
    - FRECUENCIA: cuándo tomarlo (ej: "cada 8 horas")
    
    Returns:
        dict con listas por tipo de entidad y JSON serializable
    """
    texto_lower = texto.lower()
    entidades = {
        "MEDICAMENTO": [],
        "DOSIS": [],
        "FRECUENCIA": [],
    }

    # --- MEDICAMENTO ---
    for med in MEDICAMENTOS_CONOCIDOS:
        if med in texto_lower:
            entidades["MEDICAMENTO"].append(med)

    # Con spaCy: también buscar entidades reconocidas como ORG/MISC que podrían ser marcas
    if SPACY_DISPONIBLE and _nlp:
        doc = _nlp(texto)
        for ent in doc.ents:
            nombre = ent.text.lower()
            if nombre not in entidades["MEDICAMENTO"] and nombre in MEDICAMENTOS_CONOCIDOS:
                entidades["MEDICAMENTO"].append(nombre)

    # --- DOSIS ---
    for match in PATRON_DOSIS.finditer(texto):
        entidades["DOSIS"].append(match.group(0))

    # --- FRECUENCIA ---
    for match in PATRON_FRECUENCIA.finditer(texto):
        entidades["FRECUENCIA"].append(match.group(0))

    # Deduplicar
    for k in entidades:
        entidades[k] = list(dict.fromkeys(entidades[k]))

    return entidades


def entidades_a_json(entidades: dict) -> str:
    """Serializa el diccionario de entidades a JSON string para guardar en BD."""
    return json.dumps(entidades, ensure_ascii=False)


# =========================
# DETECCIÓN DE INTENCIÓN
# =========================

def detectar_intencion(texto: str) -> str:
    """
    Detecta la intención del usuario en base a palabras clave.
    
    Returns:
        Nombre de la intención (str) o 'desconocida'
    """
    texto_lower = texto.lower()
    mejores = []

    for intencion, palabras in INTENCIONES.items():
        score = sum(1 for p in palabras if p in texto_lower)
        if score > 0:
            mejores.append((score, intencion))

    if not mejores:
        return "desconocida"

    mejores.sort(key=lambda x: -x[0])
    return mejores[0][1]


def columna_para_intencion(intencion: str) -> str | None:
    """Devuelve el nombre de columna en saberes_piccolo para una intención dada."""
    return INTENCION_A_COLUMNA.get(intencion)


# =========================
# PIPELINE COMPLETO NLP
# =========================

def procesar_texto(texto: str) -> dict:
    """
    Pipeline completo: tokeniza, hace POS, extrae entidades y detecta intención.
    
    Returns:
        dict con todos los resultados del procesamiento NLP
    """
    inicio = time.time()
    tokens = tokenizar(texto)
    pos = pos_tagging(texto)
    entidades = extraer_entidades(texto)
    intencion = detectar_intencion(texto)
    columna = columna_para_intencion(intencion)
    tiempo = int((time.time() - inicio) * 1000)

    return {
        "texto_original": texto,
        "tokens": tokens,
        "pos_tags": pos,
        "entidades": entidades,
        "entidades_json": entidades_a_json(entidades),
        "intencion": intencion,
        "columna_bd": columna,
        "medicamento_detectado": entidades["MEDICAMENTO"][0] if entidades["MEDICAMENTO"] else None,
        "tiempo_ms": tiempo,
        "spacy_usado": SPACY_DISPONIBLE,
    }


if __name__ == "__main__":
    ejemplos = [
        "para qué sirve el enalapril",
        "qué cuidados tengo que tener con el omeprazol de 20 mg",
        "dame un consejo para tomar la levotiroxina en ayunas cada día",
    ]
    for ej in ejemplos:
        res = procesar_texto(ej)
        print(f"\nTexto: {ej}")
        print(f"  Intención : {res['intencion']}")
        print(f"  Entidades : {res['entidades']}")
        print(f"  Medicamento: {res['medicamento_detectado']}")
        print(f"  Columna BD: {res['columna_bd']}")
        print(f"  Tiempo    : {res['tiempo_ms']}ms")
