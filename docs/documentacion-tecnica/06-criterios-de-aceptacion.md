# 6. Criterios de aceptación

[← Requisitos no funcionales](05-requisitos-no-funcionales.md) · [Índice](README.md) · Siguiente: [Calidad y pruebas →](07-calidad-y-pruebas.md)

Hay tres niveles de aceptación:

1. **Por requisito** (§6.1): cada RF/RNF clave tiene una condición verificable y una forma de verificarla.
2. **Por estrategia** (§6.2): cuándo una estrategia E1-E6 se queda en el sistema.
3. **Por envío** (§6.3): lista que debe cumplirse antes de subir un zip.

Formas de verificación: **PU** prueba unitaria · **PI** prueba de integración (LLM simulado) · **PH** prueba de humo (LLM pequeño) · **BL** banco local · **CB** Codabench · **RV** revisión manual.

## 6.1 Criterios por requisito

Formato *Dado / Cuando / Entonces*.

### Interfaz y robustez

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-IF-01 | RF-IF-01 | **Dado** el zip construido, **cuando** se descomprime, **entonces** `main.py` está en la raíz y `inspect.signature(answer)` tiene exactamente `(question: str, corpus_dir: str, model_id: str) -> str`. | PU |
| CA-IF-02 | RF-IF-02, RNF-CO-02 | **Dado** cualquiera de estas entradas: pregunta vacía, 10 000 caracteres, solo LaTeX, Unicode raro, `corpus_dir` vacío o inexistente, **cuando** se llama `answer()`, **entonces** devuelve un `str` no vacío y no lanza excepción. | PI |
| CA-IF-03 | RF-IF-02, RF-RT-05 | **Dado** un fallo inyectado en cada etapa (extractor, índice denso, reranker, verificación, PoT, generación), **cuando** se responde, **entonces** se usa el nivel de degradación correspondiente (N1-N4), se registra el error y la respuesta es `str`. | PI |
| CA-IF-04 | RF-IF-04, RF-RT-02 | **Dado** 3 llamadas sucesivas, **cuando** se miden, **entonces** la inicialización (modelo + índices) ocurre una sola vez. | PI |
| CA-IF-05 | RF-IF-03 | **Dado** el código fuente, **cuando** se busca con `grep`, **entonces** no hay rutas absolutas ni nombres de modelo fijos fuera de la config. | RV |

### Control de recursos

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-RT-01 | RF-RT-04 | **Dado** un reloj simulado en `t_fast` + 1 s, **cuando** se responde, **entonces** no hay reintento, ni PoT, ni $s_5$, y el contexto tiene ≤ 3 chunks. En `t_emergency` + 1 s solo se usa BM25 top-3. | PU |
| CA-RT-02 | RF-RT-07, RNF-PO-02 | **Dado** el sistema con la red bloqueada, **cuando** corre la prueba de humo completa, **entonces** termina sin errores de conexión. | PH |
| CA-RT-03 | RF-RT-06 | **Dado** un `torch.cuda.OutOfMemoryError` simulado en la generación, **cuando** se responde, **entonces** se reintenta con un contexto menor y se devuelve `str`. | PI |
| CA-RT-04 | RNF-RD-01/02 | **Dado** un envío a Codabench, **cuando** termina, **entonces** el estado es *Finished* y el tiempo reportado es < 60 min (*límite*) y ≤ 45 min (*objetivo*). | CB |
| CA-RT-05 | RNF-RC-01/02 | **Dado** el zip, **cuando** se mide el tamaño descomprimido, **entonces** es ≤ 950 MB. | PU (`check_submission`) |

### Ingesta e índices

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-IN-01 | RF-IN-05, RNF-CO-04 | **Dado** un mini-corpus con un PDF corrupto, uno cifrado, uno vacío y uno válido, **cuando** se ingiere, **entonces** se indexa el válido y los otros tres quedan registrados como omitidos. | PU |
| CA-IN-02 | RF-IN-02 | **Dado** el corpus público del banco local, **cuando** se ingiere con PyMuPDF en paralelo, **entonces** tarda menos que Docling (E0) sobre el mismo corpus. | BL |
| CA-IN-03 | RF-IN-06 | **Dado** un texto con `"tempera-\nture"`, un encabezado repetido en todas las páginas y una sección *References*, **cuando** se limpia, **entonces** queda `"temperature"`, sin el encabezado y sin las referencias. | PU |
| CA-IN-04 | RF-IN-11, RF-IN-14 | **Dado** un documento con secciones, **cuando** se divide, **entonces** cada hijo tiene `parent_id`, empieza con título y sección, y lleva `doc_id`, página y tipo. | PU |
| CA-IN-05 | RNF-CO-05 | **Dado** el corpus del banco local, **cuando** se ingiere, **entonces** ≥ 98 % de los PDF producen texto. | BL |
| CA-IX-01 | RF-IX-03 | **Dado** el texto `"Be-7 inventory in the ICS"`, **cuando** se tokeniza para BM25, **entonces** `be-7` (o `be7`) e `ics` son tokens. | PU |
| CA-IX-02 | RF-IX-02 | **Dado** un chunk indexado, **cuando** se busca con su propio texto, **entonces** aparece en el top-1 del índice denso. | PU |

### Recuperación, fusión y verificación

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-CO-01 | RF-CO-01 | **Dado** "What is the bypass ratio of the ICS Branch?", **cuando** se analiza, **entonces** las expansiones incluyen "Impurity Control System". | PU |
| CA-CO-02 | RF-CO-02 | **Dado** "volumen", ausente del vocabulario, **cuando** se corrige, **entonces** se propone "volume"; una sigla válida presente en el vocabulario no se modifica. | PU |
| CA-CO-03 | RF-CO-03 | **Dado** una pregunta que nombra "WinStat" y un índice de títulos que lo contiene, **cuando** se analiza, **entonces** `named_doc` apunta a ese documento con confianza ≥ umbral. | PU |
| CA-CO-04 | RF-CO-05 | **Dado** la pregunta de muestra 3 (constante de desintegración de Be-7), **cuando** se analiza, **entonces** `is_numeric = True`; para la pregunta 2 (diagnóstico destructivo), `False`. | PU |
| CA-RE-01 | RF-RE-02 | **Dado** confianza en el documento < umbral, **cuando** se busca, **entonces** la búsqueda es global; si ≥ umbral, todos los candidatos son de ese documento. | PU |
| CA-FU-01 | RF-FU-01 | **Dado** dos listas conocidas, **cuando** se fusiona con RRF ($k = 60$), **entonces** los puntajes coinciden con el cálculo manual (tolerancia 1e-9). | PU |
| CA-FU-02 | RF-FU-02 | **Dado** pesos $w = (1, 0)$, **entonces** OWA = máximo de las pertenencias; con $w = (0, 1)$, mínimo; con $(0{,}5; 0{,}5)$, promedio. Los pesos que no suman 1 se rechazan al cargar. | PU |
| CA-RK-01 | RF-RK-01/02 | **Dado** 50 candidatos con 2 duplicados casi idénticos, **cuando** se reordena con MMR, **entonces** los duplicados no aparecen ambos en el top-5. | PU |
| CA-VE-01 | RF-VE-01 | **Dado** cualquier conjunto de candidatos, **entonces** $s_1$ a $s_4$ están en $[0, 1]$; con un solo candidato, $s_2$ está definido (no NaN). | PU |
| CA-VE-02 | RF-VE-02 | **Dado** un LLM simulado con logits conocidos para "Yes" y "No", **cuando** se calcula $s_5$, **entonces** coincide con la fórmula y no se genera ningún token. | PU |
| CA-VE-03 | RF-VE-04 | **Dado** $\varphi = 1$, **entonces** el q-FCM se reduce al FCM clásico; con $\varphi = 0$, la salida es $A^{(0)}$. Con los pesos de experto, señales todas en 1 dan "correcta" y todas en 0 dan "incorrecta". | PU |
| CA-VE-04 | RF-VE-06 | **Dado** un veredicto "incorrecta" en el primer intento, **cuando** se procesa, **entonces** hay exactamente un reintento sin filtro por documento, y la evidencia final es la de mayor confianza de ambos intentos. | PI |
| CA-VE-05 | RF-VE-07, RNF-QR-05 | **Dado** el banco local completo, **cuando** se responde, **entonces** ninguna respuesta coincide con los patrones de abstención definidos. | BL |

### Contexto y generación

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-CX-01 | RF-CX-05 | **Dado** cualquier pregunta del banco, **cuando** se construye el contexto, **entonces** su largo en tokens de OLMo ≤ presupuesto de la config. | PI |
| CA-CX-02 | RF-CX-04 | **Dado** un contexto construido, **entonces** cada pasaje empieza con `[Doc: …, p. N]`. | PU |
| CA-GE-01 | RF-GE-03, RNF-QR-01 | **Dado** 20 respuestas del banco elegidas al azar, **cuando** se revisan, **entonces** ≥ 90 % tiene el dato clave en la primera oración. | RV |
| CA-GE-02 | RF-GE-06 | **Dado** una salida con restos de plantilla (`<|assistant|>`, espacios dobles), **cuando** se limpia, **entonces** quedan eliminados. | PU |
| CA-GE-03 | RF-GE-07, RNF-CU-03 | **Dado** todos los prompts de `resources/prompts/`, **cuando** se revisan, **entonces** no mencionan al juez, la evaluación ni piden ser marcados como correctos. | RV |
| CA-PT-01 | RF-PT-02, RNF-SE-01 | **Dado** programas que intentan `import os`, abrir un archivo, abrir un socket o hacer `while True`, **cuando** se ejecutan, **entonces** se bloquean o se cortan por tiempo y se usa la vía directa. | PU |
| CA-PT-02 | RF-PT-01/04 | **Dado** la pregunta de muestra 3 con el contexto correcto, **cuando** se usa PoT, **entonces** la respuesta contiene ≈ 0,01308 día⁻¹ (± 1 %) con unidades. | PH |

### Empaquetado, configuración y evaluación

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-EM-01 | RF-EM-03 | **Dado** un zip con `main.py` en una subcarpeta, o > 950 MB, o un import fuera del entorno, **cuando** corre `check_submission.py`, **entonces** termina con error y explica la causa. | PU |
| CA-EM-02 | RF-EM-04, RNF-RP-02 | **Dado** un zip, **entonces** `BUILD_INFO.json` permite reconstruir el mismo zip desde el commit indicado. | RV |
| CA-CF-01 | RF-CF-01 | **Dado** `eN.yaml` y `e(N-1).yaml` resueltos, **cuando** se comparan, **entonces** solo cambian los bloques del salto documentado en la estrategia. | PU |
| CA-CF-02 | RF-CF-02 | **Dado** una config con una clave mal escrita, **cuando** se carga, **entonces** falla con un mensaje que nombra la clave. | PU |
| CA-EV-01 | RF-EV-04 | **Dado** veredictos conocidos (p. ej. D = 3/10, P = 9/15), **cuando** se calcula, **entonces** $A = 0{,}5 \cdot (0{,}3 + 0{,}6) = 0{,}45$. | PU |
| CA-EV-02 | RF-EV-05 | **Dado** dos vectores de veredictos conocidos, **cuando** se aplica McNemar, **entonces** el p-valor coincide con `scipy`/`statsmodels` de referencia. | PU |
| CA-RP-01 | RNF-RP-01 | **Dado** la misma config y el mismo banco, **cuando** se ejecuta dos veces, **entonces** las respuestas son idénticas. | PH |

### Infraestructura AWS

| ID | Requisito | Criterio | Verif. |
|---|---|---|---|
| CA-AWS-01 | RF-OF-08 | **Dado** una lista de trabajos `jobs/smoke.txt`, **cuando** se ejecutan `push.sh` y `launch.sh`, **entonces** los resultados aparecen en `s3://<bucket>/runs/smoke/` sin intervención manual. | RV (sesión de prueba) |
| CA-AWS-02 | RF-OF-09, RNF-CS-02/04 | **Dado** una sesión con `--max-hours 1` y un trabajo que no termina, **cuando** pasa 1 h, **entonces** la instancia queda en estado `terminated`. | RV |
| CA-AWS-03 | RF-OF-09, RNF-CS-03 | **Dado** una instancia sin trabajos activos, **cuando** la GPU queda inactiva, **entonces** se termina en ≤ 25 min. | RV |
| CA-AWS-04 | RF-EV-08 | **Dado** una evaluación interrumpida a mitad (spot o manual), **cuando** se relanza con `--resume`, **entonces** no se repiten preguntas y el resultado final es igual al de una ejecución sin cortes. | PI + RV |
| CA-AWS-05 | ADR-16 | **Dado** el security group del proyecto, **entonces** no tiene reglas de entrada; el rol de la instancia solo tiene `AmazonSSMManagedInstanceCore` y acceso al bucket. | RV |

## 6.2 Criterios por estrategia

Una estrategia **se acepta** (se queda en el sistema) si cumple su criterio y **no empeora** la otra dimensión más allá de la tolerancia fijada antes de medir:

- Tolerancia de precisión: −1 pregunta en el banco local o −2,5 puntos en Codabench.
- Tolerancia de tiempo: +10 % del tiempo total.

| Estrategia | Criterio de aceptación | Medido en |
|---|---|---|
| **E0** | Envío *Finished* en Codabench; tiempos por etapa medidos; precisión local de E0 registrada como referencia. | CB, BL |
| **E1** | Tiempo total menor que E0 **y** precisión ≥ E0 − tolerancia **y** recall@5 ≥ E0. | BL, CB |
| **E2** | Recall@5 del híbrido > máx(recall@5 BM25, recall@5 denso) en al menos un dominio y no menor en el otro; +tiempo por pregunta < 1 s. | BL |
| **E3** | Recall@1 y recall@5 > E2; tokens de contexto promedio ≤ E2; +tiempo por pregunta ≤ 3 s. | BL, CB |
| **E4** | Precisión en el subconjunto de preguntas reintentadas > E3 en ese mismo subconjunto; precisión en numéricas ≥ E3; tiempo total dentro de la tolerancia. | BL |
| **E5** | Recall@50 o recall@5 de OWA ≥ RRF, **y** (mejor en algún dominio **o** mejor sin reranker en el leave-one-out); costo ≤ 50 ms. | BL |
| **E6** | Precisión ≥ E5 con menos reintentos, **o** > E5; quitar $s_5$ reduce la precisión (leave-one-out); q-FCM ≥ regresión logística sobre las mismas señales; público ≤ 45-50 min. | BL, CB |
| **Sistema final** | Precisión balanceada > E0 y > zero-shot en Codabench; ningún dominio por debajo de E0; *Finished* con ≤ 45 min. | CB |

Si una estrategia **no** se acepta, se documenta el resultado (negativo) y la siguiente se construye sobre la última aceptada. Las estrategias de CI (E5, E6) pueden quedarse con precisión igual si aportan interpretabilidad o velocidad medibles, tal como prevé la estrategia.

## 6.3 Definición de "listo para enviar"

Un zip solo se sube si **todos** los puntos están marcados:

- [ ] `pytest tests/unit tests/integration` pasa sin fallos.
- [ ] `ruff check` y `mypy src/` sin errores.
- [ ] `check_submission.py` pasa: estructura, tamaño ≤ 950 MB, imports, config válida.
- [ ] Prueba de humo de punta a punta con red bloqueada: todas las respuestas son `str`, sin excepciones.
- [ ] Para cambios grandes o la versión final: **ensayo general en AWS** con OLMo real y 50 preguntas cronometradas ([guía §8.8](08-guia-de-despliegue.md#88-paso-7-despliegue-en-codabench-cada-envío)).
- [ ] Tiempo medido o estimado ≤ 45 min para 50 preguntas.
- [ ] El cambio frente al último envío está descrito en una línea y tiene una hipótesis.
- [ ] Commit etiquetado (`sub-AAAA-MM-DD`) y `BUILD_INFO.json` coincide con él.
- [ ] Borrador de metodología actualizado y adjunto.
- [ ] Hora de subida antes de las 23:55 UTC (18:55 en Perú).
- [ ] Tras el resultado: fila agregada en `experiments/submissions.md`.

## 6.4 Matriz de trazabilidad (resumen)

| Objetivo | Requisitos | Criterios | Prueba / evidencia |
|---|---|---|---|
| OE-1 Superar baselines | RF-GE-*, RF-CX-*, RF-RE-* | §6.2 Sistema final | Codabench |
| OE-2 Tiempo con margen | RF-RT-01..06, RNF-RD-* | CA-RT-01, CA-RT-04 | `tests/unit/test_clock.py`, Codabench |
| OE-3 Evidencia correcta | RF-IN-*, RF-IX-*, RF-CO-*, RF-RE-*, RF-FU-*, RF-RK-* | CA-IN-*, CA-IX-*, CA-CO-*, CA-FU-*, §6.2 E1-E3 | `eval/retrieval_metrics.py` |
| OE-4 Ambos dominios | RF-CO-04, RF-GE-03, RF-EV-04 | §6.2 Sistema final | Reporte por dominio |
| OE-5 Innovación CI | RF-FU-02/03, RF-VE-02..05, RF-OF-05 | CA-FU-02, CA-VE-02/03, §6.2 E5-E6 | `tests/unit/test_owa.py`, `test_qfcm.py`, ablación |
| OE-6 Medir aportes | RF-CF-03, RF-EV-05/06 | CA-CF-01, CA-EV-02 | `eval/report.py` |
| OE-7 Material del paper | RF-EV-06, RNF-IN-* | RV | Figuras y tablas exportadas |
| OE-8 Sin envíos fallidos | RF-IF-*, RF-RT-05, RF-EM-03, RNF-CO-* | CA-IF-*, CA-EM-01, §6.3 | `check_submission.py`, prueba de humo |
| Costo acotado (soporte a todos) | RF-OF-08/09, RF-EV-08, RNF-CS-* | CA-AWS-01..05 | Sesión de prueba en AWS, AWS Budgets |
