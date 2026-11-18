# dsqa — IEEE CIS DSQA Challenge 2026

Sistema de preguntas y respuestas con recuperación (RAG) e Inteligencia Computacional para **IFMIF-DONES** y **papers de IA**, sobre el modelo fijo OLMo 3.1 32B Instruct.

- Documentación técnica: [docs/documentacion-tecnica/](docs/documentacion-tecnica/README.md) (arquitectura, requisitos, [ADR](docs/documentacion-tecnica/ADR/README.md), [specs](docs/documentacion-tecnica/spec/README.md), [guía de despliegue](docs/documentacion-tecnica/08-guia-de-despliegue.md)).
- Infraestructura de AWS (Terraform): repositorio aparte `dsqa-infra`.

## Estructura

```
src/dsqa/        sistema (lo que viaja en el zip): ingest, index, retrieval, verify, context, generate, runtime
submission/      main.py: answer(question, corpus_dir, model_id) -> str
configs/         e0.yaml … e6.yaml (cada una hereda de la anterior), ablations/, variants/
resources/       prompts, glosario DONES, léxico de dominios, parámetros OWA y q-FCM
scripts/         build_submission.py, check_submission.py
eval/            run_local, retrieval_metrics, judge, stats, report + bench/ (25 preguntas de muestra)
offline/         download_models, fetch_public_pdfs, build_glossary, build_synthetic_qa, calibrate_cmaes
infra/aws/       sesiones de trabajo en AWS (push, launch, pull…)
tests/           pruebas unitarias e integración (sin GPU: modelos simulados)
```

## Estrategias

| Config | Qué agrega |
|---|---|
| `e0` | Baseline del kit: Docling, chunks de 800, MiniLM, 10k tokens |
| `e1` | PyMuPDF en paralelo, limpieza, padre-hijo, bge-base, top-5, prompts por dominio |
| `e2` | BM25 + denso con RRF, glosario DONES, erratas |
| `e3` | Filtro por paper nombrado, bge-reranker + MMR, contexto por umbral |
| `e4` | Verificación con umbrales, 1 reintento, Program of Thoughts |
| `e5` | Fusión difusa OWA (CI 1) |
| `e6` | Verificación con q-FCM + juez OLMo (CI 2), calibrado con CMA-ES (CI 3) |

## En la laptop (sin GPU)

```bash
pip install -r requirements-dev.txt
```
```bash
python -m pytest
```
Recuperación sin LLM sobre PDFs públicos (recall@k):
```bash
python eval/run_local.py --configs configs/e2.yaml --corpus data/public_pdfs --retrieval-only --out experiments/runs/local
```
```bash
python eval/retrieval_metrics.py --run experiments/runs/local/e2
```

## Construir y comprobar un envío

1. Modelos auxiliares (una vez, con internet): `python offline/download_models.py` (y `--what minilm docling` para E0).
2. Commit y etiqueta: `git tag sub-AAAA-MM-DD`.
3. Construir y comprobar:
   ```bash
   python scripts/build_submission.py --config configs/e3.yaml
   ```
   ```bash
   python scripts/check_submission.py dist/dsqa_e3_AAAA-MM-DD.zip
   ```
4. Prueba de humo local sin GPU (opcional):
   ```bash
   DSQA_LLM_BACKEND=echo DSQA_ENCODER_BACKEND=hash DSQA_RERANKER_BACKEND=overlap python scripts/check_submission.py dist/<zip> --smoke --corpus data/public_pdfs --n 5
   ```
5. Ensayo general en AWS con OLMo real: añade a una lista de trabajos
   `python scripts/check_submission.py dist/<zip> --smoke --corpus data/public_pdfs --n 50 --timed`.
6. Subir el zip a Codabench antes de las 23:55 UTC y registrar el resultado en `experiments/submissions.md`.

## En AWS

Ver [infra/aws/README.md](infra/aws/README.md). Ejemplo de lista de trabajos para comparar estrategias:

```text
python eval/run_local.py --configs configs/e1.yaml configs/e2.yaml configs/e3.yaml --corpus data/public_pdfs --model-id allenai/Olmo-3.1-32B-Instruct --out experiments/runs/$DSQA_SESSION --resume
python eval/judge.py --run experiments/runs/$DSQA_SESSION/e1 --backend olmo
python eval/judge.py --run experiments/runs/$DSQA_SESSION/e2 --backend olmo
python eval/judge.py --run experiments/runs/$DSQA_SESSION/e3 --backend olmo
```

## Variables de entorno útiles

| Variable | Efecto |
|---|---|
| `DSQA_CONFIG` | Config a usar en lugar de `config.yaml` junto a `main.py` |
| `DSQA_LOG_LEVEL` | `INFO` o `DEBUG` para ver la inicialización y los niveles de respaldo (por defecto `WARNING`) |
| `DSQA_LLM_BACKEND=echo` | OLMo simulado (solo pruebas) |
| `DSQA_ENCODER_BACKEND=hash` | Embedder simulado sin modelos (solo pruebas) |
| `DSQA_RERANKER_BACKEND=overlap` | Reranker simulado sin modelos (solo pruebas) |

## Pendiente de completar a mano

- `eval/bench/gold_chunks.json`: el texto exacto que responde cada pregunta de muestra (para recall@k y la calibración de OWA).
- `eval/bench/pdf_list.csv`: URLs de PDFs públicos de los sitios fuente para el banco local.
- `resources/glossary_dones.json`: ampliar con `offline/build_glossary.py` cuando haya PDFs de DONES.
