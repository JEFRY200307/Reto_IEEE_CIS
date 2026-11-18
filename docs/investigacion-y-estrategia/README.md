# Investigación y estrategia: IEEE CIS DSQA Challenge 2026

Esta carpeta reúne la base bibliográfica seleccionada y la estrategia experimental para competir en el **IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs**. Complementa a [`../contexto-inicial/`](../contexto-inicial/), que contiene la información oficial del reto.

Elaborado el 26-27 de octubre de 2026.

## Pregunta que guía el trabajo

> ¿Cómo influyen las estrategias de recuperación y selección de información textual en la **precisión** y la **eficiencia** de un LLM (OLMo 3.1 32B) para responder preguntas especializadas, y qué aporta una capa de **Inteligencia Computacional** a esas decisiones?

## Índice

| # | Archivo | Contenido |
|---|---------|-----------|
| 1 | [01-referencias.md](01-referencias.md) | Las 16 referencias seleccionadas, en formato IEEE, con cuartil y su aporte a la investigación |
| 2 | [02-estrategia-vision-general.md](02-estrategia-vision-general.md) | Pipeline de 5 etapas, estrategias E0 a E6, metodología de evaluación, recursos y riesgos |
| 3 | [estrategias/E0-base-estandar.md](estrategias/E0-base-estandar.md) | E0: baseline RAG del starter kit |
| 4 | [estrategias/E1-preparacion-optimizada.md](estrategias/E1-preparacion-optimizada.md) | E1: extracción, chunking, embeddings y salida concisa |
| 5 | [estrategias/E2-recuperacion-hibrida.md](estrategias/E2-recuperacion-hibrida.md) | E2: BM25 + denso con RRF |
| 6 | [estrategias/E3-recuperacion-dos-fases.md](estrategias/E3-recuperacion-dos-fases.md) | E3: filtro por documento + reranker + selección de contexto |
| 7 | [estrategias/E4-verificacion-clasica.md](estrategias/E4-verificacion-clasica.md) | E4: verificación de evidencia con umbrales (estilo CRAG) |
| 8 | [estrategias/E5-fusion-difusa.md](estrategias/E5-fusion-difusa.md) | E5: fusión difusa OWA (CI 1) |
| 9 | [estrategias/E6-verificacion-qfcm.md](estrategias/E6-verificacion-qfcm.md) | E6: verificación con q-FCM calibrado con CMA-ES (CI 2 y 3) |

## Resumen en 30 segundos

- **Sistema:** RAG de 5 etapas (preparación, recuperación, verificación, contexto, generación) con control de recursos transversal.
- **Estrategias:** una base estándar (E0) y seis estrategias incrementales (E1 a E6). Cada una cambia un solo bloque para medir su aporte.
- **Inteligencia Computacional:** fusión difusa de evidencias (E5), verificación con mapa cognitivo difuso cuasi-no lineal (E6) y calibración evolutiva (E6).
- **Evaluación:** cada paso es una hipótesis que se puede rechazar. Se mide precisión por dominio, recall@5 y tiempo, con ablación incremental y leave-one-out.
- **Referencias:** 16 seleccionadas; 8 forman el núcleo mínimo para el paper de 4 páginas.
