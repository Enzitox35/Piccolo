"""
tests/eval_search.py — Evaluación del Motor de Recuperación de Información (IR)
Sistema Piccolo

Cómo usar:
    python tests/eval_search.py

Qué hace:
    - Corre 10 consultas de prueba contra el índice TF-IDF
    - Calcula Precisión, Recall y F1 por consulta
    - Muestra tabla completa con promedios
    - Guarda los resultados en tests/resultados_search.txt
"""

import sys
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ))

from modules.search import MotorBusqueda, CORPUS_DOCUMENTOS, CONSULTAS_EVALUACION


def calcular_metricas(recuperados: list[str], relevantes: list[str]) -> dict:
    """Calcula Precisión, Recall y F1 para una consulta."""
    rec_set = set(recuperados)
    rel_set = set(relevantes)
    tp = len(rec_set & rel_set)
    precision = tp / len(rec_set) if rec_set else 0.0
    recall    = tp / len(rel_set) if rel_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)
    return {
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
        "tp": tp,
        "recuperados": list(rec_set),
        "relevantes":  list(rel_set),
    }


def ejecutar_evaluacion(top_n: int = 3):
    print("=" * 70)
    print("  SISTEMA PICCOLO — EVALUACIÓN MOTOR DE BÚSQUEDA IR (P / R / F1)")
    print("=" * 70)
    print(f"  Documentos en el índice : {len(CORPUS_DOCUMENTOS)}")
    print(f"  Consultas de prueba     : {len(CONSULTAS_EVALUACION)}")
    print(f"  Top-N recuperados       : {top_n}")
    print()

    # Construir el índice
    motor = MotorBusqueda()
    motor.construir_indice(CORPUS_DOCUMENTOS)
    print(f"  Términos únicos en índice: {len(motor.indice)}")
    print()

    resultados = []
    precision_lista = []
    recall_lista    = []
    f1_lista        = []

    for consulta, relevantes_reales in CONSULTAS_EVALUACION:
        docs_recuperados = motor.buscar(consulta, top_n=top_n)
        ids_recuperados  = [d["id"] for d in docs_recuperados]
        sims             = [d["similitud"] for d in docs_recuperados]

        metricas = calcular_metricas(ids_recuperados, relevantes_reales)
        precision_lista.append(metricas["precision"])
        recall_lista.append(metricas["recall"])
        f1_lista.append(metricas["f1"])

        estado = "✅" if metricas["f1"] >= 0.5 else ("⚠️" if metricas["f1"] > 0 else "❌")
        print(f"{estado} '{consulta}'")
        print(f"   Esperados  : {relevantes_reales}")
        print(f"   Recuperados: {ids_recuperados}")
        print(f"   Similitudes: {[round(s, 3) for s in sims]}")
        print(f"   P={metricas['precision']:.3f}  R={metricas['recall']:.3f}  F1={metricas['f1']:.3f}")
        print()

        resultados.append({
            "consulta": consulta,
            "esperados": relevantes_reales,
            "recuperados": ids_recuperados,
            **metricas,
        })

    # Estadísticas globales
    p_media  = statistics.mean(precision_lista)
    r_media  = statistics.mean(recall_lista)
    f1_media = statistics.mean(f1_lista)
    p_std    = statistics.stdev(precision_lista) if len(precision_lista) > 1 else 0.0
    r_std    = statistics.stdev(recall_lista)    if len(recall_lista) > 1    else 0.0
    f1_std   = statistics.stdev(f1_lista)        if len(f1_lista) > 1        else 0.0

    print("=" * 70)
    print("  RESULTADOS GLOBALES")
    print("=" * 70)
    print(f"  Precisión promedio  : {p_media:.4f}  (±{p_std:.4f})")
    print(f"  Recall promedio     : {r_media:.4f}  (±{r_std:.4f})")
    print(f"  F1 promedio         : {f1_media:.4f}  (±{f1_std:.4f})")
    print(f"  Consultas perfectas : {sum(1 for f in f1_lista if f == 1.0)}/{len(f1_lista)}")
    print()

    # Guardar en archivo
    salida = Path(__file__).parent / "resultados_search.txt"
    with open(salida, "w", encoding="utf-8") as f:
        f.write("SISTEMA PICCOLO — RESULTADOS EVALUACIÓN IR (P / R / F1)\n")
        f.write("=" * 70 + "\n\n")
        for r in resultados:
            f.write(f"Consulta    : {r['consulta']}\n")
            f.write(f"Esperados   : {r['esperados']}\n")
            f.write(f"Recuperados : {r['recuperados']}\n")
            f.write(f"P={r['precision']:.4f}  R={r['recall']:.4f}  F1={r['f1']:.4f}\n\n")
        f.write("=" * 70 + "\n")
        f.write(f"Precisión promedio : {p_media:.4f} (±{p_std:.4f})\n")
        f.write(f"Recall promedio    : {r_media:.4f} (±{r_std:.4f})\n")
        f.write(f"F1 promedio        : {f1_media:.4f} (±{f1_std:.4f})\n")

    print(f"  Resultados guardados en: {salida}")
    return {
        "precision": p_media, "recall": r_media, "f1": f1_media,
        "precision_std": p_std, "recall_std": r_std, "f1_std": f1_std,
        "detalle": resultados,
    }


if __name__ == "__main__":
    ejecutar_evaluacion(top_n=3)
