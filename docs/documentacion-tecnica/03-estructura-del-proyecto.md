# 3. Estructura del proyecto

[← Arquitectura](02-arquitectura.md) · [Índice](README.md) · Siguiente: [Requisitos funcionales →](04-requisitos-funcionales.md)

## 3.1 Árbol del repositorio

```
Reto_IEEE_CIS/
├── README.md                      # Cómo instalar, probar y construir un envío
├── pyproject.toml                 # Metadatos, ruff, pytest, mypy
├── requirements-runtime.txt       # = requirements-participant.txt (versiones exactas del entorno)
├── requirements-dev.txt           # Solo local: pytest, ruff, mypy, cma, etc. (no viajan en el zip)
├── .gitignore                     # Ignora models/, dist/, runs/, corpus locales, *.zip
│
├── src/dsqa/                      # Paquete del sistema en línea (se copia al zip)
│   ├── __init__.py
│   ├── pipeline.py                # Orquestador de las 5 etapas
│   ├── types.py                   # Dataclasses: Page, Document, Chunk, Query, Candidate, Signals, Verdict, Trace
│   ├── runtime/
│   │   ├── config.py              # Carga y validación (pydantic) del YAML
│   │   ├── clock.py               # Reloj global y modos (normal / rápido / emergencia)
│   │   ├── state.py               # Caché del proceso e inicialización perezosa y paralela
│   │   ├── safety.py              # Cadena de degradación N0-N4, garantía de str
│   │   └── logging.py             # Trazas por pregunta (solo en modo local)
│   ├── ingest/
│   │   ├── extract.py             # PyMuPDF (paralelo), pdfplumber (tablas), Docling (E0)
│   │   ├── clean.py               # ftfy, guiones, encabezados/pies, referencias
│   │   ├── chunk.py               # FixedChunker (E0), SectionChunker padre-hijo (E1+)
│   │   └── enrich.py              # Título + sección + metadatos + dominio
│   ├── index/
│   │   ├── dense.py               # Embedder + FAISS Flat (IP sobre vectores normalizados)
│   │   ├── lexical.py             # BM25 (rank-bm25) con tokenización técnica
│   │   └── titles.py              # Índice de título + abstract por documento
│   ├── retrieval/
│   │   ├── query.py               # Glosario, erratas, paper nombrado, dominio, ¿numérica?
│   │   ├── search.py              # Buscadores + filtro doc → pasaje blando
│   │   ├── fusion.py              # NoFusion, RRF, OWA
│   │   └── rerank.py              # Cross-encoder + MMR
│   ├── verify/
│   │   ├── signals.py             # s1..s5
│   │   ├── threshold.py           # ThresholdDecider (E4-E5)
│   │   ├── qfcm.py                # QFCMDecider (E6)
│   │   └── actions.py             # Aceptar / refinar / reintentar / mejor evidencia
│   ├── context/
│   │   └── builder.py             # Selección, orden, vecinos, etiquetas [Doc: título, p. X]
│   └── generate/
│       ├── llm.py                 # Carga de OLMo, generate(), yes_no_prob()
│       ├── prompts.py             # Render de plantillas por dominio y tipo
│       └── pot.py                 # Program of Thoughts en subproceso aislado
│
├── submission/
│   └── main.py                    # Adaptador: answer() → dsqa.pipeline (plantilla del envío)
│
├── configs/                       # Una estrategia = un YAML
│   ├── base.yaml                  # Valores comunes (rutas, reloj, presupuestos)
│   ├── e0.yaml  e1.yaml  e2.yaml  e3.yaml  e4.yaml  e5.yaml  e6.yaml
│   └── ablations/                 # Leave-one-out: e6-sin-s5.yaml, e6-rrf.yaml, ...
│
├── resources/                     # Artefactos pequeños que viajan en el zip
│   ├── glossary_dones.json        # Siglas DONES → expansión (con fuente citada)
│   ├── domain_lexicon.json        # Términos por dominio (DONES / IA) para estimar pertenencias
│   ├── owa_params.json            # Pertenencias y pesos OWA calibrados
│   ├── qfcm_params.json           # φ, W, pertenencias de salida calibrados
│   └── prompts/                   # Plantillas (sistema, DONES, AI, juez s5, PoT)
│
├── models/                        # (git-ignored) Pesos auxiliares descargados offline
│   ├── embedder/                  # bge-base-en-v1.5 (fp16)
│   └── reranker/                  # bge-reranker-base (fp16)
│
├── offline/                       # Herramientas fuera de línea (no viajan en el zip)
│   ├── download_models.py         # Descarga y guarda en fp16 los modelos auxiliares
│   ├── fetch_public_pdfs.py       # PDFs públicos de los sitios fuente para el banco local
│   ├── build_glossary.py          # Construye glossary_dones.json
│   ├── build_synthetic_qa.py      # QA sintético desde PDFs públicos
│   └── calibrate_cmaes.py         # Calibración de OWA + q-FCM con validación cruzada
│
├── eval/                          # Evaluación local
│   ├── bench/
│   │   ├── sample_qa.json         # 25 preguntas oficiales de muestra
│   │   ├── synthetic_qa.json      # QA sintético (100-200)
│   │   └── gold_chunks.json       # Chunk(s) correcto(s) por pregunta, marcados a mano
│   ├── run_local.py               # Corre una config sobre el banco y guarda trazas
│   ├── retrieval_metrics.py       # Recall@k, MRR, tokens de contexto
│   ├── judge.py                   # Juez local binario (backend configurable)
│   ├── stats.py                   # McNemar, bootstrap, IC
│   └── report.py                  # Tabla de ablación E0-E6 y figuras para el paper
│
├── scripts/
│   ├── build_submission.py        # Arma dist/<config>-<fecha>.zip
│   └── check_submission.py        # Chequeo previo al envío (estructura, tamaño, imports, smoke)
│
├── infra/aws/                     # Ejecución remota en AWS (SPEC-031); sin secretos. Ver su README
│   ├── config.env                 # (git-ignored) Generado por dsqa-infra: región, bucket, plantillas
│   ├── config.env.example
│   ├── lib.sh                     # Funciones comunes
│   ├── push.sh  launch.sh  status.sh  stop.sh  pull.sh   # Ciclo de una sesión (laptop)
│   ├── ami.sh                     # Crea la AMI propia desde la instancia de preparación
│   ├── bootstrap.sh               # user data de la instancia
│   ├── watchdog.sh                # Apagado por inactividad
│   └── jobs/                      # Una lista de trabajos por sesión (prep.txt, smoke.txt, s01.txt, ...)
│
├── tests/
│   ├── unit/                      # Por módulo
│   ├── integration/               # Pipeline sin LLM (LLM simulado)
│   ├── smoke/                     # Punta a punta con LLM pequeño
│   └── fixtures/                  # PDFs mínimos, mini-corpus, preguntas de prueba
│
├── experiments/
│   ├── submissions.md             # Registro de envíos (fecha, config, hash, estado, score, tiempo)
│   ├── aws-sessions.md            # Registro de sesiones de AWS (horas, tipo, costo estimado)
│   └── runs/                      # (git-ignored) Trazas y resultados locales
│
└── docs/                          # Contexto, estrategia, presentación y esta documentación
    └── documentacion-tecnica/
        ├── ADR/                   # Una decisión por archivo
        └── spec/                  # Una funcionalidad por archivo
```

Cada módulo de `src/dsqa/` tiene su especificación en [spec/](spec/README.md) (columna "Módulo" del índice).

## 3.2 Estructura del zip de envío

`scripts/build_submission.py --config configs/e6.yaml` genera:

```
dsqa_e6_2026-11-22.zip         (≤ 950 MB descomprimido, control interno)
├── main.py                    # En la raíz (obligatorio)
├── config.yaml                # Config resuelta (base.yaml + e6.yaml), sin herencia
├── BUILD_INFO.json            # Commit, fecha, config, tamaños, versión del paquete
├── dsqa/                      # Copia de src/dsqa (sin __pycache__ ni tests)
├── resources/                 # Solo los recursos que pide la config
└── models/                    # Solo los modelos que pide la config
    ├── embedder/
    └── reranker/
```

`main.py` resuelve todas las rutas relativas a su propio archivo (`Path(__file__).parent`) y añade esa carpeta a `sys.path`. Nunca usa rutas absolutas ni la ruta del corpus fijada a mano.

### `submission/main.py` (forma esperada)

```python
import os, sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dsqa.runtime.clock import CLOCK          # arranca el reloj al importar
from dsqa.runtime.safety import safe_answer

def answer(question: str, corpus_dir: str, model_id: str) -> str:
    return safe_answer(question, corpus_dir, model_id, root=ROOT)  # siempre devuelve str
```

## 3.3 Configuración

La configuración se valida con `pydantic` al cargar; una clave desconocida o un valor fuera de rango es un error en la construcción del zip, no en Codabench.

```yaml
# configs/e6.yaml
extends: e5.yaml
strategy: E6

verify:
  enabled: true
  decider: qfcm                 # none | threshold | qfcm
  signals: [s1, s2, s3, s4, s5]
  judge_topk: 3                 # chunks que lee el juez OLMo (s5)
  max_retries: 1
  qfcm:
    params_file: resources/qfcm_params.json
    iterations: 10
```

Bloques de la config (claves de primer nivel):

| Bloque | Controla |
|---|---|
| `runtime` | Umbrales del reloj (`t_fast`, `t_emergency`), semilla, nivel de trazas |
| `ingest` | Extractor, pasos de limpieza, chunker, tamaños, solape, tablas |
| `index` | Embedder, dispositivo, tamaño de batch, BM25 (k1, b), índice de títulos |
| `retrieval` | Glosario, erratas, detección de paper, `top_k` por buscador, filtro doc → pasaje |
| `fusion` | `none` / `rrf` (k) / `owa` (archivo de parámetros) |
| `rerank` | Modelo, `top_n`, MMR (λ) |
| `verify` | Decisor, señales, reintentos, juez |
| `context` | Presupuesto de tokens, mín./máx. de chunks, umbral del reranker, vecinos |
| `generate` | Prompts, `max_new_tokens`, PoT activado, tiempo máx. de PoT |

## 3.4 Responsabilidades y dependencias entre módulos

Regla: las dependencias van **hacia abajo** en esta tabla; ningún módulo importa a uno que esté por encima.

| Capa | Módulos | Puede importar |
|---|---|---|
| Adaptador | `main.py` | `runtime` |
| Orquestación | `pipeline` | Todo lo de abajo |
| Etapas | `ingest`, `index`, `retrieval`, `verify`, `context`, `generate` | `types`, `runtime.config`, `runtime.clock`, librerías del entorno |
| Base | `types`, `runtime.config`, `runtime.clock` | Solo librería estándar y `pydantic` |

`offline/`, `eval/` y `scripts/` pueden importar `dsqa`, pero `dsqa` **nunca** importa nada de ellos.

## 3.5 Convenciones

| Tema | Convención |
|---|---|
| Lenguaje | Python ≥ 3.10 (confirmar la versión exacta de la imagen `ieee-cis-competition:latest`) |
| Estilo | `ruff` (lint + formato), líneas ≤ 100 |
| Tipos | Anotaciones en todas las funciones públicas; `mypy` en modo básico sobre `src/` |
| Nombres | Módulos y funciones en `snake_case`, clases en `PascalCase`; identificadores en inglés, documentación en español |
| Docstrings | Una línea con qué hace; añadir más solo si el porqué no es obvio |
| Imports pesados | `torch`, `transformers`, `FlagEmbedding`, etc. se importan dentro de las funciones de inicialización para que las pruebas unitarias sean rápidas |
| Aleatoriedad | Semilla única en la config; greedy en generación |
| Commits | Mensajes en imperativo; un cambio lógico por commit; las configs enviadas se etiquetan (`git tag sub-2026-11-22`) |
| Ramas | `main` siempre construible; trabajo en ramas `feat/...`, `exp/...` |
| Secretos | Ninguno en el repo (no se necesitan para el envío) |
