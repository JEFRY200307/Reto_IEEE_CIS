# ADR-09: El juez OLMo es una entrada del q-FCM, no el decisor

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Verificación · **Relacionado:** RF-VE-02, RF-VE-04, [SPEC-018](../spec/SPEC-018-juez-olmo-s5.md), [SPEC-020](../spec/SPEC-020-decisor-qfcm.md)

## Contexto
OLMo puede estimar si la evidencia alcanza ($s_5$), pero los LLM tienden a sobreestimar la suficiencia.

## Decisión
$s_5$ es el concepto $C_5$ del q-FCM y se combina con las señales numéricas $s_1$-$s_4$. Nunca decide solo.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Juez OLMo como decisor único | Sesgo hacia "Sí", sin control |
| Sin juez | Se pierde la única señal semántica |

## Consecuencias
- Positivas: señal semántica barata (una pasada, sin generar).
- Negativas: +~3 s por pregunta; se desactiva en modo rápido.
- Verificación: leave-one-out de $s_5$ (criterio de E6 en §6.2).
