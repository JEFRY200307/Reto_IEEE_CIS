# ADR-01: Inferencia en bf16 con `transformers` y atención `sdpa`, sin cuantizar

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Generación · **Relacionado:** RF-GE-01, [SPEC-023](../spec/SPEC-023-generacion-olmo.md)

## Contexto
El entorno de Codabench no tiene vLLM ni flash-attn. OLMo 3.1 32B en bf16 ocupa ~64 GB y la H100 tiene 80 GB.

## Decisión
Cargar OLMo con `AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")`.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| 8 bits / 4 bits con `bitsandbytes` | Baja la calidad y no acelera sin kernels dedicados; en una H100 no hace falta |
| Atención `eager` | Más lenta y con más memoria que `sdpa` |

## Consecuencias
- Positivas: máxima fidelidad del modelo; mismo comportamiento en AWS p5 y en Codabench.
- Negativas: quedan ~14 GB para KV cache, embedder y reranker, lo que obliga a limitar el contexto (≤ 6k tokens).
- Verificación: pico de VRAM ≤ 76 GB en una sesión de AWS (RNF-RC-03).
