# ADR-07: Umbral fijo del modo rápido sin conocer la fase

**Estado:** Propuesta · **Fecha:** 2026-10-29 · **Área:** Runtime · **Relacionado:** RF-RT-04, SUP-07, [SPEC-002](../spec/SPEC-002-reloj-global-y-modos.md)

## Contexto
El límite público (1 h, ~50 preguntas) es duro; el privado (2 h, ~100 preguntas) es blando. El sistema no sabe en qué fase corre ni cuántas preguntas quedan.

## Decisión (provisional)
Modo rápido a los 50 min y modo emergencia a los 56 min, ambos configurables. En la fase privada esto puede degradar las últimas ~40 preguntas.

## Pendiente
Preguntar en Discord si existe una variable de entorno u otro dato que indique la fase o el número de preguntas. Si existe, reemplazar este ADR por un presupuesto por pregunta según la fase.

## Alternativas consideradas
| Alternativa | Por qué no (por ahora) |
|---|---|
| Umbral de 110 min | Haría fallar el envío en la fase pública |
| Inferir la fase por el tamaño del corpus | Probablemente el corpus es el mismo en ambas fases |

## Consecuencias
- Positivas: en la fase pública el pipeline nunca supera 1 h.
- Negativas: posible pérdida de precisión en la fase privada.
- Verificación: CA-RT-01; tiempo real en Codabench.
