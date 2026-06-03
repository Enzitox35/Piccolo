"""
tests/eval_ner.py — Evaluación del Reconocimiento de Entidades (NER)
Sistema Piccolo

Cómo usar:
    python tests/eval_ner.py

Qué hace:
    - Evalúa la extracción de entidades (MEDICAMENTO, DOSIS, FRECUENCIA)
    - Sobre 20 ejemplos anotados manualmente
    - Calcula Accuracy global y por tipo de entidad
    - Guarda los resultados en tests/resultados_ner.txt
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ))

from modules.nlp import extraer_entidades
from modules.dashboard import EJEMPLOS_NER, calcular_accuracy_ner


def ejecutar_evaluacion():
    print("=" * 65)
    print("  SISTEMA PICCOLO — EVALUACIÓN NER (Accuracy)")
    print("=" * 65)
    print(f"  Total de ejemplos: {len(EJEMPLOS_NER)}")
    print()

    resultado = calcular_accuracy_ner(EJEMPLOS_NER)
    detalle_filas = []

    for ej in EJEMPLOS_NER:
        obtenidas = extraer_entidades(ej["texto"])
        esperadas = ej["entidades_esperadas"]

        correctos_ej = 0
        total_ej = 0
        for tipo, vals in esperadas.items():
            for val in vals:
                total_ej += 1
                obtenidas_tipo = [v.lower() for v in obtenidas.get(tipo, [])]
                if val.lower() in obtenidas_tipo:
                    correctos_ej += 1

        estado = "✅" if correctos_ej == total_ej else ("⚠️" if correctos_ej > 0 else "❌")
        print(f"{estado} '{ej['texto']}'")
        print(f"   Esperadas : {esperadas}")
        print(f"   Obtenidas : { {k: v for k, v in obtenidas.items() if v} }")
        print(f"   Correctas : {correctos_ej}/{total_ej}")
        print()

        detalle_filas.append({
            "texto": ej["texto"],
            "esperadas": esperadas,
            "obtenidas": {k: v for k, v in obtenidas.items() if v},
            "correctas": correctos_ej,
            "total": total_ej,
        })

    print("=" * 65)
    print("  RESULTADOS GLOBALES")
    print("=" * 65)
    print(f"  Accuracy global     : {resultado['accuracy_global']:.4f}  ({resultado['accuracy_global']*100:.1f}%)")
    print(f"  Entidades correctas : {resultado['correctos']} / {resultado['total']}")
    print()
    print("  Accuracy por tipo:")
    for tipo, acc in resultado["accuracy_por_tipo"].items():
        barra = "█" * int(acc * 20) + "░" * (20 - int(acc * 20))
        print(f"    {tipo:<15} {barra}  {acc:.1%}")
    print()

    # Guardar resultados
    salida = Path(__file__).parent / "resultados_ner.txt"
    with open(salida, "w", encoding="utf-8") as f:
        f.write("SISTEMA PICCOLO — RESULTADOS EVALUACIÓN NER\n")
        f.write("=" * 65 + "\n\n")
        for fila in detalle_filas:
            f.write(f"Texto     : {fila['texto']}\n")
            f.write(f"Esperadas : {fila['esperadas']}\n")
            f.write(f"Obtenidas : {fila['obtenidas']}\n")
            f.write(f"Resultado : {fila['correctas']}/{fila['total']}\n\n")
        f.write("=" * 65 + "\n")
        f.write(f"Accuracy global : {resultado['accuracy_global']:.4f} ({resultado['accuracy_global']*100:.1f}%)\n")
        for tipo, acc in resultado["accuracy_por_tipo"].items():
            f.write(f"  {tipo}: {acc:.4f}\n")

    print(f"  Resultados guardados en: {salida}")
    return resultado


if __name__ == "__main__":
    ejecutar_evaluacion()
