# ADR-13: Modelos auxiliares guardados en fp16

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Empaquetado · **Relacionado:** RNF-RC-01/02, RF-OF-01, [SPEC-026](../spec/SPEC-026-empaquetado-y-chequeo.md)

## Contexto
El envío no puede superar 1 GB. bge-base (~440 MB en fp32) y bge-reranker-base (~1,1 GB en fp32) no caben juntos.

## Decisión
Guardar embedder y reranker en fp16 (`safetensors`): ~220 MB + ~560 MB. Límite interno de 950 MB.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| fp32 | No cabe |
| Modelos más pequeños (bge-small, reranker MiniLM) | Plan B si el tamaño o el tiempo lo exigen; medir recall@5 antes |

## Consecuencias
- Positivas: caben ambos modelos con margen.
- Negativas: diferencias numéricas mínimas frente a fp32.
- Verificación: CA-RT-05; recall@5 en fp16 ≈ fp32 en el banco local.
