# 7. Calidad y pruebas

[← Criterios de aceptación](06-criterios-de-aceptacion.md) · [Índice](README.md) · Siguiente: [Guía de despliegue →](08-guia-de-despliegue.md)

## 7.1 Modelo de calidad

Se usan las características de ISO/IEC 25010 que importan en este reto, con la métrica que las mide.

| Característica | Qué significa aquí | Métrica principal | Requisitos |
|---|---|---|---|
| **Adecuación funcional** | Responde bien preguntas de experto | Precisión balanceada por dominio; recall@5 | RF-*, RNF-QR-* |
| **Eficiencia de desempeño** | Cabe en 1 h, 1 GPU, 1 GB | Tiempo total y por etapa; pico de VRAM; tamaño del zip | RNF-RD-*, RNF-RC-* |
| **Fiabilidad** | Nunca falla un envío ni una pregunta | Envíos *Failed*; excepciones por pregunta | RNF-CO-* |
| **Compatibilidad / portabilidad** | Corre en la imagen oficial sin red | Imports fuera del entorno; llamadas de red | RNF-PO-* |
| **Mantenibilidad** | Cambiar una estrategia sin romper otra | Cobertura; lint; tamaño de módulos | RNF-MA-* |
| **Seguridad** | PoT no puede dañar el proceso | Pruebas de escape del sandbox | RNF-SE-* |
| **Interpretabilidad** (extra) | Las decisiones CI se pueden explicar | Trazas completas; grafo del q-FCM | RNF-IN-* |

## 7.2 Estrategia de pruebas

| Nivel | Qué cubre | Herramienta | LLM | Dónde | Cuándo |
|---|---|---|---|---|---|
| **Unitarias** | Funciones puras: limpieza, chunking, tokenización BM25, RRF, OWA, señales, q-FCM, reloj, config, sandbox PoT, métricas | `pytest` | No | Laptop | Cada commit |
| **Integración** | Pipeline completo con un LLM simulado (respuestas y logits fijos) sobre un mini-corpus de `tests/fixtures/` | `pytest` | Simulado | Laptop | Cada commit |
| **Inyección de fallos** | Excepciones forzadas en cada etapa, OOM simulado, PDFs dañados, reloj adelantado | `pytest` + `monkeypatch` | Simulado | Laptop | Cada commit |
| **Humo de punta a punta** | El zip real, descomprimido en una carpeta limpia, con red bloqueada, llamado como lo haría Codabench | `scripts/check_submission.py --smoke` | Pequeño (p. ej. un Instruct de 0,5-1,5B) | Colab / Kaggle | Antes de cada envío |
| **Recuperación** | Recall@k, MRR por dominio sobre el banco local | `eval/retrieval_metrics.py` | No | Laptop | Cada cambio en etapas 1-2 |
| **Respuesta** | Precisión con juez local sobre el banco | `eval/run_local.py` + `eval/judge.py` | Sí | Colab / AWS opcional | Cada estrategia |
| **Aceptación oficial** | Precisión y tiempo reales | Codabench | OLMo | H100 | 1 por día |

### Simulación del LLM

`tests/fixtures/fake_llm.py` implementa la misma interfaz que `generate.llm` (`generate`, `yes_no_prob`, `count_tokens`) con salidas deterministas. Permite probar la verificación, el PoT y la degradación sin GPU.

### Casos de prueba prioritarios

| Caso | Por qué |
|---|---|
| Las 25 preguntas de muestra pasan por todo el pipeline sin excepción | Cubre erratas reales ("volumen", "le $G$") y LaTeX |
| Corpus vacío / inexistente | Debe caer a zero-shot (N3) sin fallar |
| PDF de 500 páginas y PDF de 0 bytes | Tiempo máximo de extracción y robustez |
| Pregunta con dos papers homónimos (ZeroDiff, REVEL) | Filtro por documento con confianza baja → búsqueda global |
| Pregunta numérica con contexto sin el dato | PoT no debe inventar; vía directa como respaldo |
| Reloj en 49:59, 50:01 y 56:01 | Cambios de modo exactos |

## 7.3 Protocolo experimental

1. **Hipótesis primero:** cada cambio se anota con la hipótesis y el criterio de §6.2 **antes** de medir.
2. **Un cambio por salto:** la config nueva solo cambia los bloques del salto (CA-CF-01).
3. **Medir recuperación antes que respuesta:** si recall@5 no mejora, no se gasta GPU en la precisión.
4. **Banco local:** 25 de muestra + QA sintético (100-200) + chunks correctos marcados a mano. Se separa en **calibración** (para CMA-ES) y **prueba** (para reportar), con validación cruzada de 5 particiones estratificada por dominio y tipo.
5. **Estadística:** McNemar pregunta por pregunta entre dos configuraciones; IC al 95 % por bootstrap (10 000 remuestreos) para la precisión. Una diferencia sin significancia se reporta como "sin diferencia".
6. **Por dominio:** todas las tablas muestran D, P y el promedio balanceado.
7. **Ablación:** incremental (E0 → E6) y leave-one-out sobre el sistema final.
8. **Resultados negativos:** se reportan con su posible causa.
9. **Juez local:** sirve para **comparar** configuraciones, no para predecir el puesto. Se valida comparando su veredicto con una revisión manual en las 25 preguntas de muestra (acuerdo esperado ≥ 85 %).

### Métricas

| Métrica | Fórmula / definición | Uso |
|---|---|---|
| Precisión balanceada | $A = \tfrac{1}{2}(\bar v_\mathcal{D} + \bar v_\mathcal{P})$ | Métrica oficial |
| Recall@k | % de preguntas con al menos un chunk correcto en el top-k | Recuperación |
| MRR | Media de $1/\text{rango}$ del primer chunk correcto | Orden |
| Tokens de contexto | Media y p95 por pregunta | Costo |
| Tiempo | Total, por etapa, por pregunta (media y p95) | Eficiencia y desempate |
| % reintentos | Preguntas con veredicto "incorrecta" / total | Actividad de la verificación |
| Precisión condicionada | Precisión en preguntas reintentadas, numéricas, por tipo de pregunta | Análisis de E4-E6 |

## 7.4 Puertas de calidad

| Puerta | Cuándo | Condición para pasar |
|---|---|---|
| **G1 Commit** | Cada commit a `main` | Unitarias + integración en verde; `ruff` y `mypy` limpios |
| **G2 Estrategia** | Al cerrar cada E1-E6 | Criterio de §6.2 evaluado y anotado (aceptada o no) |
| **G3 Envío** | Antes de subir un zip | Lista completa de §6.3 |
| **G4 Envío final** | Última semana (23-30 nov) | La config elegida tiene ≥ 1 envío *Finished* previo con ≤ 45 min; no se suben cambios no probados en Codabench el último día |
| **G5 Paper** | Diciembre | Todas las cifras del paper salen de `eval/report.py` y de envíos registrados |

## 7.5 Gestión de envíos

- **Presupuesto:** ~33 envíos posibles entre el 29 oct y el 30 nov. Reservar al menos 3 para la última semana.
- **Prioridad de uso:** (1) validar que una estrategia nueva no falla y mide tiempo real; (2) confirmar una mejora local significativa; (3) nunca para "probar suerte" sin hipótesis.
- **Registro** (`experiments/submissions.md`):

| Fecha (UTC) | Config | Commit | Cambio / hipótesis | Estado | Precisión | Tiempo (s) | Notas |
|---|---|---|---|---|---|---|---|
| 2026-10-30 | e0 | `abc1234` | Baseline del kit | Finished | — | — | Referencia |

- **Mejor envío:** Codabench usa *Force_Best*; el leaderboard público usa solo el 50 % de las preguntas (≈ 1-2,5 puntos por pregunta), así que se elige el final por precisión local + pública + margen de tiempo, no solo por el máximo público.

## 7.6 Registro de riesgos de calidad

| ID | Riesgo | Prob. | Impacto | Mitigación | Indicador de alerta |
|---|---|---|---|---|---|
| R-01 | Superar 1 h en el público | Media | Alto (envío fallido) | Reloj global, presupuestos, prueba de tiempos por etapa | Tiempo de un envío > 50 min |
| R-02 | Preguntas sin responder en el privado (2 h) | Media | Alto | Público ≤ 45 min; ADR-07 (consultar fase en Discord) | Estimado privado > 100 min |
| R-03 | Envío fallido por error de código | Baja | Alto (pierde el día) | §6.3, prueba de humo, cadena N0-N4 | Cualquier *Failed* |
| R-04 | Zip > 1 GB | Media | Alto | Control a 950 MB; fp16; alternativas pequeñas | `check_submission` > 900 MB |
| R-05 | Banco local poco representativo | Media | Medio | Validar con E0 en Codabench; QA sintético por tipo | Orden local ≠ orden público |
| R-06 | Sobreajuste de CMA-ES | Alta | Medio | Validación cruzada, intervalos de experto, banco de prueba separado | Gran brecha calibración vs prueba |
| R-07 | Mejoras dentro del ruido | Alta | Medio | McNemar, bootstrap, no decidir por 1 pregunta | p > 0,05 |
| R-08 | Respuestas en figuras no extraídas | Media | Medio | Pies de figura como chunks; medir frecuencia antes de invertir en OCR | Fallos de recall con chunk en figura |
| R-09 | Cambio de reglas o dependencias | Baja | Medio | Seguir Discord; `requirements-runtime.txt` actualizado | Anuncio oficial |
| R-10 | Descuidar un dominio | Media | Alto | Reportes por dominio; criterio "ningún dominio < E0" | Caída en D o P frente a E0 |
