# 11. Implicaciones para la solución (análisis propio)

> Este archivo **no es información oficial**: es una lectura de las reglas para orientar el diseño. Las fuentes están en los archivos 01–10.

## Fechas urgentes (al 26 oct 2026)

- **1 nov 2026:** cierra el registro y la formación de equipos. Cada miembro debe haber llenado el [formulario](https://forms.gle/F7YHkE7PALziNpqk6) y estar en la organización de Codabench **antes** de esa fecha.
- Quedan ~35 envíos posibles (1 por día) hasta el 30 nov. Cada envío fallido gasta el día.

## Restricciones que condicionan el diseño

| Restricción | Consecuencia |
|-------------|--------------|
| Modelo base fijo (OLMo 3.1 32B) | La mejora viene de **qué contexto le damos** (RAG), **cómo le preguntamos** (prompts) y, como mucho, **adaptadores ligeros** (LoRA vía `peft`). |
| 1 h total en H100, incluyendo cargar el modelo | El modelo 32B en bf16 ocupa ~64 GB y tarda en cargar. Indexar el corpus con Docling se come buena parte del tiempo (el baseline RAG tarda ~36 min con 50 preguntas). Hay que medir y repartir el tiempo. |
| El corpus solo se ve en tiempo de ejecución | No se puede preindexar el corpus oficial. Opciones: (a) parsers más rápidos que Docling (p. ej. `pymupdf`); (b) **preconstruir offline** un índice propio a partir de los sitios fuente y combinarlo con el corpus en vivo. |
| Corpus con **distractores** | La recuperación debe ser precisa: híbrida (BM25 + denso), reranking, filtros por título de paper. |
| Sin vLLM ni flash-attn | La generación es lenta: conviene limitar `max_new_tokens` y la longitud del contexto. |
| 1 GB por envío | Cabe un embedder/reranker pequeño, un adaptador LoRA y un índice preconstruido, pero no mucho más. |
| Juez LLM binario con respuestas de referencia concisas | Respuestas **directas y precisas** primero (dato clave al inicio), luego una justificación breve. Evitar divagaciones que contradigan la referencia. |
| Precisión balanceada por dominio | DONES y AI Papers pesan **igual**, aunque haya menos preguntas de un dominio. No descuidar ninguno. |
| Desempate por tiempo | Ser más rápido solo importa en empates, pero el límite de tiempo sí es crítico. |
| Innovación técnica = 40 % de la nota final | Para ganar, no basta con un buen RAG: hace falta un componente de **Inteligencia Computacional** justificable y original (difuso, evolutivo, grafos de conocimiento, fusión dinámica…), bien documentado en el paper de 4 páginas. |

## Ideas iniciales a explorar

- **Recuperación híbrida** BM25 + embeddings (`FlagEmbedding`/BGE) con **reranker** cruzado, y detección del título del paper en la pregunta.
- **Ruteo por dominio** (DONES vs AI Papers) con prompts y estrategias distintas.
- **Grafo de conocimiento** de DONES (subsistemas, parámetros, valores numéricos) construido offline con `networkx`.
- **Fusión difusa** de puntuaciones de recuperación o de varias respuestas candidatas (componente CI para el paper).
- **Optimización evolutiva** de hiperparámetros del pipeline (tamaño de chunk, top-k, prompts) usando el dataset de muestra.
- **Evaluación local** con un juez LLM sobre las 25 preguntas de ejemplo antes de gastar envíos.
