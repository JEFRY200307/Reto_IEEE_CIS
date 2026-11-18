# 9. Estrategias implementadas (E0-E6)

[← Guía de despliegue](08-guia-de-despliegue.md) · [Índice](README.md)

Descripción de cada estrategia **tal como quedó implementada** en `configs/`, con su configuración exacta, lo que lleva su zip y su estado de validación. El diseño y la justificación teórica de cada una están en [`../investigacion-y-estrategia/estrategias/`](../investigacion-y-estrategia/README.md).

**Regla del proyecto:** las estrategias se envían a Codabench **tal como están diseñadas**, una por día, para medir cuánto sube el score cada salto. No se ajustan para perseguir un número.

## 9.1 Resumen

| Estrategia | Config | Qué agrega sobre la anterior | Modelos en el zip | Zip (sin comprimir) | Prueba real local | Score Codabench | Predicción |
|---|---|---|---|---|---|---|---|
| **E0** Base estándar | `configs/e0.yaml` | Baseline RAG del starter kit | MiniLM + Docling | — (no construido) | — | — | — |
| **E1** Preparación optimizada | `configs/e1.yaml` | PyMuPDF, limpieza, chunks padre-hijo, bge-base, top-5, prompts por dominio | bge-base | 210 MB | ✅ 3/3 en N0 | **46,67** (18 nov) | — |
| **E2** Recuperación híbrida | `configs/e2.yaml` | BM25 + denso con RRF, glosario DONES, erratas | bge-base | 210 MB | ✅ 3/3 en N0 | pendiente | ~50 (47-53) |
| **E3** Recuperación en dos fases | `configs/e3.yaml` | Filtro por paper nombrado, reranker + MMR, contexto por umbral con vecinos | bge-base + bge-reranker-base | 756 MB | ✅ 3/3 en N0 | pendiente | ~55 (51-59) |
| **E4** Verificación clásica | `configs/e4.yaml` | Señales s1-s4, umbrales, 1 reintento, Program of Thoughts | igual que E3 | ~756 MB | pendiente | pendiente | ~56 (52-60) |
| **E5** Fusión difusa (CI 1) | `configs/e5.yaml` | OWA en lugar de RRF | igual que E3 | ~756 MB | pendiente | pendiente | ~56 (52-60) |
| **E6** Verificación q-FCM (CI 2 y 3) | `configs/e6.yaml` | q-FCM + juez OLMo s5 en lugar de umbrales | igual que E3 | ~756 MB | pendiente | pendiente | ~57 (53-61) |

"N0" es el nivel completo del pipeline (sin respaldos). Las pruebas reales locales usan el zip descomprimido en una carpeta limpia, la red bloqueada, los modelos auxiliares reales y un OLMo pequeño (`allenai/OLMo-2-0425-1B-Instruct`, CPU) en lugar del de 32B. Validan que el envío **funciona**, no su precisión.

Cada estrategia hereda de la anterior (`extends`) y la prueba `tests/unit/test_config_clock.py` comprueba que cada salto cambia **solo** los bloques indicados.

## 9.2 Descripción de cada estrategia

### E0: Base estándar
Reproduce el baseline RAG del starter kit (`02_rag`) con el código de `dsqa`, para tener la referencia.

| Etapa | Configuración |
|---|---|
| Extracción | Docling a Markdown (`do_ocr=False`, `do_table_structure=False`), 4 procesos |
| Limpieza | Ninguna |
| Chunking | Fijo: ~800 caracteres con 150 de solape, cortando en párrafos |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` en CPU (`models/embedder-minilm`), sin instrucción de consulta |
| Búsqueda | Solo densa, top-50 |
| Contexto | Pasajes en orden hasta 10.000 tokens |
| Generación | Prompt genérico ("scientific expert"), hasta 2.048 tokens |

Necesita `offline/download_models.py --what minilm docling`. No se envía en el plan actual (E1 es la referencia medida).

### E1: Preparación optimizada
Mejora la preparación del corpus y la salida sin cambiar la lógica de búsqueda (sigue siendo solo densa).

| Etapa | Configuración |
|---|---|
| Extracción | PyMuPDF en paralelo (hasta 30 procesos), tablas (`find_tables`, respaldo pdfplumber) y pies de figura |
| Limpieza | ftfy, unión de palabras cortadas por guion, encabezados/pies repetidos (solo primeras/últimas líneas de página), corte de referencias |
| Chunking | Por sección, padre-hijo: hijos de 600 caracteres (se buscan), padres de 2.000 (se leen), solape 100; tablas y pies como chunks propios |
| Enriquecimiento | Título del documento + sección antepuestos a cada hijo; pertenencia difusa de dominio (DONES / IA) |
| Embeddings | `BAAI/bge-base-en-v1.5` (fp16 en GPU) con instrucción de consulta BGE |
| Búsqueda | Solo densa, top-50 (FAISS Flat) |
| Contexto | Top-5 pasajes (padres), máximo 4.000 tokens, etiquetas `[Doc: título, p. N]` |
| Generación | Prompt por dominio (ingeniero de IFMIF-DONES / investigador de IA): dato clave primero, justificación breve, unidades, nunca negarse; hasta 300 tokens, greedy |

### E2: Recuperación híbrida
Cambia `retrieval` y `fusion`.

| Etapa | Configuración |
|---|---|
| Búsqueda | **BM25** (implementación propia con matrices dispersas; tokenización que conserva `Be-7`, `RQ-Kmeans`, `ICS`) + **denso**, top-50 cada uno |
| Consulta | Expansión de siglas con `resources/glossary_dones.json` (24 siglas) y corrección de erratas contra el vocabulario del corpus (umbral 90) |
| Fusión | **RRF** con k = 60, top-50 fusionados |

### E3: Recuperación en dos fases
Cambia `index`, `retrieval`, `rerank` y `context`.

| Etapa | Configuración |
|---|---|
| Índice de títulos | Título + abstract por documento; nombres propios (WinStat, ZeroDiff, REVEL…) con detección de homónimos |
| Filtro documento → pasaje | Si la confianza en el paper nombrado es ≥ 0,7, se busca dentro de ese documento (completando con búsqueda global si hay menos de 5 resultados) |
| Reranker | `BAAI/bge-reranker-base` (fp16 en GPU) sobre los 50 fusionados; se quedan 20 |
| Diversidad | MMR con λ = 0,7 y descarte de casi-duplicados (similitud ≥ 0,95) |
| Contexto | Por umbral: pasajes con puntaje de reranker ≥ 0,3, entre 3 y 8, más vecinos ±1; máximo 6.000 tokens |

### E4: Verificación clásica
Cambia `verify` y `generate`.

| Etapa | Configuración |
|---|---|
| Señales | s1 puntaje del top-1 del reranker, s2 brecha top-1/top-2, s3 acuerdo BM25-denso (top-10), s4 cobertura de términos clave (top-3) |
| Decisor | Umbrales fijos: correcta si s1 ≥ 0,7 y s4 ≥ 0,5; incorrecta si s1 < 0,3; ambigua en otro caso |
| Acciones | Ambigua → +2 pasajes y vecinos; incorrecta → reformulación (términos clave + glosario) sin filtro por documento y **1 reintento**; se conserva la mejor evidencia; nunca abstenerse |
| Program of Thoughts | En preguntas numéricas y modo normal: OLMo escribe Python, se valida con `ast` y se ejecuta aislado (solo `math`, 5 s, sin red ni archivos) |

### E5: Fusión difusa OWA (CI 1)
Cambia solo `fusion`. Puntajes de cada buscador → normalización min-max → pertenencia sigmoide μ = σ(a(ŝ − c)) con a = 8, c = 0,5 → agregación OWA con pesos w = (0,4; 0,6) sobre las pertenencias ordenadas (sesgo hacia el acuerdo). Parámetros en `resources/owa_params.json` (valores de experto; `offline/calibrate_cmaes.py` los calibra).

### E6: Verificación con q-FCM (CI 2 y 3)
Cambia solo `verify`.
- **Señal nueva s5:** juez OLMo con una sola pasada sin generar, P(Yes) / (P(Yes) + P(No)) sobre los 3 mejores pasajes.
- **Decisor q-FCM:** conceptos C1-C5 (señales) y C6 (confianza); regla A(t+1) = φ·f(A(t)W − h) + (1 − φ)·A(0) con φ = 0,7, λ = 3, h = 1,1, 10 iteraciones; pesos de experto C1→C6 0,65, C2→C6 0,30, C3→C6 0,30, C4→C6 0,45, C5→C6 0,55 (en `resources/qfcm_params.json`, dentro de rangos de experto); confianza = A6/φ mapeada a pertenencias trapezoidales correcta / ambigua / incorrecta.
- **Calibración (CI 3):** `offline/calibrate_cmaes.py` ajusta OWA y q-FCM con CMA-ES, validación cruzada y pesos acotados.

## 9.3 Variantes y ablaciones

| Config | Uso |
|---|---|
| `configs/ablations/e6-sin-s5.yaml`, `e6-rrf.yaml`, `e6-sin-reranker.yaml`, `e6-sin-verificacion.yaml`, `e6-sin-pot.yaml`, `e6-sin-filtro-doc.yaml` | Leave-one-out: E6 quitando un componente |
| `configs/variants/e5-calibrado.yaml`, `e6-calibrado.yaml` | E5/E6 con parámetros calibrados por CMA-ES (`resources/calibrated/`) |
| `configs/variants/e4-4bit-g6e.yaml` | Plan B con OLMo en 4 bits (solo pruebas funcionales) |

## 9.4 Validación local de la recuperación

`eval/bench/gold_chunks.json` marca el pasaje que responde 14 de las 25 preguntas de muestra dentro de los 27 PDFs públicos de `data/public_pdfs/`. Las otras 11 dependen de documentos que no están en el banco local (WinStat, ThinkMore, *Fairness by Brute Force*, ONB-MACF…) o de datos en figuras. Con eso, `eval/run_local.py --retrieval-only` mide recall@k y MRR por estrategia sin OLMo; los resultados quedan en `experiments/runs/recall-local/`.

### Resultados (18 nov 2026)

Medición sin OLMo, con el bge y el reranker reales en CPU, sobre las 14 preguntas con gold (6 DONES, 8 IA) y las estrategias **sin modificar**:

```bash
python eval/run_local.py --configs configs/e1.yaml configs/e2.yaml configs/e3.yaml --corpus data/public_pdfs --retrieval-only --out experiments/runs/recall-local --ids 2 3 5 6 7 8 11 14 16 20 22 23 24 25
```

| Estrategia | Recall@1 | **Recall@5** | Recall@20 | MRR | DONES r@5 | IA r@5 |
|---|---|---|---|---|---|---|
| E1 | 14 % | **29 %** | 50 % | 0,21 | 33 % | 25 % |
| E2 | 21 % | **36 %** | 57 % | 0,27 | 50 % | 25 % |
| E3 | 7 % | **29 %** | 43 % | 0,16 | 33 % | 25 % |

Puesto del pasaje correcto en la lista final de cada estrategia ("—" = fuera de la lista: 50 candidatos en E1 y E2, 20 en E3 tras el reranker):

| Pregunta | E1 | E2 | E3 |
|---|---|---|---|
| #3 Be-7 (constante de desintegración) | 1 | 1 | 4 |
| #6 Caudal del intercambiador | 2 | 1 | 1 |
| #7 Trampa de nitrógeno | 17 | 4 | — |
| #8 Bypass del ICS | 13 | 10 | 14 |
| #22 SimCLR | — | 14 | — |
| #23 (α,f)-Byzantine | 5 | 4 | 8 |
| #24 GPAIS | 1 | 1 | 4 |
| #25 Mamba | 6 | 6 | 2 |
| #2, #5, #11, #14, #16, #20 | — | — | — |

**Lectura:**
- **E2 mejora a E1**, sobre todo en DONES (recall@5 de 33 % a 50 %), como se esperaba de BM25 con siglas y valores exactos.
- **E3 no mejora a E2** en esta muestra: el reranker de propósito general reordena peor en varias preguntas (#3, #7, #24) y mejora otras (#25). E3 además deja solo 20 candidatos tras el reranker y el filtro de duplicados.
- **6 de las 14 preguntas no encuentran su pasaje en ninguna estrategia.** Hallazgo: en PDFs a dos columnas, PyMuPDF (`sort=True`) a veces intercala líneas de ambas columnas, lo que ensucia los fragmentos; afecta por igual a E1-E6.

**Límites:** con 14 preguntas cada una vale ~7 puntos (E2 vs. E3 es una sola pregunta de diferencia); el banco local es una aproximación del corpus privado de Codabench. Estas cifras sirven para **explicar** los scores de Codabench, no para reemplazarlos.

## 9.5 Registro de envíos

Ver [`../../experiments/submissions.md`](../../experiments/submissions.md).
