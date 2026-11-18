# ADR-08: Verificar la evidencia recuperada, no la respuesta generada

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Verificación · **Relacionado:** RF-VE-*, [SPEC-017](../spec/SPEC-017-senales-de-evidencia.md), [SPEC-021](../spec/SPEC-021-acciones-de-verificacion.md)

## Contexto
Un RAG sin control confía en lo recuperado aunque sea un distractor. Verificar la respuesta exigiría generar dos veces.

## Decisión
La etapa 3 juzga si la evidencia permite responder (estilo CRAG) **antes** de generar, y decide si aceptar, refinar o reintentar la recuperación.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Autoverificación de la respuesta | Duplica la generación, que es la parte más cara |
| Sin verificación | No rescata las preguntas cuya primera búsqueda falló |

## Consecuencias
- Positivas: una sola generación por pregunta; costo acotado.
- Negativas: no detecta errores de razonamiento cuando la evidencia es buena.
- Verificación: criterio de E4 en §6.2.
