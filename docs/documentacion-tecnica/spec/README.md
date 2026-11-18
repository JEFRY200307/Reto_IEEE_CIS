# Especificaciones por funcionalidad (spec)

[← Documentación técnica](../README.md)

Cada archivo especifica **una sola funcionalidad** (atómica): qué hace, su interfaz, su comportamiento paso a paso, su configuración, cómo falla y cómo se prueba. Una spec debe poder implementarse y probarse **sin leer las demás**; solo se cruzan por los tipos de datos de [§2.6](../02-arquitectura.md#26-modelo-de-datos).

**Relación con el resto:** los requisitos dicen *qué* debe cumplirse ([RF](../04-requisitos-funcionales.md), [RNF](../05-requisitos-no-funcionales.md)); las specs dicen *cómo* lo hace cada pieza; los [ADR](../ADR/README.md) dicen *por qué*; los [criterios](../06-criterios-de-aceptacion.md) dicen *cuándo está terminada*.

## Índice

| Spec | Funcionalidad | Módulo | Estrategia | Prioridad |
|---|---|---|---|---|
| **Runtime** | | | | |
| [SPEC-001](SPEC-001-interfaz-answer.md) | Interfaz `answer()` | `main.py` | Todas | M |
| [SPEC-002](SPEC-002-reloj-global-y-modos.md) | Reloj global y modos | `runtime/clock.py` | E4 | M |
| [SPEC-003](SPEC-003-inicializacion-y-cache.md) | Inicialización perezosa, paralela y caché | `runtime/state.py` | Todas | M |
| [SPEC-004](SPEC-004-degradacion-y-respaldo.md) | Cadena de degradación N0-N4 | `runtime/safety.py` | E1 | M |
| **Etapa 1: preparación** | | | | |
| [SPEC-005](SPEC-005-extraccion-pdf.md) | Extracción de PDF | `ingest/extract.py` | Todas | M |
| [SPEC-006](SPEC-006-limpieza-de-texto.md) | Limpieza de texto | `ingest/clean.py` | E1 | S |
| [SPEC-007](SPEC-007-chunking-padre-hijo.md) | Chunking (fijo y padre-hijo) | `ingest/chunk.py` | E0/E1 | M |
| [SPEC-008](SPEC-008-enriquecimiento-y-dominio.md) | Enriquecimiento y dominio del documento | `ingest/enrich.py` | E1 | M |
| [SPEC-009](SPEC-009-indice-denso.md) | Índice denso | `index/dense.py` | Todas | M |
| [SPEC-010](SPEC-010-indice-bm25.md) | Índice BM25 | `index/lexical.py` | E2 | M |
| [SPEC-011](SPEC-011-indice-de-titulos.md) | Índice de títulos | `index/titles.py` | E3 | M |
| **Etapa 2: recuperación** | | | | |
| [SPEC-012](SPEC-012-analisis-de-consulta.md) | Análisis de la consulta | `retrieval/query.py` | E2-E4 | M |
| [SPEC-013](SPEC-013-busqueda-y-filtro-documento.md) | Búsqueda y filtro documento → pasaje | `retrieval/search.py` | E3 | M |
| [SPEC-014](SPEC-014-fusion-rrf.md) | Fusión RRF | `retrieval/fusion.py` | E2 | M |
| [SPEC-015](SPEC-015-fusion-owa.md) | Fusión difusa OWA (CI 1) | `retrieval/fusion.py` | E5 | M |
| [SPEC-016](SPEC-016-reranking-mmr.md) | Reranking y MMR | `retrieval/rerank.py` | E3 | M |
| **Etapa 3: verificación** | | | | |
| [SPEC-017](SPEC-017-senales-de-evidencia.md) | Señales $s_1$-$s_4$ | `verify/signals.py` | E4 | M |
| [SPEC-018](SPEC-018-juez-olmo-s5.md) | Juez OLMo $s_5$ | `verify/signals.py` | E6 | M |
| [SPEC-019](SPEC-019-decisor-umbrales.md) | Decisor por umbrales | `verify/threshold.py` | E4 | M |
| [SPEC-020](SPEC-020-decisor-qfcm.md) | Decisor q-FCM (CI 2) | `verify/qfcm.py` | E6 | M |
| [SPEC-021](SPEC-021-acciones-de-verificacion.md) | Acciones y reintento | `verify/actions.py` | E4 | M |
| **Etapas 4 y 5** | | | | |
| [SPEC-022](SPEC-022-construccion-de-contexto.md) | Construcción del contexto | `context/builder.py` | Todas | M |
| [SPEC-023](SPEC-023-generacion-olmo.md) | Generación con OLMo | `generate/llm.py`, `prompts.py` | Todas | M |
| [SPEC-024](SPEC-024-program-of-thoughts.md) | Program of Thoughts | `generate/pot.py` | E4 | M |
| **Transversal y fuera de línea** | | | | |
| [SPEC-025](SPEC-025-configuracion-y-estrategias.md) | Configuración y estrategias | `runtime/config.py`, `configs/` | Todas | M |
| [SPEC-026](SPEC-026-empaquetado-y-chequeo.md) | Empaquetado y chequeo del envío | `scripts/` | Todas | M |
| [SPEC-027](SPEC-027-glosario-dones.md) | Glosario de DONES | `offline/build_glossary.py` | E2 | M |
| [SPEC-028](SPEC-028-banco-local-y-qa-sintetico.md) | Banco local y QA sintético | `offline/`, `eval/bench/` | E1 | M |
| [SPEC-029](SPEC-029-calibracion-cmaes.md) | Calibración CMA-ES (CI 3) | `offline/calibrate_cmaes.py` | E6 | M |
| [SPEC-030](SPEC-030-evaluacion-local-y-estadistica.md) | Evaluación local y estadística | `eval/` | Todas | M |
| [SPEC-031](SPEC-031-ejecucion-remota-aws.md) | Ejecución remota en AWS | `infra/aws/` | Todas | M |

## Plantilla

```markdown
# SPEC-NNN: <funcionalidad>

**Módulo:** `ruta` · **Estrategia:** EN · **Prioridad:** M/S/C
**Requisitos:** RF-… · **Criterios:** CA-… · **ADR:** ADR-…

## Propósito
<Una o dos frases.>

## Interfaz
<Firma(s) en Python.>

## Comportamiento
1. …

## Reglas y casos borde
- …

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|

## Errores y respaldo
- …

## Pruebas
- …
```

**Regla de atomicidad:** si una spec necesita describir dos interfaces públicas sin relación, se divide en dos.
