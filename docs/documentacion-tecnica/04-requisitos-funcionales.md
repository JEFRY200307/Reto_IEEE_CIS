# 4. Requisitos funcionales (RF)

[← Estructura](03-estructura-del-proyecto.md) · [Índice](README.md) · Siguiente: [Requisitos no funcionales →](05-requisitos-no-funcionales.md)

**Prioridad:** M = obligatorio · S = debería · C = podría · W = no en esta versión.
**Estrategia:** desde cuál se exige el requisito. "Todas" = E0 a E6.
Los criterios de aceptación de cada RF están en [06-criterios-de-aceptacion.md](06-criterios-de-aceptacion.md); el detalle de cómo se implementa cada funcionalidad, en las [specs](spec/README.md).

## 4.1 Interfaz con Codabench (IF)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-IF-01 | El envío debe exponer en `main.py`, en la raíz del zip, la función `answer(question: str, corpus_dir: str, model_id: str) -> str`. | M | Todas |
| RF-IF-02 | `answer()` debe devolver siempre un objeto de tipo `str`, no vacío, para cualquier entrada, incluso si ocurre una excepción interna. | M | Todas |
| RF-IF-03 | El sistema debe leer los documentos solo desde `corpus_dir` y cargar el modelo solo a partir de `model_id`, sin rutas fijas. | M | Todas |
| RF-IF-04 | El sistema debe soportar llamadas sucesivas a `answer()` en el mismo proceso, reutilizando modelo, índices y modelos auxiliares. | M | Todas |
| RF-IF-05 | El sistema debe aceptar preguntas con erratas, mayúsculas irregulares, LaTeX o Unicode sin fallar. | M | Todas |

## 4.2 Control de ejecución y recursos (RT)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-RT-01 | El sistema debe iniciar un reloj global al importarse `main.py` y exponer el tiempo transcurrido a todas las etapas. | M | E1 |
| RF-RT-02 | El sistema debe inicializar modelo e índices de forma perezosa en la primera llamada y cachearlos para las siguientes. | M | Todas |
| RF-RT-03 | El sistema debe cargar OLMo en paralelo con la ingesta del corpus. | S | E1 |
| RF-RT-04 | El sistema debe pasar a **modo rápido** al superar `t_fast` y a **modo emergencia** al superar `t_emergency` (configurables), con los cambios definidos en la arquitectura (§2.7). | M | E4 |
| RF-RT-05 | El sistema debe aplicar la cadena de degradación N0-N4 (§2.10) ante errores, sin propagar excepciones a Codabench. | M | E1 |
| RF-RT-06 | Ante un error de memoria de GPU, el sistema debe liberar caché y reintentar la pregunta con un contexto menor. | S | E1 |
| RF-RT-07 | El sistema debe forzar el modo sin red (`HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`) antes de cargar cualquier modelo. | M | Todas |
| RF-RT-08 | En modo local, el sistema debe escribir una traza por pregunta (tiempos por etapa, candidatos, señales, veredictos, tokens de contexto, respuesta, errores). En Codabench las trazas se desactivan o van a `stderr`. | M | E1 |

## 4.3 Ingesta del corpus (IN)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-IN-01 | El sistema debe recorrer `corpus_dir` de forma recursiva y procesar todos los archivos `.pdf`, ignorando los demás. | M | Todas |
| RF-IN-02 | El sistema debe extraer el texto por página con PyMuPDF usando varios procesos en paralelo. | M | E1 |
| RF-IN-03 | El sistema debe extraer las tablas con pdfplumber solo en las páginas donde se detecten tablas, y representarlas como texto tabular. | S | E1 |
| RF-IN-04 | El sistema debe ofrecer el extractor Docling con la configuración del kit (`do_ocr=False`, `do_table_structure=False`) para reproducir E0. | M | E0 |
| RF-IN-05 | Un PDF corrupto, cifrado o sin texto no debe detener la ingesta: se omite y se registra. Un PDF que exceda un tiempo máximo de extracción se abandona. | M | Todas |
| RF-IN-06 | El sistema debe limpiar el texto: reparar codificación (ftfy), unir palabras cortadas por guion, quitar encabezados y pies repetidos y descartar la sección de referencias bibliográficas. | S | E1 |
| RF-IN-07 | El sistema debe extraer por documento: título, abstract (si existe) y secciones detectadas. | M | E1 |
| RF-IN-08 | El sistema debe conservar los pies de figura y de tabla como chunks de tipo `caption`. | S | E1 |
| RF-IN-09 | El sistema debe asignar a cada documento una pertenencia de dominio (DONES / AI / desconocido) a partir de su texto. | S | E1 |

## 4.4 Chunking y enriquecimiento (IN)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-IN-10 | El sistema debe ofrecer chunking fijo de ~800 caracteres con 150 de solape cortando en párrafos (E0). | M | E0 |
| RF-IN-11 | El sistema debe ofrecer chunking por sección con estructura padre-hijo: se busca con el chunk hijo y se entrega el padre. | M | E1 |
| RF-IN-12 | Las tablas deben indexarse como chunks independientes con su encabezado. | S | E1 |
| RF-IN-13 | Si no se detectan secciones, el sistema debe usar chunking recursivo por párrafo como respaldo. | M | E1 |
| RF-IN-14 | Cada chunk debe llevar antepuestos el título del documento y la sección, y guardar los metadatos `doc_id`, página, sección, tipo y dominio. | M | E1 |

## 4.5 Índices (IX)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-IX-01 | El sistema debe construir un índice denso con el embedder configurado y vectores normalizados (MiniLM en CPU para E0; bge-base en GPU en batch desde E1). | M | Todas |
| RF-IX-02 | El índice denso debe usar FAISS Flat (búsqueda exacta por producto interno). | M | E1 |
| RF-IX-03 | El sistema debe construir un índice BM25 con una tokenización que conserve siglas, isótopos, números con unidades y nombres con guiones (p. ej. `Be-7`, `RQ-Kmeans`, `ICS`). | M | E2 |
| RF-IX-04 | El sistema debe construir un índice de documentos con título y abstract. | M | E3 |
| RF-IX-05 | Los embeddings del corpus deben calcularse antes de que OLMo ocupe la GPU o de forma que ambos quepan; la memoria del embedder se libera si no se usa para consultas. | S | E1 |

## 4.6 Procesamiento de la consulta (CO)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-CO-01 | El sistema debe expandir las siglas de la pregunta usando el glosario de DONES. | M | E2 |
| RF-CO-02 | El sistema debe corregir erratas comparando con el vocabulario del corpus (`rapidfuzz`), solo en palabras ausentes del vocabulario y con un umbral de similitud alto. | S | E2 |
| RF-CO-03 | El sistema debe detectar si la pregunta nombra un paper o método y estimar la confianza de esa coincidencia con el índice de títulos. | M | E3 |
| RF-CO-04 | El sistema debe estimar la pertenencia de la pregunta a cada dominio. | S | E2 |
| RF-CO-05 | El sistema debe marcar si la pregunta es numérica (pide una cantidad, unidad o cálculo). | M | E4 |
| RF-CO-06 | El sistema debe extraer los términos clave de la pregunta (para la cobertura $s_4$ y BM25). | M | E4 |
| RF-CO-07 | El sistema debe generar consultas reformuladas para el reintento (glosario + variantes). | M | E4 |

## 4.7 Búsqueda, fusión y reranking (RE, FU, RK)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-RE-01 | El sistema debe recuperar los `top_k` candidatos (por defecto 50) de cada buscador activo. | M | Todas |
| RF-RE-02 | El sistema debe aplicar el filtro blando documento → pasaje: si la confianza del paper nombrado supera el umbral, buscar dentro de ese documento; si no, buscar en todo el corpus. | M | E3 |
| RF-FU-01 | El sistema debe fusionar las listas con RRF ($k = 60$). | M | E2 |
| RF-FU-02 | El sistema debe fusionar las listas con OWA: normalizar cada puntaje, convertirlo en pertenencia con una sigmoide $(a_r, c_r)$ y agregar con pesos de posición $w$ que sumen 1. | M | E5 |
| RF-FU-03 | Los parámetros de OWA deben leerse de `resources/owa_params.json`. | M | E5 |
| RF-FU-04 | Pesos OWA dinámicos según dominio y tipo de pregunta (o integral de Choquet). | C | — |
| RF-RK-01 | El sistema debe reordenar los candidatos fusionados con el cross-encoder configurado. | M | E3 |
| RF-RK-02 | El sistema debe aplicar MMR para reducir pasajes redundantes. | S | E3 |

## 4.8 Verificación de la evidencia (VE)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-VE-01 | El sistema debe calcular las señales $s_1$ (puntaje del reranker top-1), $s_2$ (brecha top-1 − top-2), $s_3$ (solape de los top-10 de BM25 y denso) y $s_4$ (cobertura de términos clave), normalizadas en $[0, 1]$. | M | E4 |
| RF-VE-02 | El sistema debe calcular $s_5 = P(\text{Sí}) / (P(\text{Sí}) + P(\text{No}))$ con una sola pasada de OLMo sobre la pregunta y el top-3, sin generar texto. | M | E6 |
| RF-VE-03 | El sistema debe ofrecer un decisor por umbrales fijos que clasifique la evidencia en correcta / ambigua / incorrecta. | M | E4 |
| RF-VE-04 | El sistema debe ofrecer un decisor q-FCM con 5 conceptos de entrada y 1 de salida, regla $A^{(t+1)} = \varphi f(A^{(t)}W) + (1-\varphi)A^{(0)}$, ~10 iteraciones, y mapeo de la salida a pertenencias difusas correcta / ambigua / incorrecta. | M | E6 |
| RF-VE-05 | Los parámetros del q-FCM ($\varphi$, $W$, pertenencias de salida) deben leerse de `resources/qfcm_params.json`. | M | E6 |
| RF-VE-06 | Acciones: **correcta** → contexto; **ambigua** → añadir vecinos, subir k y filtrar oraciones irrelevantes; **incorrecta** → reformular, quitar el filtro por documento y reintentar una vez; si sigue incorrecta → usar la mejor evidencia de todos los intentos. | M | E4 |
| RF-VE-07 | El sistema nunca debe abstenerse ni responder "no lo sé" como respuesta final. | M | Todas |
| RF-VE-08 | El sistema debe registrar en la traza las señales, las pertenencias y la acción tomada. | M | E4 |
| RF-VE-09 | Pesos del q-FCM por intervalos con calibración restringida. | C | — |

## 4.9 Construcción del contexto (CX)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-CX-01 | E0: concatenar los mejores fragmentos hasta ~10 000 tokens. | M | E0 |
| RF-CX-02 | E1-E2: top-5 chunks con un máximo de 4 000 tokens, el más relevante primero. | M | E1 |
| RF-CX-03 | E3+: seleccionar entre 3 y 8 chunks según un umbral sobre el puntaje del reranker, y añadir los chunks vecinos ±1 dentro del presupuesto. | M | E3 |
| RF-CX-04 | Cada pasaje debe ir etiquetado como `[Doc: <título>, p. <página>]`. | M | E1 |
| RF-CX-05 | El contexto nunca debe superar el presupuesto de tokens configurado, medido con el tokenizador de OLMo. | M | Todas |

## 4.10 Generación (GE) y Program of Thoughts (PT)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-GE-01 | El sistema debe cargar OLMo con `AutoModelForCausalLM.from_pretrained(model_id)` en bf16, `device_map="cuda"`, atención `sdpa`. | M | Todas |
| RF-GE-02 | El sistema debe usar la plantilla de chat del tokenizador y decodificación greedy. | M | Todas |
| RF-GE-03 | El sistema debe usar prompts por dominio (DONES / AI) que pidan el **dato clave primero** y luego una justificación breve, basada en el contexto. | M | E1 |
| RF-GE-04 | `max_new_tokens` debe ser configurable (≈ 300 desde E1; 2048 en E0). | M | Todas |
| RF-GE-05 | Si el contexto no contiene la respuesta, el prompt debe pedir la mejor respuesta posible con el conocimiento del modelo, sin negarse. | M | E1 |
| RF-GE-06 | La respuesta final debe limpiarse: sin restos de la plantilla, sin texto de razonamiento interno, sin espacios sobrantes. | M | Todas |
| RF-GE-07 | Los prompts no deben contener instrucciones dirigidas al juez ni intentar influir en su veredicto. | M | Todas |
| RF-PT-01 | Para preguntas numéricas en modo normal, el sistema debe pedir a OLMo un programa Python que calcule el resultado a partir del contexto. | M | E4 |
| RF-PT-02 | El programa debe ejecutarse en un subproceso con límite de tiempo, sin red, sin acceso a archivos y con solo `math` disponible. | M | E4 |
| RF-PT-03 | Si el programa falla o excede el tiempo, el sistema debe responder por la vía directa. | M | E4 |
| RF-PT-04 | El resultado del programa debe incorporarse a la respuesta final con unidades y una justificación breve. | M | E4 |

## 4.11 Configuración y estrategias (CF)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-CF-01 | Cada estrategia E0-E6 debe definirse como un YAML que hereda de la anterior y cambia solo los bloques de su salto. | M | Todas |
| RF-CF-02 | La config debe validarse al cargar; claves desconocidas o valores fuera de rango son error. | M | Todas |
| RF-CF-03 | Cualquier componente debe poder desactivarse por config para la ablación leave-one-out. | M | E5 |

## 4.12 Empaquetado (EM)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-EM-01 | `build_submission.py` debe generar un zip con la estructura de §3.2 a partir de una config. | M | Todas |
| RF-EM-02 | El zip debe incluir solo los modelos y recursos que la config usa. | M | Todas |
| RF-EM-03 | `check_submission.py` debe verificar: `main.py` en la raíz, tamaño descomprimido ≤ 950 MB, que todos los imports existan en `requirements-runtime.txt`, que la config sea válida y que `answer()` devuelva `str` en la prueba de humo. | M | Todas |
| RF-EM-04 | Cada zip debe incluir `BUILD_INFO.json` (commit, config, fecha, tamaños). | M | Todas |

## 4.13 Herramientas fuera de línea (OF)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-OF-01 | Descargar los modelos auxiliares y guardarlos en fp16 en `models/`. | M | E1 |
| RF-OF-02 | Construir `glossary_dones.json` desde literatura pública, con la fuente de cada entrada. | M | E2 |
| RF-OF-03 | Descargar PDFs públicos de los sitios fuente para el banco local, registrando la URL y la licencia. | M | E1 |
| RF-OF-04 | Generar QA sintético (100-200 pares) con tipo de pregunta, dominio y chunk de origen. | S | E4 |
| RF-OF-05 | Calibrar con CMA-ES los parámetros de OWA y del q-FCM, con validación cruzada y pesos dentro de intervalos de experto, y exportarlos a `resources/`. | M | E6 |
| RF-OF-06 | Calibración multiobjetivo precisión-tiempo (NSGA-II / MO-CMA-ES). | C | — |
| RF-OF-07 | Ajuste fino LoRA de OLMo. | W | — |
| RF-OF-08 | Lanzar una sesión de trabajo en AWS con un comando: subir código y trabajos a S3, crear una instancia GPU (spot primero), ejecutar la lista de trabajos y guardar los resultados en S3 ([SPEC-031](spec/SPEC-031-ejecucion-remota-aws.md)). | M | Todas |
| RF-OF-09 | Toda instancia de AWS debe terminarse sola: al acabar sus trabajos, al cumplir el tiempo máximo de la sesión o tras 20 min de GPU inactiva. | M | Todas |

## 4.14 Evaluación local (EV)

| ID | Requisito | Prioridad | Estrategia |
|---|---|---|---|
| RF-EV-01 | Ejecutar una config sobre el banco local y guardar respuestas y trazas en `experiments/runs/<config>-<fecha>/`. | M | Todas |
| RF-EV-02 | Calcular recall@1, recall@5, recall@50 y MRR por dominio, sin LLM, contra `gold_chunks.json`. | M | E1 |
| RF-EV-03 | Juez local binario (correcto/incorrecto frente a la referencia) con backend configurable. | M | Todas |
| RF-EV-04 | Calcular la precisión balanceada por dominio con la misma fórmula que el reto. | M | Todas |
| RF-EV-05 | Comparar dos ejecuciones pregunta por pregunta (McNemar) y con IC por bootstrap. | M | E2 |
| RF-EV-06 | Generar la tabla de ablación E0-E6 y leave-one-out, y las figuras del paper (grafo del q-FCM con pesos, tiempos por etapa). | M | E6 |
| RF-EV-07 | Mantener `experiments/submissions.md` con cada envío: fecha, config, commit, estado, puntuación y tiempo. | M | Todas |
| RF-EV-08 | La evaluación local debe guardar cada pregunta en cuanto termina y poder reanudarse (`--resume`) tras una interrupción, sin repetir las preguntas ya respondidas. | M | Todas |
