# ADR-06: Decodificación greedy y respuestas de ≈300 tokens

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Generación · **Relacionado:** RF-GE-02..04, RNF-QR-02, [SPEC-023](../spec/SPEC-023-generacion-olmo.md)

## Contexto
El juez compara con respuestas de referencia concisas. Sin vLLM, cada token generado cuesta tiempo. Además se necesita reproducibilidad.

## Decisión
`do_sample=False` y `max_new_tokens≈300` desde E1 (2048 en E0). El prompt pide el dato clave en la primera oración.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Muestreo + votación (self-consistency) | Multiplica el tiempo por pregunta |
| Respuestas largas | Más tiempo y más riesgo de contradecir la referencia |

## Consecuencias
- Positivas: determinismo (RNF-RP-01) y menos tiempo.
- Negativas: la respuesta puede truncarse si la justificación es larga; se controla con el prompt.
- Verificación: CA-GE-01, CA-RP-01.
