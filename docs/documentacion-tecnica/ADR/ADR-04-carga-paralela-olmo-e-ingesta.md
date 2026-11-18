# ADR-04: Cargar OLMo en paralelo con la ingesta del corpus

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Runtime · **Relacionado:** RF-RT-03, [SPEC-003](../spec/SPEC-003-inicializacion-y-cache.md)

## Contexto
Cargar ~64 GB de pesos es intensivo en disco; extraer y dividir PDFs es intensivo en CPU (32 núcleos). Hacerlo en secuencia suma ambos tiempos.

## Decisión
Un hilo carga OLMo mientras un pool de procesos ingiere el corpus. Los embeddings se calculan en GPU cuando termina la ingesta, porque el embedder cabe junto a OLMo.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Secuencial | Pierde varios minutos del límite de 1 h |
| Embeber en CPU para no compartir la GPU | Mucho más lento con bge-base |

## Consecuencias
- Positivas: el arranque dura el máximo de ambas tareas, no la suma.
- Negativas: más complejidad; hay que controlar la memoria de GPU compartida.
- Verificación: tiempos por etapa en la traza de una sesión de AWS (RNF-RD-04).
