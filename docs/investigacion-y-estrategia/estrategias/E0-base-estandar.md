# E0: Base estándar

[← Visión general](../02-estrategia-vision-general.md) · Siguiente: [E1 →](E1-preparacion-optimizada.md)

## Objetivo

Servir como **punto de comparación estándar**. Es el baseline RAG oficial del starter kit (`02_rag`), sin modificaciones. Toda mejora de E1 a E6 se reporta contra E0.

## Configuración

| Subetapa | Elección |
|---|---|
| 1a Extracción | Docling a Markdown (`do_ocr=False`, `do_table_structure=False`) |
| 1b Limpieza | Ninguna |
| 1c Chunking | Agrupación de párrafos en ~800 caracteres con 150 de solape |
| 1d Enriquecimiento | Ninguno |
| 1e Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, normalizados, en CPU |
| 1f Índices | Similitud coseno sobre los vectores |
| 2a Consulta | Pregunta original |
| 2b Buscadores | Solo denso |
| 2c Fusión | No aplica |
| 2d Reranker | No |
| 3 Verificación | No |
| 4 Contexto | Mejores fragmentos hasta llenar ~10 000 tokens |
| 5 Generación | Prompt genérico ("You are a scientific expert…"), greedy, `max_new_tokens=2048` |
| Control | Modelo e índice cacheados entre llamadas |

## Qué se espera

- **Precisión:** el piso de referencia de un RAG estándar.
- **Tiempo:** ~36 minutos para indexar el corpus y responder 50 preguntas, según los organizadores.

## Cómo se mide

- Un envío a Codabench del zip generado por `02_rag/build.sh`, sin cambios.
- Ejecución local sobre el banco de evaluación: precisión con juez local, recall@5 y tiempo por etapa.

## Para qué sirve además

- **Validar el banco local:** si la precisión local de E0 está muy lejos de la del leaderboard, el banco no es representativo.
- **Descomponer el tiempo:** medir cuánto tarda cada etapa (Docling, embeddings, generación) indica dónde está el mayor ahorro posible para E1.

## Referencias

- [1] Lewis et al., RAG (fundamento del enfoque).
- [2] Team OLMo, Olmo 3 (modelo).
- Starter kit oficial: https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit
