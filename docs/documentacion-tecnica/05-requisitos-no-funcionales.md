# 5. Requisitos no funcionales (RNF)

[← Requisitos funcionales](04-requisitos-funcionales.md) · [Índice](README.md) · Siguiente: [Criterios de aceptación →](06-criterios-de-aceptacion.md)

**Tipo de valor:** *límite* = viene de las reglas, no se negocia · *objetivo* = meta interna ajustable con mediciones.

## 5.1 Rendimiento (RD)

| ID | Requisito | Valor | Tipo |
|---|---|---|---|
| RNF-RD-01 | Tiempo total de reloj en el leaderboard público (carga + indexado + todas las preguntas) | < 60 min | *límite* |
| RNF-RD-02 | Tiempo total en el leaderboard público | ≤ 45 min | *objetivo* |
| RNF-RD-03 | Tiempo total en el leaderboard privado (~100 preguntas) | ≤ 90 min (límite 120 min, blando) | *objetivo* |
| RNF-RD-04 | Inicialización completa (OLMo + ingesta + índices) | ≤ 14 min | *objetivo* |
| RNF-RD-05 | Tiempo medio por pregunta en modo normal | ≤ 35 s | *objetivo* |
| RNF-RD-06 | Tiempo máximo por pregunta en modo normal (p95) | ≤ 60 s | *objetivo* |
| RNF-RD-07 | Recuperación completa (consulta + búsqueda + fusión + rerank) por pregunta | ≤ 3 s | *objetivo* |
| RNF-RD-08 | Costo de la fusión OWA y del q-FCM por pregunta | ≤ 50 ms | *objetivo* |
| RNF-RD-09 | Tiempo máximo de ejecución de un programa PoT | ≤ 10 s | *objetivo* |

## 5.2 Recursos (RC)

| ID | Requisito | Valor | Tipo |
|---|---|---|---|
| RNF-RC-01 | Tamaño descomprimido del zip | ≤ 1 GB | *límite* |
| RNF-RC-02 | Tamaño descomprimido del zip (control interno) | ≤ 950 MB | *objetivo* |
| RNF-RC-03 | Pico de memoria de GPU | ≤ 76 GB (de 80) | *objetivo* |
| RNF-RC-04 | Pico de memoria RAM | ≤ 100 GB (de 128) | *objetivo* |
| RNF-RC-05 | Tokens de contexto por pregunta (desde E1) | ≤ 6 000 | *objetivo* |
| RNF-RC-06 | GPUs usadas | 1 | *límite* |

## 5.3 Confiabilidad (CO)

| ID | Requisito | Valor |
|---|---|---|
| RNF-CO-01 | Envíos *Failed* por errores del código | 0 |
| RNF-CO-02 | Preguntas en las que `answer()` lanza una excepción o devuelve algo que no es `str` | 0 |
| RNF-CO-03 | Un fallo en una pregunta no debe afectar a las siguientes (estado del proceso intacto) | Siempre |
| RNF-CO-04 | La ingesta debe completarse aunque haya PDFs corruptos, cifrados, vacíos o enormes | Siempre |
| RNF-CO-05 | Cobertura del corpus: documentos con texto extraído / documentos PDF | ≥ 98 % |
| RNF-CO-06 | El sistema funciona aunque falte un recurso opcional (glosario, parámetros): usa valores por defecto y lo registra | Siempre |

## 5.4 Portabilidad y compatibilidad (PO)

| ID | Requisito |
|---|---|
| RNF-PO-01 | El código en línea solo importa librerías de `requirements-participant.txt` en sus versiones exactas, más la librería estándar. |
| RNF-PO-02 | El sistema no hace ninguna llamada de red durante la evaluación. |
| RNF-PO-03 | No depende de vLLM, flash-attn, `faiss-gpu`, `cv2`/`libGL` ni de binarios externos. |
| RNF-PO-04 | El mismo código corre en laptop (CPU, sin LLM o con LLM simulado), Colab/Kaggle (LLM pequeño) y Codabench (OLMo) cambiando solo `model_id`, `corpus_dir` y la config. |
| RNF-PO-05 | Las rutas se resuelven relativas a `main.py`; funciona en Linux con cualquier directorio de trabajo. |

## 5.5 Reproducibilidad (RP)

| ID | Requisito |
|---|---|
| RNF-RP-01 | Con la misma config, el mismo corpus y el mismo hardware, las respuestas son idénticas (greedy, semillas fijas, orden estable de archivos y candidatos). |
| RNF-RP-02 | Cada envío se puede reconstruir desde un commit etiquetado y su config (`BUILD_INFO.json`). |
| RNF-RP-03 | Cada experimento local guarda config resuelta, commit, banco usado y resultados. |
| RNF-RP-04 | La calibración CMA-ES fija su semilla y guarda el historial de evaluaciones. |

## 5.6 Seguridad e integridad (SE)

| ID | Requisito |
|---|---|
| RNF-SE-01 | El código PoT se ejecuta en un subproceso aislado: sin red, sin escritura ni lectura de archivos, sin `import` fuera de una lista permitida (`math`), con límite de tiempo y de memoria. |
| RNF-SE-02 | El contenido de los PDFs se trata como datos: nunca se ejecuta ni se interpreta como instrucciones del sistema. |
| RNF-SE-03 | El repositorio no contiene credenciales ni datos personales. |
| RNF-SE-04 | Los modelos auxiliares se descargan solo de repositorios oficiales de Hugging Face y se cargan con `safetensors`. |

## 5.7 Mantenibilidad y modularidad (MA)

| ID | Requisito |
|---|---|
| RNF-MA-01 | Cada componente intercambiable (extractor, chunker, buscador, fusión, reranker, decisor) implementa una interfaz común; agregar una variante no exige cambiar el orquestador. |
| RNF-MA-02 | Las dependencias entre capas siguen §3.4; no hay imports circulares. |
| RNF-MA-03 | Ningún módulo de `src/dsqa` supera ~400 líneas; ninguna función ~60 líneas. |
| RNF-MA-04 | Cobertura de pruebas unitarias en `src/dsqa` (sin `generate/llm.py`) ≥ 70 %. |
| RNF-MA-05 | `ruff` y `mypy` pasan sin errores en `src/`. |

## 5.8 Interpretabilidad y observabilidad (IN)

| ID | Requisito |
|---|---|
| RNF-IN-01 | Cada veredicto de verificación se puede explicar con sus señales, las activaciones del q-FCM y la acción tomada. |
| RNF-IN-02 | Los pesos del q-FCM y de OWA son legibles (JSON) y se pueden dibujar como grafo para el paper. |
| RNF-IN-03 | La traza local registra el tiempo de cada etapa para descomponer el tiempo total. |

## 5.9 Calidad de las respuestas (QR)

| ID | Requisito | Valor |
|---|---|---|
| RNF-QR-01 | La primera oración de la respuesta contiene el dato o la conclusión clave. | Siempre (verificado por muestreo) |
| RNF-QR-02 | Longitud de la respuesta | ≤ ~300 tokens; *objetivo* 60-200 |
| RNF-QR-03 | Las respuestas numéricas incluyen unidades. | Siempre |
| RNF-QR-04 | La respuesta está en inglés (idioma de las preguntas y referencias). | Siempre |
| RNF-QR-05 | Sin frases de abstención ("I don't know", "the context does not mention") como respuesta final. | 0 casos |

## 5.10 Cumplimiento (CU)

| ID | Requisito |
|---|---|
| RNF-CU-01 | Se respetan todas las reglas del reto ([03](../contexto-inicial/03-reglas-y-bases-oficiales.md)): modelo fijo, 1 envío por día, plazos en UTC. |
| RNF-CU-02 | Los datos externos usados (glosario, PDFs públicos, QA sintético, modelos auxiliares) son públicos, se registran con su fuente y se citan en la metodología y el paper. |
| RNF-CU-03 | Ningún prompt, respuesta o componente intenta manipular, atacar o hacer jailbreak al LLM juez. |
| RNF-CU-04 | El envío es obra original del equipo; el código de terceros reutilizado (p. ej. el kit, licencia MIT) se reconoce. |
| RNF-CU-05 | Cada envío lleva el borrador de la metodología exigido por Codabench. |

## 5.11 Costo de la infraestructura (CS)

Ver [ADR-14](ADR/ADR-14-computo-aws-p5-spot.md) a [ADR-17](ADR/ADR-17-control-de-costos-aws.md) y la [guía de despliegue](08-guia-de-despliegue.md).

| ID | Requisito | Valor | Tipo |
|---|---|---|---|
| RNF-CS-01 | Gasto total en AWS hasta el 30 nov 2026 | ≤ USD 150 (presupuesto con alertas); *objetivo* ≤ USD 70 | *objetivo* |
| RNF-CS-02 | Duración máxima de una instancia GPU | ≤ 3 h por sesión (ampliable a mano hasta 4 h) | *objetivo* |
| RNF-CS-03 | Tiempo máximo de GPU inactiva antes de terminar la instancia | ≤ 25 min | *objetivo* |
| RNF-CS-04 | Instancias del proyecto encendidas fuera de una sesión | 0 | Siempre |
| RNF-CS-05 | Lo que no necesita OLMo se ejecuta en la laptop | Ingesta, índices, fusión, q-FCM, CMA-ES, recall@5, pruebas | Siempre |
