# ADR-10: Calibración CMA-ES solo fuera de línea

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** CI · **Relacionado:** RF-OF-05, [SPEC-029](../spec/SPEC-029-calibracion-cmaes.md)

## Contexto
Durante la evaluación no hay datos etiquetados ni tiempo para optimizar, y la librería `cma` no está en el entorno de Codabench.

## Decisión
CMA-ES corre antes del envío (en la laptop o en AWS) sobre el banco local y exporta los parámetros finales a `resources/owa_params.json` y `resources/qfcm_params.json`.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Calibrar en línea | Sin etiquetas, sin tiempo y sin la librería |
| Solo pesos de experto | Válido como punto de partida; la calibración puede mejorarlos |

## Consecuencias
- Positivas: costo nulo durante la evaluación.
- Negativas: riesgo de sobreajuste con pocas preguntas, mitigado con validación cruzada e intervalos de experto.
- Verificación: brecha entre calibración y prueba en el banco local.
