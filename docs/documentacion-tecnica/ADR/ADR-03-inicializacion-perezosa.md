# ADR-03: Inicializar modelo e índices en la primera llamada a `answer()`

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Runtime · **Relacionado:** RF-RT-02, RF-IF-04, [SPEC-003](../spec/SPEC-003-inicializacion-y-cache.md)

## Contexto
Codabench importa `main.py` y llama `answer(question, corpus_dir, model_id)` una vez por pregunta, en el mismo proceso. Al importar no se conocen `corpus_dir` ni `model_id`.

## Decisión
La primera llamada dispara la inicialización completa (modelo, ingesta, índices, modelos auxiliares) y la guarda en un estado global del proceso. Las llamadas siguientes la reutilizan.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Inicializar al importar | No se conocen las rutas ni el modelo |
| Reindexar en cada pregunta | Imposible dentro de 1 h |

## Consecuencias
- Positivas: el costo fijo se paga una sola vez.
- Negativas: la primera pregunta tarda varios minutos; si la inicialización falla, el fallo debe recordarse para no repetirlo en cada pregunta.
- Verificación: CA-IF-04.
