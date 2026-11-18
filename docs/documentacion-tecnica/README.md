# Documentación técnica del sistema — IEEE CIS DSQA Challenge 2026

**Sistema:** `dsqa` — sistema de preguntas y respuestas con recuperación (RAG) e Inteligencia Computacional para IFMIF-DONES y papers de IA.
**Versión del documento:** 1.0 · **Fecha:** 29 oct 2026
**Autores:** Cristhian J. Maylle Briceño · Jefferson D. Flores Montenegro

Esta carpeta define **qué** se construye, **cómo** se organiza y **cuándo** se considera terminado. Se apoya en:

- [`../contexto-inicial/`](../contexto-inicial/README.md): reglas y datos oficiales del reto (fuente de las restricciones).
- [`../investigacion-y-estrategia/`](../investigacion-y-estrategia/README.md): estrategias E0 a E6 y referencias (fuente de las decisiones de diseño).

Si algo de esta carpeta contradice las reglas oficiales, **mandan las reglas oficiales**.

## Resumen en 30 segundos

- **Qué es:** un paquete Python que se empaqueta en un `.zip` con `main.py` y expone `answer(question, corpus_dir, model_id) -> str`.
- **Cómo funciona:** pipeline de 5 etapas (preparación del corpus, recuperación, verificación de la evidencia, contexto, generación) con un control de recursos transversal.
- **Estrategias:** cada estrategia E0 a E6 es un **archivo de configuración**, no una rama de código. El mismo código ejecuta todas.
- **Inteligencia Computacional:** fusión difusa OWA (E5), verificación con q-FCM (E6) y calibración con CMA-ES (E6).
- **Límites duros:** 1 h en el leaderboard público, 1 GB de envío, sin internet, solo las librerías preinstaladas, `answer()` siempre devuelve `str`.
- **Dónde se corre OLMo para desarrollar:** AWS `p5.4xlarge` (la misma H100 que Codabench) en spot, con instancias que se terminan solas. Gasto esperado de ~USD 45-70 hasta el 30 nov.

## Índice

| # | Archivo | Contenido |
|---|---------|-----------|
| 1 | [01-objetivo-y-alcance.md](01-objetivo-y-alcance.md) | Objetivo general y específicos, alcance, fuera de alcance, supuestos, restricciones, partes interesadas |
| 2 | [02-arquitectura.md](02-arquitectura.md) | Vistas de la arquitectura, componentes, flujo de datos, ciclo de vida, modelo de datos, presupuestos de tiempo y espacio, decisiones (ADR) |
| 3 | [03-estructura-del-proyecto.md](03-estructura-del-proyecto.md) | Árbol del repositorio, estructura del zip, responsabilidades por módulo, configuración, convenciones |
| 4 | [04-requisitos-funcionales.md](04-requisitos-funcionales.md) | RF agrupados por módulo, con prioridad y estrategia en la que entran |
| 5 | [05-requisitos-no-funcionales.md](05-requisitos-no-funcionales.md) | RNF de rendimiento, recursos, confiabilidad, portabilidad, reproducibilidad, seguridad, mantenibilidad, cumplimiento |
| 6 | [06-criterios-de-aceptacion.md](06-criterios-de-aceptacion.md) | Criterios verificables por requisito, por estrategia y por envío; matriz de trazabilidad |
| 7 | [07-calidad-y-pruebas.md](07-calidad-y-pruebas.md) | Modelo de calidad, estrategia de pruebas, métricas, protocolo experimental, puertas de calidad, gestión de riesgos |
| 8 | [08-guia-de-despliegue.md](08-guia-de-despliegue.md) | Montar AWS al menor costo (p5.4xlarge spot, S3, sesiones desechables), ciclo de una sesión, envío a Codabench, plan de sesiones, solución de problemas |
| — | [ADR/](ADR/README.md) | 18 decisiones de arquitectura, una por archivo |
| — | [spec/](spec/README.md) | 31 especificaciones atómicas, una por funcionalidad |

### Cómo se relacionan

```
Requisitos (04, 05)  ──qué──▶  Specs (spec/)  ──cómo──▶  Código (src/dsqa)
        ▲                          ▲
        └── Objetivos (01)         └── ADR (por qué)        Criterios (06) ──cuándo está terminado
```

## Glosario

| Término | Significado en este proyecto |
|---|---|
| **Corpus** | PDFs disponibles en `corpus_dir` durante la evaluación. Incluye documentos reales y distractores. No se ve antes. |
| **Chunk** | Fragmento de texto indexado. Puede ser hijo (pequeño, para buscar) o padre (más grande, para entregar al LLM). |
| **Buscador** | Método de recuperación de candidatos: BM25 (léxico) o denso (embeddings). |
| **Fusión** | Combinar las listas de varios buscadores en una: RRF (E2-E4) u OWA (E5-E6). |
| **Reranker** | Cross-encoder que relee pregunta + pasaje y reordena los candidatos. |
| **Verificación** | Juzgar si la evidencia recuperada permite responder y decidir una acción (aceptar, refinar, reintentar). |
| **Señales** | Valores numéricos que describen la calidad de la evidencia ($s_1$ a $s_5$). |
| **q-FCM** | Mapa cognitivo difuso con regla de razonamiento cuasi-no lineal. Decisor de la verificación en E6. |
| **PoT** | *Program of Thoughts*: el LLM escribe código Python que se ejecuta para resolver cálculos. |
| **Modo rápido** | Modo degradado que se activa cuando el reloj global se acerca al límite. |
| **Banco local** | Conjunto de evaluación propio: 25 preguntas de muestra + QA sintético + chunks correctos marcados. |
| **Estrategia** | Configuración completa del pipeline (E0 a E6), definida en un YAML. |
| **Envío** | Un `.zip` subido a Codabench. Máximo 1 por día. |

## Convenciones de este documento

- **Identificadores:** `RF-XX-NN` (funcional), `RNF-XX-NN` (no funcional), `CA-...` (criterio de aceptación), `ADR-NN` (decisión de arquitectura).
- **Prioridad (MoSCoW):** **M** = obligatorio, **S** = debería, **C** = podría, **W** = no en esta versión.
- **Estrategia:** columna que indica desde qué estrategia se exige el requisito (E0 a E6, o "Todas").
- Los valores numéricos marcados como *objetivo* son metas iniciales que se ajustan con mediciones; los marcados como *límite* vienen de las reglas y no se negocian.
