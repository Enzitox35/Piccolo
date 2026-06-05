"""
tests/eval_wer.py — Evaluación del Reconocimiento Automático del Habla (ASR)
Sistema Piccolo

Cómo usar:
    python tests/eval_wer.py

Qué hace:
    - Carga 10 pares (referencia, hipótesis) del dominio medicamentos
    - Calcula WER para cada par usando distancia de edición a nivel de palabras
    - Muestra media, desviación estándar y tabla completa
    - Guarda los resultados en tests/resultados_wer.txt
"""

import sys
import statistics
from pathlib import Path

# Asegurar que Python encuentre los módulos del proyecto
RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ))

from modules.asr import calcular_wer

# =========================
# PARES DE PRUEBA
# (referencia = lo que debería decir el sistema)
# (hipotesis  = lo que transcribió realmente el ASR)
#
# Para obtener las hipótesis reales:
# 1. Grabá cada frase de referencia en voz alta
# 2. El sistema la transcribe → eso es la hipótesis
# 3. Reemplazá los valores de hipotesis_real abajo
# =========================
PARES_PRUEBA = [
    {
        "id": 1,
        "referencia": "para qué sirve el enalapril",
        "hipotesis":  "para que sirve el enalapril",   # reemplazar con transcripción real
    },
    {
        "id": 2,
        "referencia": "cuándo tengo que tomar la metformina",
        "hipotesis":  "cuando tengo que tomar la metformina",
    },
    {
        "id": 3,
        "referencia": "qué cuidados tengo que tener con el omeprazol",
        "hipotesis":  "que cuidados tengo que tener con el omeprazol",
    },
    {
        "id": 4,
        "referencia": "qué hace el losartán en el cuerpo",
        "hipotesis":  "que hace el losartan en el cuerpo",
    },
    {
        "id": 5,
        "referencia": "dame un consejo para tomar la levotiroxina",
        "hipotesis":  "dame un consejo para tomar la levotiroxina",
    },
    {
        "id": 6,
        "referencia": "para qué es la atorvastatina",
        "hipotesis":  "para que es la atorvastatina",
    },
    {
        "id": 7,
        "referencia": "tengo que tomar la aspirina con comida",
        "hipotesis":  "tengo que tomar la aspirina con comida",
    },
    {
        "id": 8,
        "referencia": "qué tipo de medicamento es el clonazepam",
        "hipotesis":  "que tipo de medicamento es el clonazepam",
    },
    {
        "id": 9,
        "referencia": "para quién es la furosemida",
        "hipotesis":  "para quien es la furosemida",
    },
    {
        "id": 10,
        "referencia": "qué cuidados tiene la amlodipina",
        "hipotesis":  "que cuidados tiene la amlodipina",
    },
]


def ejecutar_evaluacion():
    print("=" * 60)
    print("  SISTEMA PICCOLO — EVALUACIÓN ASR (WER)")
    print("=" * 60)
    print()

    resultados = []

    for par in PARES_PRUEBA:
        wer = calcular_wer(par["referencia"], par["hipotesis"])
        resultados.append({
            "id": par["id"],
            "referencia": par["referencia"],
            "hipotesis": par["hipotesis"],
            "wer": wer,
        })
        estado = "✅" if wer == 0.0 else ("⚠️" if wer < 0.3 else "❌")
        print(f"{estado} Frase {par['id']:2d} | WER = {wer:.4f}")
        print(f"   REF: {par['referencia']}")
        print(f"   HIP: {par['hipotesis']}")
        print()

    # Estadísticas globales
    wer_lista = [r["wer"] for r in resultados]
    media = statistics.mean(wer_lista)
    std   = statistics.stdev(wer_lista) if len(wer_lista) > 1 else 0.0
    minimo = min(wer_lista)
    maximo = max(wer_lista)

    print("=" * 60)
    print("  RESULTADOS GLOBALES")
    print("=" * 60)
    print(f"  Total de frases evaluadas : {len(resultados)}")
    print(f"  WER promedio              : {media:.4f}  ({media*100:.1f}%)")
    print(f"  Desviación estándar       : {std:.4f}")
    print(f"  WER mínimo                : {minimo:.4f}")
    print(f"  WER máximo                : {maximo:.4f}")
    print(f"  Frases perfectas (WER=0)  : {sum(1 for w in wer_lista if w == 0)}/{len(wer_lista)}")
    print()

    # Guardar en archivo de texto
    salida = Path(__file__).parent / "resultados_wer.txt"
    with open(salida, "w", encoding="utf-8") as f:
        f.write("SISTEMA PICCOLO — RESULTADOS EVALUACIÓN ASR (WER)\n")
        f.write("=" * 60 + "\n\n")
        for r in resultados:
            f.write(f"Frase {r['id']:2d} | WER = {r['wer']:.4f}\n")
            f.write(f"  REF: {r['referencia']}\n")
            f.write(f"  HIP: {r['hipotesis']}\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"WER Promedio        : {media:.4f} ({media*100:.1f}%)\n")
        f.write(f"Desviación estándar : {std:.4f}\n")
        f.write(f"WER mínimo          : {minimo:.4f}\n")
        f.write(f"WER máximo          : {maximo:.4f}\n")

    print(f"  Resultados guardados en: {salida}")
    print()
    return {"media": media, "std": std, "min": minimo, "max": maximo, "detalle": resultados}


if __name__ == "__main__":
    ejecutar_evaluacion()
