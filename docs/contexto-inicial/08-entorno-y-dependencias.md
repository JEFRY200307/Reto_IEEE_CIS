# 8. Entorno de evaluación y dependencias

**Fuentes:** [requirements-participant.txt](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/requirements-participant.txt) (copia local: [recursos/requirements-participant.txt](recursos/requirements-participant.txt)) · [Codabench — How to participate](https://www.codabench.org/competitions/17954/)

Estas son las **versiones exactas** preinstaladas en el entorno de evaluación. Solo se puede usar lo que está en esta lista (no hay internet). Para pedir algo nuevo: canal **#dependencies** en [Discord](https://discord.gg/q6H7cJVkQQ).

> **No están instalados vLLM ni flash-attn.** La inferencia va por `transformers`/`accelerate` con atención `sdpa` o `eager`.

## Hardware

1× H100 (80 GB VRAM) · 32 núcleos CPU · 128 GB RAM · sin internet.

## Librerías por categoría

| Categoría | Paquetes |
|-----------|----------|
| **Framework base** | torch 2.8.0, torchvision 0.23.0, torchaudio 2.8.0 |
| **Inferencia** | triton 3.4.0, transformers 5.17.0, accelerate 1.15.0, bitsandbytes 0.50.2, kernels 0.15.2, safetensors 0.8.0, optimum 2.3.0, **peft 0.21.0**, datasets 5.0.1, einops 0.8.2, sentencepiece 0.2.2, tiktoken 0.14.0, huggingface_hub[cli] 1.31.0 |
| **RAG / recuperación** | sentence-transformers 6.0.1, **FlagEmbedding 1.4.2**, llama-index-core 0.14.24, llama-index-vector-stores-faiss 0.7.0, llama-index-vector-stores-chroma 0.6.0, langchain 1.4.0, langchain-community 0.4.2, langchain-text-splitters 1.1.2, **faiss-cpu 1.15.0**, chromadb 1.5.9, qdrant-client 1.19.1, **rank-bm25 0.2.2**, whoosh 2.7.4, rapidfuzz 3.14.5 |
| **Documentos / PDF** | **docling 2.127.0**, pypdf 6.19.0, pdfplumber 0.11.10, **pymupdf 1.28.2**, python-docx 1.2.0, beautifulsoup4 4.15.0, lxml 6.1.3, markdownify 1.2.3 |
| **NLP / texto** | nltk 3.10.3, spacy 3.8.16, regex 2026.9.10, ftfy 6.3.1, langdetect 1.0.9 |
| **Generación estructurada** | outlines 1.3.3, lm-format-enforcer 0.11.3, jsonschema 4.26.0, pydantic 2.13.5 |
| **Evaluación local** | evaluate 0.4.6, rouge-score 0.1.2, bert-score 0.3.13, sacrebleu 2.6.0 |
| **Datos / utilidades** | numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, scikit-learn 1.7.2, **networkx 3.4.2**, pyyaml 6.0.3, orjson 3.12.0, python-dotenv 1.2.3, tenacity 9.1.4, rich 15.0.0, tqdm 4.70.1, loguru 0.7.3, typer 0.26.8 |

## Notas prácticas

- **Pesos de modelos auxiliares** (embedders, rerankers, modelos de layout) **no** están en caché: hay que **incluirlos en el zip**, y cuentan para el límite de **1 GB**.
- Sin `faiss-gpu`: la búsqueda vectorial con FAISS va en CPU (32 núcleos).
- `peft` está disponible: se pueden enviar **adaptadores LoRA** propios para OLMo (el modelo base ya está en el entorno; solo se envía el adaptador).
- `bitsandbytes` permite cuantizar (8/4 bits) si se quiere ahorrar memoria o tiempo.
- `docling` sin `do_table_structure` (falta `cv2/libGL` en la imagen, según el kit).
