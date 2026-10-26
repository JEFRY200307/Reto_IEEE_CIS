# Contexto inicial del proyecto — IEEE CIS DSQA Challenge 2026

**IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs**

Esta carpeta reúne toda la información oficial del reto, organizada por tema. Se recopiló el **26 de octubre de 2026** desde la página oficial, las bases oficiales (PDF), la página de Codabench, el repositorio del kit de inicio y el video de presentación.

## Resumen en 30 segundos

- **Tarea:** construir un sistema que responda preguntas de expertos en dos dominios muy especializados: **IFMIF-DONES** (acelerador de partículas en Granada) y **papers de investigación en IA**.
- **Modelo fijo:** `allenai/Olmo-3.1-32B-Instruct`. No se puede cambiar el modelo base, solo adaptarlo (RAG, prompts, adaptadores LoRA, grafos de conocimiento, etc.).
- **Entrega:** un `.zip` con `main.py` que expone `answer(question, corpus_dir, model_id) -> str`.
- **Límites:** 1 GPU H100 (80 GB), **1 hora** en total (2 h en el leaderboard privado), **sin internet**, **1 GB** máximo descomprimido, **1 envío por día**.
- **Puntuación:** precisión balanceada por dominio, juzgada por un LLM oculto (correcto/incorrecto). Los 20 mejores pasan a evaluación por expertos, donde la **innovación técnica pesa 40 %**.
- **Fechas clave:** registro y equipos hasta el **1 nov 2026**; último envío el **30 nov 2026**; resultados finales el **14 dic 2026**.
- **Premios:** USD 20 000 en total (9 000 / 5 000 / 3 000 / 1 500 / 1 500).

## Índice

| # | Archivo | Contenido |
|---|---------|-----------|
| 1 | [01-vision-general.md](01-vision-general.md) | Qué es el reto, motivación, dominios, tipos de preguntas, video |
| 2 | [02-cronograma.md](02-cronograma.md) | Fechas clave y fases |
| 3 | [03-reglas-y-bases-oficiales.md](03-reglas-y-bases-oficiales.md) | Elegibilidad, restricciones, juego limpio y resumen de las bases legales |
| 4 | [04-evaluacion.md](04-evaluacion.md) | Métricas y fórmulas de la Fase 1 y la Fase 2 |
| 5 | [05-formato-de-envio.md](05-formato-de-envio.md) | Contrato de `main.py`, formato del zip, entorno de ejecución, proceso en Codabench |
| 6 | [06-kit-de-inicio.md](06-kit-de-inicio.md) | Repositorio del starter kit: baselines zero-shot y RAG |
| 7 | [07-dataset-de-muestra-y-corpus.md](07-dataset-de-muestra-y-corpus.md) | Las 25 preguntas de ejemplo y las fuentes del corpus |
| 8 | [08-entorno-y-dependencias.md](08-entorno-y-dependencias.md) | Librerías preinstaladas en el entorno de evaluación |
| 9 | [09-premios-y-organizacion.md](09-premios-y-organizacion.md) | Premios, organizadores y comité científico |
| 10 | [10-enlaces.md](10-enlaces.md) | Todos los enlaces oficiales en un solo lugar |
| 11 | [11-implicaciones-para-la-solucion.md](11-implicaciones-para-la-solucion.md) | Análisis propio: qué significan estas reglas para el diseño de la solución |

## Carpeta `recursos/`

Copias locales de archivos oficiales para consulta rápida:

| Archivo | Origen |
|---------|--------|
| [recursos/sample_qa.json](recursos/sample_qa.json) | 25 pares pregunta/respuesta de ejemplo ([starter kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/sample/sample_qa.json), licencia MIT) |
| [recursos/sites.txt](recursos/sites.txt) | Sitios de donde proviene el corpus ([starter kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/sample/sites.txt)) |
| [recursos/requirements-participant.txt](recursos/requirements-participant.txt) | Versiones exactas del entorno de evaluación ([starter kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit/blob/main/requirements-participant.txt)) |
| [recursos/bases-oficiales-contest-rules.pdf](recursos/bases-oficiales-contest-rules.pdf) | [Bases oficiales (PDF)](https://cis.taskforce.ieee.org/gpais/wp-content/uploads/sites/6/2026/09/IEEE-CIS-Technical-Challenge-on-Domain-Specific-Question-Answering-with-LLMs-Contest-Rules.pdf) |

> Las reglas pueden cambiar. Los organizadores anuncian cambios en [Discord](https://discord.gg/q6H7cJVkQQ) y por correo. Ante cualquier duda, manda la fuente oficial.
