"""
modules/ngrams.py — Modelo de Lenguaje con N-gramas (Bloque 2)
Sistema Piccolo — Asistente de medicamentos por voz para adultos mayores

Implementa:
- Entrenamiento de modelos de bigramas y trigramas
- Suavizado Add-k (k configurable)
- Cálculo de perplejidad
- Top-10 bigramas por contexto
- Corpus del dominio medicamentos (generado internamente)
"""

import math
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

# Archivo de persistencia del modelo
MODEL_PATH = Path(__file__).parent.parent / "data" / "ngram_model.json"

# =========================
# CORPUS DEL DOMINIO PICCOLO
# (frases en lenguaje coloquial de adultos mayores sobre medicamentos)
# =========================
CORPUS_PICCOLO = [
    "para qué sirve el enalapril",
    "el enalapril sirve para bajar la presión",
    "tengo que tomar el enalapril todos los días",
    "el enalapril relaja los vasos sanguíneos",
    "qué cuidados tengo que tener con el enalapril",
    "el enalapril no se toma en el embarazo",
    "para qué sirve la metformina",
    "la metformina ayuda a controlar el azúcar en la sangre",
    "tengo que tomar la metformina con la comida",
    "la metformina es para la diabetes tipo dos",
    "qué pasa si no tomo la metformina",
    "la metformina puede afectar los riñones",
    "para qué sirve el omeprazol",
    "el omeprazol protege el estómago de la acidez",
    "tengo que tomar el omeprazol media hora antes del desayuno",
    "el omeprazol reduce el ácido del estómago",
    "para qué sirve el losartán",
    "el losartán baja la presión y cuida los riñones",
    "el losartán relaja los vasos sanguíneos",
    "hay que tomar agua seguido cuando se toma losartán",
    "para qué sirve la levotiroxina",
    "la levotiroxina es para la tiroides",
    "la levotiroxina se toma en ayunas media hora antes de desayunar",
    "no mezclar la levotiroxina con calcio ni hierro",
    "para qué sirve la atorvastatina",
    "la atorvastatina baja el colesterol malo",
    "la atorvastatina se toma de noche",
    "no tomar la atorvastatina con jugo de pomelo",
    "para qué sirve la amlodipina",
    "la amlodipina baja la presión y alivia la angina",
    "la amlodipina puede hinchar los tobillos",
    "para qué sirve la aspirina de cien miligramos",
    "la aspirina evita que se formen coágulos en la sangre",
    "hay que tomar la aspirina con comida para proteger el estómago",
    "para qué sirve la furosemida",
    "la furosemida elimina el líquido que se acumula en el cuerpo",
    "la furosemida se toma a la mañana para no levantarse de noche",
    "la furosemida puede bajar el potasio",
    "para qué sirve el clonazepam",
    "el clonazepam calma la ansiedad",
    "el clonazepam no se deja de golpe hay que bajar de a poco",
    "no manejar después de tomar el clonazepam",
    "cuándo tengo que tomar el medicamento",
    "me olvidé de tomar la pastilla",
    "puedo tomar dos pastillas juntas",
    "tengo que tomar la medicina con o sin comida",
    "qué efecto tiene este medicamento",
    "qué hace la medicina en el cuerpo",
    "cuál es la dosis correcta del medicamento",
    "puedo tomar alcohol con el medicamento",
    "el medicamento tiene efectos secundarios",
    "buen día Piccolo en qué me podés ayudar",
    "necesito información sobre mi medicamento",
    "me olvidé si tomé la medicina esta mañana",
    "a qué hora tengo que tomar el medicamento",
    "quiero saber para qué sirve mi remedio",
    "dame un consejo para tomar mejor mi medicamento",
    "cuáles son los cuidados que tengo que tener",
    "qué tipo de medicamento es este",
    "para quién está indicado este medicamento",
    "tengo presión alta qué medicamento necesito",
    "tengo diabetes cuál es el remedio",
    "me duele el estómago puedo tomar omeprazol",
    "tengo colesterol alto qué medicamento tomo",
    "cuáles son los efectos secundarios de la medicina",
    "puedo dejar de tomar el medicamento",
    "cuánto tiempo tengo que tomar el medicamento",
    "el médico me recetó este medicamento para qué sirve",
    "piccolo recordame tomar el medicamento a las ocho",
    "poneme una alarma para la medicina de la mañana",
    "avisame cuando sea hora de tomar la pastilla",
    "quiero un recordatorio para el medicamento del mediodía",
]


# =========================
# PREPROCESAMIENTO
# =========================
def _tokenizar_simple(texto: str) -> list[str]:
    """Tokenización básica: minúsculas + split por palabras."""
    texto = texto.lower().strip()
    tokens = re.findall(r'\b[a-záéíóúüñ0-9]+\b', texto)
    return ["<s>"] + tokens + ["</s>"]


def preparar_corpus(frases: list[str]) -> list[list[str]]:
    """Convierte una lista de frases a lista de listas de tokens."""
    return [_tokenizar_simple(frase) for frase in frases]


# =========================
# CLASE MODELO N-GRAMAS
# =========================
class ModeloNGramas:
    """
    Modelo de bigramas y trigramas con suavizado Add-k.
    
    Attributes:
        n: Orden del modelo (2=bigramas, 3=trigramas)
        k: Parámetro de suavizado Add-k
        conteos_ngrama: Conteo de cada n-grama
        conteos_contexto: Conteo de cada (n-1)-grama como contexto
        vocabulario: Conjunto de tokens vistos en entrenamiento
    """

    def __init__(self, n: int = 2, k: float = 1.0):
        self.n = n
        self.k = k
        self.conteos_ngrama = defaultdict(int)
        self.conteos_contexto = defaultdict(int)
        self.vocabulario = set()
        self.entrenado = False

    def entrenar(self, corpus: list[list[str]]):
        """Entrena el modelo sobre el corpus (lista de frases tokenizadas)."""
        self.conteos_ngrama.clear()
        self.conteos_contexto.clear()
        self.vocabulario.clear()

        for frase in corpus:
            for token in frase:
                self.vocabulario.add(token)
            for i in range(len(frase) - self.n + 1):
                ngrama = tuple(frase[i:i + self.n])
                contexto = ngrama[:-1]
                self.conteos_ngrama[ngrama] += 1
                self.conteos_contexto[contexto] += 1

        self.entrenado = True

    def probabilidad(self, ngrama: tuple) -> float:
        """
        Calcula P(wn | w1...wn-1) con suavizado Add-k.
        P = (C(ngrama) + k) / (C(contexto) + k * V)
        """
        V = len(self.vocabulario)
        contexto = ngrama[:-1]
        c_ngrama = self.conteos_ngrama.get(ngrama, 0)
        c_contexto = self.conteos_contexto.get(contexto, 0)
        return (c_ngrama + self.k) / (c_contexto + self.k * V)

    def perplejidad(self, frase: str) -> float:
        """
        Calcula la perplejidad del modelo sobre una frase.
        PP = exp(-1/N * sum(log P(wi|contexto)))
        
        Valores más bajos = frase más "esperada" por el modelo.
        """
        if not self.entrenado:
            return float("inf")

        tokens = _tokenizar_simple(frase)
        if len(tokens) < self.n:
            return float("inf")

        log_prob_total = 0.0
        n_tokens = 0

        for i in range(len(tokens) - self.n + 1):
            ngrama = tuple(tokens[i:i + self.n])
            p = self.probabilidad(ngrama)
            if p > 0:
                log_prob_total += math.log(p)
            else:
                log_prob_total += math.log(1e-10)
            n_tokens += 1

        if n_tokens == 0:
            return float("inf")

        return round(math.exp(-log_prob_total / n_tokens), 4)

    def top_bigramas_por_contexto(self, contexto: str, top_n: int = 10) -> list[dict]:
        """
        Devuelve los top_n tokens más probables dado un contexto (una palabra).
        Para bigramas: P(w2 | contexto).
        """
        contexto_tok = tuple(_tokenizar_simple(contexto)[1:-1])  # sin <s> y </s>
        if not contexto_tok:
            return []

        # Buscar todos los n-gramas que empiezan con este contexto
        candidatos = []
        for ngrama, count in self.conteos_ngrama.items():
            if ngrama[:-1] == contexto_tok:
                p = self.probabilidad(ngrama)
                candidatos.append({
                    "contexto": " ".join(contexto_tok),
                    "siguiente": ngrama[-1],
                    "conteo": count,
                    "probabilidad": round(p, 6),
                })

        candidatos.sort(key=lambda x: -x["probabilidad"])
        return candidatos[:top_n]

    def tabla_probabilidades(self, top_contextos: int = 10) -> list[dict]:
        """
        Devuelve una tabla con los top contextos y sus distribuciones.
        Útil para mostrar en el dashboard.
        """
        # Ordenar contextos por frecuencia
        contextos_top = sorted(
            self.conteos_contexto.items(),
            key=lambda x: -x[1]
        )[:top_contextos]

        tabla = []
        for contexto, freq in contextos_top:
            top = self.top_bigramas_por_contexto(" ".join(contexto))[:5]
            tabla.append({
                "contexto": " ".join(contexto),
                "frecuencia": freq,
                "top_siguientes": top,
            })
        return tabla

    def guardar(self, path: Path = MODEL_PATH):
        """Persiste el modelo entrenado en JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        datos = {
            "n": self.n,
            "k": self.k,
            "vocabulario": list(self.vocabulario),
            "conteos_ngrama": {str(k): v for k, v in self.conteos_ngrama.items()},
            "conteos_contexto": {str(k): v for k, v in self.conteos_contexto.items()},
            "entrenado": self.entrenado,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    def cargar(self, path: Path = MODEL_PATH) -> bool:
        """Carga el modelo desde JSON. Devuelve True si tuvo éxito."""
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                datos = json.load(f)
            self.n = datos["n"]
            self.k = datos["k"]
            self.vocabulario = set(datos["vocabulario"])
            self.conteos_ngrama = defaultdict(int, {
                eval(k): v for k, v in datos["conteos_ngrama"].items()
            })
            self.conteos_contexto = defaultdict(int, {
                eval(k): v for k, v in datos["conteos_contexto"].items()
            })
            self.entrenado = datos["entrenado"]
            return True
        except Exception:
            return False


# =========================
# INSTANCIA GLOBAL (singleton)
# =========================
_modelo_bigrama: ModeloNGramas | None = None
_modelo_trigrama: ModeloNGramas | None = None


def get_modelo(n: int = 2, k: float = 1.0) -> ModeloNGramas:
    """
    Devuelve el modelo entrenado (singleton).
    Si no existe, lo entrena con el corpus del dominio y lo persiste.
    """
    global _modelo_bigrama, _modelo_trigrama

    if n == 2:
        if _modelo_bigrama is not None and _modelo_bigrama.entrenado:
            return _modelo_bigrama
        modelo = ModeloNGramas(n=2, k=k)
        path = Path(__file__).parent.parent / "data" / "ngram_bigrama.json"
        if not modelo.cargar(path):
            corpus = preparar_corpus(CORPUS_PICCOLO)
            modelo.entrenar(corpus)
            modelo.guardar(path)
        _modelo_bigrama = modelo
        return modelo

    else:  # trigrama
        if _modelo_trigrama is not None and _modelo_trigrama.entrenado:
            return _modelo_trigrama
        modelo = ModeloNGramas(n=3, k=k)
        path = Path(__file__).parent.parent / "data" / "ngram_trigrama.json"
        if not modelo.cargar(path):
            corpus = preparar_corpus(CORPUS_PICCOLO)
            modelo.entrenar(corpus)
            modelo.guardar(path)
        _modelo_trigrama = modelo
        return modelo


def calcular_perplejidad(texto: str, n: int = 2, k: float = 1.0) -> float:
    """API simplificada: calcula perplejidad de un texto."""
    modelo = get_modelo(n=n, k=k)
    return modelo.perplejidad(texto)


def reentrenar(k: float = 1.0):
    """Reentrena ambos modelos con el corpus del dominio y los persiste."""
    global _modelo_bigrama, _modelo_trigrama
    corpus = preparar_corpus(CORPUS_PICCOLO)

    bigrama = ModeloNGramas(n=2, k=k)
    bigrama.entrenar(corpus)
    bigrama.guardar(Path(__file__).parent.parent / "data" / "ngram_bigrama.json")
    _modelo_bigrama = bigrama

    trigrama = ModeloNGramas(n=3, k=k)
    trigrama.entrenar(corpus)
    trigrama.guardar(Path(__file__).parent.parent / "data" / "ngram_trigrama.json")
    _modelo_trigrama = trigrama

    return bigrama, trigrama


if __name__ == "__main__":
    print("Entrenando modelos N-gramas con corpus Piccolo...")
    b, t = reentrenar(k=1.0)
    print(f"Vocabulario bigrama: {len(b.vocabulario)} tokens")
    print(f"N-gramas bigrama: {len(b.conteos_ngrama)}")

    frases_test = [
        "para qué sirve el enalapril",
        "quiero un helado de chocolate",
        "la atorvastatina baja el colesterol",
        "el gato subió al árbol",
    ]
    print("\nPerplejidades:")
    for f in frases_test:
        pp_b = b.perplejidad(f)
        pp_t = t.perplejidad(f)
        print(f"  [{pp_b:8.2f} | {pp_t:8.2f}]  {f}")

    print("\nTop bigramas para contexto 'enalapril':")
    for item in b.top_bigramas_por_contexto("enalapril"):
        print(f"  '{item['siguiente']}' → P={item['probabilidad']:.4f} (n={item['conteo']})")
