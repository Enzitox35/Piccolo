"""
modules/search.py — Motor de Recuperación de Información (Bloque 3)
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Implementa:
- Índice invertido sobre el corpus de medicamentos
- Pesos TF-IDF para cada término
- Búsqueda por similitud del coseno
- Evaluación con Precisión, Recall y F1 (10 consultas de prueba)
- Persistencia del índice en JSON
- Snippets relevantes en los resultados
"""

import re
import math
import json
from pathlib import Path
from collections import defaultdict

INDEX_PATH = Path(__file__).parent.parent / "data" / "indice_invertido.json"

# =========================
# DOCUMENTOS DEL CORPUS PICCOLO
# Cada documento = un medicamento con su descripción completa
# =========================
CORPUS_DOCUMENTOS = [
    {
        "id": "enalapril",
        "titulo": "Enalapril",
        "texto": (
            "El enalapril sirve para bajar la presión de la sangre. "
            "Es un antihipertensivo que relaja los vasos sanguíneos para que el corazón trabaje con más calma. "
            "Mejor no tomarlo si estás embarazada. "
            "Está indicado para presión alta. "
            "Tomalo siempre a la misma hora del día, como un ritual."
        ),
    },
    {
        "id": "metformina",
        "titulo": "Metformina",
        "texto": (
            "La metformina ayuda a controlar el azúcar en la sangre. "
            "Es un antidiabético que le dice al cuerpo cómo usar mejor el azúcar. "
            "Avisale al médico si tenés problemas de riñón. "
            "Está indicada para diabetes tipo dos. "
            "Tomala con la comida, así el estómago lo agradece."
        ),
    },
    {
        "id": "atorvastatina",
        "titulo": "Atorvastatina",
        "texto": (
            "La atorvastatina baja el colesterol malo. "
            "Es un hipolipemiante que limpia las grasas que se acumulan en la sangre. "
            "No tomar con jugo de pomelo. "
            "Está indicada para colesterol alto. "
            "La noche es el mejor momento para tomarla."
        ),
    },
    {
        "id": "omeprazol",
        "titulo": "Omeprazol",
        "texto": (
            "El omeprazol protege el estómago y calma la acidez. "
            "Es un gastroprotector que reduce el ácido que produce el estómago. "
            "Si lo tomás mucho tiempo hablá con tu médico. "
            "Está indicado para acidez gastritis reflujo. "
            "Tomalo media hora antes del desayuno con un vasito de agua."
        ),
    },
    {
        "id": "losartan",
        "titulo": "Losartán",
        "texto": (
            "El losartán baja la presión y cuida los riñones. "
            "Es un antihipertensivo que relaja los vasos sanguíneos. "
            "No tomarlo durante el embarazo. "
            "Está indicado para presión alta. "
            "Tomá agua seguido y controlate la presión de vez en cuando."
        ),
    },
    {
        "id": "levotiroxina",
        "titulo": "Levotiroxina",
        "texto": (
            "La levotiroxina reemplaza la hormona que la tiroides no produce. "
            "Es una hormona tiroidea que ayuda al metabolismo a funcionar bien. "
            "No mezclar con calcio ni hierro. "
            "Está indicada para tiroides baja hipotiroidismo. "
            "Tomala en ayunas al menos treinta minutos antes de desayunar."
        ),
    },
    {
        "id": "amlodipina",
        "titulo": "Amlodipina",
        "texto": (
            "La amlodipina baja la presión y alivia la angina de pecho. "
            "Es un antihipertensivo que abre los vasos sanguíneos para que la sangre fluya mejor. "
            "A veces hincha un poco los tobillos. "
            "Está indicada para presión alta y angina. "
            "Se puede tomar con o sin comida lo importante es la misma hora siempre."
        ),
    },
    {
        "id": "aspirina",
        "titulo": "Aspirina 100mg",
        "texto": (
            "La aspirina evita que se formen coágulos en la sangre. "
            "Es un antiagregante que hace que la sangre fluya sin pegarse. "
            "No tomar si tenés úlcera o tomás anticoagulantes. "
            "Está indicada para cuidado del corazón. "
            "Tomala con comida para proteger el estómago."
        ),
    },
    {
        "id": "furosemida",
        "titulo": "Furosemida",
        "texto": (
            "La furosemida elimina el líquido que se acumula en el cuerpo. "
            "Es un diurético que le ayuda al riñón a sacar el agua de más. "
            "Puede bajar el potasio comer banana ayuda. "
            "Está indicada para retención de líquido y corazón. "
            "Tomala a la mañana para no levantarte de noche."
        ),
    },
    {
        "id": "clonazepam",
        "titulo": "Clonazepam",
        "texto": (
            "El clonazepam calma la ansiedad y ayuda con las convulsiones. "
            "Es un ansiolítico que tranquiliza el sistema nervioso. "
            "No dejarlo de golpe hay que ir bajando de a poco. "
            "Está indicado para ansiedad y epilepsia. "
            "No manejes después de tomarlo. Avisale a alguien de confianza que lo tomás."
        ),
    },
]

# =========================
# CONSULTAS DE PRUEBA PARA EVALUACIÓN P/R/F1
# formato: (consulta, [doc_ids relevantes])
# =========================
CONSULTAS_EVALUACION = [
    ("presión alta medicamento", ["enalapril", "losartan", "amlodipina"]),
    ("colesterol", ["atorvastatina"]),
    ("diabetes azúcar", ["metformina"]),
    ("estómago acidez reflujo", ["omeprazol"]),
    ("tiroides hormona", ["levotiroxina"]),
    ("corazón angina", ["aspirina", "amlodipina", "furosemida"]),
    ("riñón líquido", ["furosemida", "losartan"]),
    ("ansiedad nervioso", ["clonazepam"]),
    ("embarazo contraindicado", ["enalapril", "losartan"]),
    ("tomar en ayunas mañana", ["omeprazol", "levotiroxina"]),
]


# =========================
# STOPWORDS ESPAÑOL (básico)
# =========================
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "del", "las", "un", "una",
    "con", "para", "por", "es", "se", "que", "al", "su", "lo", "le",
    "no", "más", "o", "si", "sus", "ya", "hay", "me", "mi", "te",
    "como", "qué", "que", "cuando", "cuándo", "cómo", "cual",
}


def _tokenizar(texto: str) -> list[str]:
    texto = texto.lower().strip()
    tokens = re.findall(r'\b[a-záéíóúüñ]{2,}\b', texto)
    return [t for t in tokens if t not in STOPWORDS]


# =========================
# ÍNDICE INVERTIDO
# =========================

class MotorBusqueda:
    """
    Motor de búsqueda TF-IDF con índice invertido.
    
    Attributes:
        documentos: Lista de docs con id, titulo, texto
        indice: {término → {doc_id → tf}}
        idf: {término → idf}
        tfidf: {doc_id → {término → tfidf}}
    """

    def __init__(self):
        self.documentos = []
        self.indice = defaultdict(dict)   # término → {doc_id: tf}
        self.idf = {}                      # término → idf
        self.tfidf = defaultdict(dict)    # doc_id → {término: tfidf}
        self.construido = False

    def construir_indice(self, documentos: list[dict] = None):
        """Construye el índice invertido y calcula TF-IDF."""
        if documentos is None:
            documentos = CORPUS_DOCUMENTOS
        self.documentos = documentos
        N = len(documentos)

        self.indice.clear()
        self.idf.clear()
        self.tfidf.clear()

        # TF por documento
        tf_raw = {}
        for doc in documentos:
            tokens = _tokenizar(doc["texto"])
            n_tokens = len(tokens)
            conteo = defaultdict(int)
            for t in tokens:
                conteo[t] += 1
            tf_raw[doc["id"]] = {t: c / n_tokens for t, c in conteo.items()}
            for t in conteo:
                if doc["id"] not in self.indice[t]:
                    self.indice[t][doc["id"]] = tf_raw[doc["id"]][t]

        # IDF
        for termino, docs_con_termino in self.indice.items():
            df = len(docs_con_termino)
            self.idf[termino] = math.log((N + 1) / (df + 1)) + 1  # suavizado

        # TF-IDF
        for doc in documentos:
            for termino, tf in tf_raw[doc["id"]].items():
                self.tfidf[doc["id"]][termino] = tf * self.idf.get(termino, 0)

        self.construido = True

    def _vector_consulta(self, consulta: str) -> dict[str, float]:
        """Convierte la consulta a vector TF-IDF."""
        tokens = _tokenizar(consulta)
        n = len(tokens)
        if n == 0:
            return {}
        conteo = defaultdict(int)
        for t in tokens:
            conteo[t] += 1
        return {t: (c / n) * self.idf.get(t, 0) for t, c in conteo.items()}

    def _similitud_coseno(self, vec_a: dict, vec_b: dict) -> float:
        """Calcula la similitud coseno entre dos vectores (dicts)."""
        terminos = set(vec_a) & set(vec_b)
        if not terminos:
            return 0.0
        dot = sum(vec_a[t] * vec_b[t] for t in terminos)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return round(dot / (norm_a * norm_b), 4)

    def buscar(self, consulta: str, top_n: int = 5) -> list[dict]:
        """
        Busca documentos relevantes para la consulta.
        
        Returns:
            Lista de resultados ordenados por similitud, con snippet.
        """
        if not self.construido:
            self.construir_indice()

        vec_q = self._vector_consulta(consulta)
        if not vec_q:
            return []

        resultados = []
        for doc in self.documentos:
            vec_d = self.tfidf.get(doc["id"], {})
            sim = self._similitud_coseno(vec_q, vec_d)
            if sim > 0:
                snippet = _generar_snippet(doc["texto"], consulta)
                resultados.append({
                    "id": doc["id"],
                    "titulo": doc["titulo"],
                    "similitud": sim,
                    "snippet": snippet,
                    "texto_completo": doc["texto"],
                })

        resultados.sort(key=lambda x: -x["similitud"])
        return resultados[:top_n]

    def guardar_indice(self, path: Path = INDEX_PATH):
        """Persiste el índice en JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        datos = {
            "documentos": self.documentos,
            "indice": {t: dict(d) for t, d in self.indice.items()},
            "idf": self.idf,
            "tfidf": {k: dict(v) for k, v in self.tfidf.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    def cargar_indice(self, path: Path = INDEX_PATH) -> bool:
        """Carga el índice desde JSON."""
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                datos = json.load(f)
            self.documentos = datos["documentos"]
            self.indice = defaultdict(dict, {t: d for t, d in datos["indice"].items()})
            self.idf = datos["idf"]
            self.tfidf = defaultdict(dict, datos["tfidf"])
            self.construido = True
            return True
        except Exception:
            return False


def _generar_snippet(texto: str, consulta: str, max_chars: int = 200) -> str:
    """
    Genera un snippet del texto que incluya términos de la consulta.
    """
    tokens_q = set(_tokenizar(consulta))
    oraciones = re.split(r'[.!?]', texto)
    mejor_oracion = ""
    mejor_score = -1

    for oracion in oraciones:
        oracion = oracion.strip()
        if not oracion:
            continue
        tokens_o = set(_tokenizar(oracion))
        score = len(tokens_q & tokens_o)
        if score > mejor_score:
            mejor_score = score
            mejor_oracion = oracion

    if not mejor_oracion:
        return texto[:max_chars] + "..."

    return mejor_oracion[:max_chars]


# =========================
# EVALUACIÓN P / R / F1
# =========================

def evaluar_motor(motor: MotorBusqueda, top_n: int = 3) -> dict:
    """
    Evalúa el motor con las consultas de prueba definidas.
    
    Returns:
        dict con resultados por consulta y promedios globales
    """
    resultados_detalle = []
    precision_lista = []
    recall_lista = []
    f1_lista = []

    for consulta, relevantes_reales in CONSULTAS_EVALUACION:
        resultados = motor.buscar(consulta, top_n=top_n)
        recuperados = [r["id"] for r in resultados]

        relevantes_set = set(relevantes_reales)
        recuperados_set = set(recuperados)

        tp = len(relevantes_set & recuperados_set)
        precision = tp / len(recuperados_set) if recuperados_set else 0.0
        recall = tp / len(relevantes_set) if relevantes_set else 0.0
        f1 = (2 * precision * recall / (precision + recall)
               if (precision + recall) > 0 else 0.0)

        precision_lista.append(precision)
        recall_lista.append(recall)
        f1_lista.append(f1)

        resultados_detalle.append({
            "consulta": consulta,
            "relevantes_esperados": relevantes_reales,
            "recuperados": recuperados,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        })

    return {
        "detalle": resultados_detalle,
        "precision_promedio": round(sum(precision_lista) / len(precision_lista), 4),
        "recall_promedio": round(sum(recall_lista) / len(recall_lista), 4),
        "f1_promedio": round(sum(f1_lista) / len(f1_lista), 4),
    }


# =========================
# INSTANCIA GLOBAL
# =========================
_motor: MotorBusqueda | None = None


def get_motor() -> MotorBusqueda:
    """Devuelve el motor de búsqueda (singleton), construyendo si es necesario."""
    global _motor
    if _motor is not None and _motor.construido:
        return _motor
    _motor = MotorBusqueda()
    if not _motor.cargar_indice():
        _motor.construir_indice()
        _motor.guardar_indice()
    return _motor


def buscar(consulta: str, top_n: int = 5) -> list[dict]:
    """API simplificada: busca y devuelve resultados."""
    return get_motor().buscar(consulta, top_n=top_n)


if __name__ == "__main__":
    motor = MotorBusqueda()
    motor.construir_indice()
    motor.guardar_indice()
    print(f"Índice construido: {len(motor.indice)} términos únicos\n")

    consultas_test = [
        "presión alta",
        "azúcar diabetes",
        "estómago acidez",
        "colesterol",
    ]
    for q in consultas_test:
        resultados = motor.buscar(q, top_n=3)
        print(f"Consulta: '{q}'")
        for r in resultados:
            print(f"  [{r['similitud']:.3f}] {r['titulo']}: {r['snippet'][:80]}...")
        print()

    print("Evaluación P/R/F1:")
    eval_res = evaluar_motor(motor)
    print(f"  Precisión promedio: {eval_res['precision_promedio']}")
    print(f"  Recall promedio   : {eval_res['recall_promedio']}")
    print(f"  F1 promedio       : {eval_res['f1_promedio']}")
    for d in eval_res["detalle"]:
        print(f"  '{d['consulta']}' → P={d['precision']} R={d['recall']} F1={d['f1']}")
