# ADR-12: El sistema nunca se abstiene

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Generación · **Relacionado:** RF-VE-07, RF-GE-05, RNF-QR-05

## Contexto
El juez es binario y no da crédito parcial: "no lo sé" siempre vale 0.

## Decisión
Si la evidencia es débil, se responde con la mejor evidencia disponible; si no hay ninguna, con el conocimiento del modelo.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Abstenerse cuando la evidencia es débil | Siempre 0 puntos |

## Consecuencias
- Positivas: toda respuesta tiene alguna probabilidad de ser correcta.
- Negativas: en la Fase 2 los expertos podrían valorar la prudencia; se compensa con un tono fundamentado, no con abstención.
- Verificación: CA-VE-05.
