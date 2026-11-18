# 2. Estrategia: visión general

## Objetivo

Construir un sistema de preguntas y respuestas para IFMIF-DONES y papers de IA que:

1. Maximice la **domain-balanced accuracy** (Fase 1, 30 % de la nota final).
2. Responda dentro del límite de tiempo con margen.
3. Incorpore una capa de **Inteligencia Computacional** original y justificada (innovación técnica, 40 % de la nota final).

## Restricciones que condicionan el diseño

| Restricción | Valor | Consecuencia |
|---|---|---|
| Modelo | OLMo 3.1 32B Instruct (bf16 ≈ 64 GB) | Disponible en caché local; no va en el zip |
| Hardware | 1× H100 80 GB, 32 núcleos, 128 GB RAM | Cabe el modelo en bf16; no hace falta cuantizar |
| Tiempo público | 1 h, límite **duro** (si se excede, el envío falla) | Medir y dejar margen |
| Tiempo privado | 2 h, límite **blando**: solo se puntúan las preguntas respondidas a tiempo (aclaración del organizador, Discord, 2 oct 2026) | Si el público tarda menos de ~45-50 min, el privado debería caber |
| Tamaño del envío | 1 GB descomprimido | Es la restricción que decide qué modelos auxiliares caben |
| Modelos auxiliares | Se permite cualquier modelo, generativo o no (aclaración del organizador) | No se usan en el plan actual; quedan como opción si una medición lo justifica |
| Internet | No durante la evaluación | Todo recurso externo se prepara offline |
| Envíos | 1 por día (máx. 60) | Probar en local antes de subir |
| PDF | Texto nativo (el kit usa `do_ocr=False`); pueden tener figuras | La información solo presente en imágenes no se extrae |

## Pipeline de 5 etapas

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. PREPARACIÓN DEL CORPUS (una vez por ejecución)                │
│    1a extracción · 1b limpieza · 1c chunking · 1d enriquecimiento│
│    1e embeddings · 1f índices · 1g recursos offline              │
├──────────────────────────────────────────────────────────────────┤
│ 2. RECUPERACIÓN (por pregunta)                                   │
│    2a procesamiento de la consulta                               │
│    2b búsqueda de candidatos (BM25 y/o denso)                    │
│    2c fusión (solo si hay más de un buscador)                    │
│    2d reordenamiento (cross-encoder)                             │
├──────────────────────────────────────────────────────────────────┤
│ 3. VERIFICACIÓN DE LA EVIDENCIA                                  │
│    3a señales · 3b decisor · 3c acciones                         │
│    Correcta → 4 · Ambigua → refinar → 4 · Incorrecta → volver a 2│
├──────────────────────────────────────────────────────────────────┤
│ 4. CONSTRUCCIÓN DEL CONTEXTO                                     │
│    Cantidad, orden, expansión, formato                           │
├──────────────────────────────────────────────────────────────────┤
│ 5. GENERACIÓN (OLMo 3.1 32B)                                     │
└──────────────────────────────────────────────────────────────────┘
 ═══ CONTROL DE RECURSOS (transversal): tiempo, tokens, memoria ═══
```

### Glosario

| Término | Significado en este proyecto |
|---|---|
| **Fusión** | Combinar las listas de resultados de varios buscadores en una sola (RRF u OWA) |
| **Reordenamiento (rerank)** | Segunda fase de la recuperación: un cross-encoder relee pregunta + pasaje y reordena los ~50 candidatos |
| **Verificación** | Juzgar si la evidencia recuperada permite responder, antes de armar el contexto, y decidir una acción |
| **Contexto** | El texto que efectivamente lee OLMo: qué pasajes, cuántos y en qué orden |
| **Control de recursos** | Restricción transversal: tiempo, tokens y memoria por pregunta y en total |

## Estrategias

Una base estándar y seis estrategias incrementales. Cada una hereda la anterior y cambia un solo bloque.

| Estrategia | Nombre | Qué agrega | Tipo | Detalle |
|---|---|---|---|---|
| **E0** | Base estándar | RAG del starter kit sin cambios | Referencia | [E0](estrategias/E0-base-estandar.md) |
| **E1** | Preparación optimizada | Extracción, chunking y embeddings mejores + contexto corto + respuesta concisa | Ingeniería | [E1](estrategias/E1-preparacion-optimizada.md) |
| **E2** | Recuperación híbrida | BM25 + denso con RRF + procesamiento de la consulta | Ingeniería | [E2](estrategias/E2-recuperacion-hibrida.md) |
| **E3** | Recuperación en dos fases | Filtro por documento + reranker + selección del contexto | Ingeniería | [E3](estrategias/E3-recuperacion-dos-fases.md) |
| **E4** | Verificación clásica | Etapa 3 con umbrales fijos + reintento + PoT | Ingeniería | [E4](estrategias/E4-verificacion-clasica.md) |
| **E5** | Fusión difusa | RRF → OWA | **CI 1** | [E5](estrategias/E5-fusion-difusa.md) |
| **E6** | Verificación difusa | Umbrales → q-FCM con juez OLMo, calibrado con CMA-ES | **CI 2 y 3** | [E6](estrategias/E6-verificacion-qfcm.md) |

### Configuración por etapa

"=" significa que se mantiene igual que en la estrategia anterior.

| Subetapa | E0 | E1 | E2 | E3 | E4 | E5 | E6 |
|---|---|---|---|---|---|---|---|
| 1a Extracción | Docling | PyMuPDF ∥ + pdfplumber en tablas | = | = | = | = | = |
| 1b Limpieza | Ninguna | ftfy + guiones + encabezados + referencias | = | = | = | = | = |
| 1c Chunking | Fijo 800 car. | Sección + padre-hijo + tablas aparte | = | = | = | = | = |
| 1d Enriquecimiento | Ninguno | Título + sección + metadatos + dominio | = | = | = | = | = |
| 1e Embeddings | MiniLM (CPU) | bge-base (GPU) | = | = | = | = | = |
| 1f Índices | Vectorial | FAISS Flat | + BM25 | + títulos | = | = | = |
| 1g Recursos offline | — | — | Glosario DONES | = | = | = | = |
| 2a Consulta | Original | Original | Glosario + erratas | + detección del paper | = | = | = |
| 2b Buscadores | Denso | Denso | BM25 + denso (top-50) | + filtro doc → pasaje | = | = | = |
| 2c Fusión | — | — | RRF | RRF | RRF | **OWA** | OWA |
| 2d Reranker | No | No | No | bge-reranker-base + MMR | = | = | = |
| 3a Señales | — | — | — | — | Top-1, brecha, acuerdo, cobertura | = | **+ juez OLMo** |
| 3b Decisor | — | — | — | — | Umbrales fijos | Umbrales fijos | **q-FCM + CMA-ES** |
| 3c Acciones | — | — | — | — | Aceptar / refinar / 1 reintento / PoT | = | = |
| 4 Contexto | Hasta 10k tokens | Top-5, máx. 4k | = | Umbral (3-8) + vecinos | = | = | = |
| 5 Generación | Genérica, 2048 tokens | Por dominio, concisa, ≈300 | = | = | + PoT si es numérica | = | = |
| Control | — | Caché global | = | = | + reloj global (modo rápido) | = | = |

### Qué mide cada salto

| Salto | Pregunta que responde |
|---|---|
| E0 → E1 | ¿Cuánto aportan una preparación y una salida bien hechas? |
| E1 → E2 | ¿Cuánto aporta combinar recuperación léxica y densa? |
| E2 → E3 | ¿Cuánto aportan el reranking y el filtro por documento? |
| E3 → E4 | ¿Cuánto aporta verificar la evidencia? |
| E4 → E5 | ¿La fusión difusa supera a RRF? |
| E5 → E6 | ¿La verificación con q-FCM supera a los umbrales fijos? |
| E0 → E6 | ¿Cuánto mejora el sistema completo frente al estándar? |

## Metodología de evaluación

### Principio

La secuencia E0 a E6 **no asume que cada paso mejore la precisión**. Cada paso es una hipótesis basada en literatura de otros benchmarks, que puede no cumplirse en este corpus. Lo que funcione se queda; lo que no, se reporta y se descarta.

### Criterios de éxito por paso

| Paso | Criterio |
|---|---|
| E1 | Menos tiempo sin perder precisión |
| E2, E3 | Más recall@5 y más precisión |
| E4 | Más precisión en preguntas con evidencia débil, con aumento de tiempo acotado |
| E5, E6 | Mejor que su alternativa simple (RRF, umbrales), o igual pero más interpretable o más rápido |

**Regla de decisión:** un componente se queda si mejora precisión o tiempo sin empeorar el otro más allá de una tolerancia fijada de antemano.

### Métricas

| Métrica | Qué mide | Necesita OLMo |
|---|---|---|
| Domain-balanced accuracy (total, DONES, Papers) | Precisión, métrica oficial | Sí |
| Recall@5 | Si el chunk con la respuesta llega al top-5 | No |
| Tiempo total y por pregunta | Eficiencia | Sí |
| Tokens de contexto promedio | Costo de lectura del LLM | No |
| % de preguntas con reintento (E4-E6) | Actividad de la verificación | Sí |

### Diseño experimental

1. **Ablación incremental** (E0 → E6): aporte de cada paso al construir el sistema.
2. **Ablación leave-one-out** (sistema completo menos un componente): detecta interacciones, por ejemplo si el reranker absorbe la diferencia entre RRF y OWA.
3. **Resultados por dominio**, no solo el promedio.
4. **Estadística:** banco local ampliado con QA sintético (100-200 preguntas); comparación pregunta por pregunta (McNemar) o intervalos de confianza por bootstrap. En el leaderboard público una sola pregunta mueve ~1 a 2,5 puntos.
5. **Resultados negativos:** se reportan y se analizan.

### Banco de evaluación local

- Las 25 preguntas de `sample_qa.json`.
- QA sintético generado desde PDF públicos de los sitios fuente.
- Chunk correcto marcado a mano para medir recall@5.
- Juez local binario (correcto/incorrecto frente a la referencia). La precisión local sirve para **comparar estrategias entre sí**, no para predecir el puesto.

## Recursos de cómputo

| Tarea | Dónde | Costo |
|---|---|---|
| Etapas 1, 2 y 4; fusión, q-FCM, CMA-ES; recall@5 | Laptop (CPU) | 0 |
| Verificar que `main.py` no falle de punta a punta | Colab o Kaggle gratis (modelo pequeño) | 0 |
| Precisión y tiempo reales | Envíos diarios a Codabench (H100) | 0 |
| Depuración o medición puntual en H100 (opcional) | AWS p5.4xlarge (requiere plan de pago y cuota de GPU) | ≈ 6,9 USD/h |

Plan por defecto: escenario sin gasto. AWS solo si aparece un problema concreto que no se pueda resolver sin ver la ejecución en una H100.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Superar 1 h en el público | Medir por etapa; reloj global con modo rápido |
| Preguntas sin responder en el privado (2 h) | Mantener el público bajo ~45-50 min |
| Envío fallido (pierde el día) | Probar `main.py` en local; `try/except` que siempre devuelva `str` |
| Superar 1 GB | Verificar tamaños con `du -sh` antes de empaquetar |
| Respuestas solo presentes en figuras | Extraer pies de figura; medir la frecuencia en PDF públicos antes de invertir en OCR |
| Sobreajuste de la calibración (25 preguntas) | QA sintético, validación cruzada, pesos por intervalos |
| Mejoras dentro del ruido | Estadística pregunta por pregunta |

## Calendario

| Semana | Actividad | Envíos |
|---|---|---|
| 26 oct - 1 nov | Inscripción y equipo (**cierre 1 nov**) · E0 a E2 en local · banco de evaluación | E0 de referencia |
| 2 - 8 nov | E3 a E5 en local (recall@5) · pipeline completo en Colab | E1, E2 |
| 9 - 15 nov | E4 completo · implementación del q-FCM | E3, E4 |
| 16 - 22 nov | E5 y E6 · calibración con CMA-ES · ablación leave-one-out | E5, E6 |
| 23 - 30 nov | Ajustes finales · mejor envío con margen de tiempo | Mejores versiones |
| Diciembre | Paper IEEE de 4 páginas (si pasa a la Fase 2) | — |

## Mejoras evaluadas pero no adoptadas

Quedan registradas como opciones si las mediciones las justifican:

| Mejora | Sobre | Motivo para considerarla |
|---|---|---|
| Fusión difusa dinámica (pesos según dominio y tipo de pregunta, OWA o Choquet) | E5 | Mayor originalidad; el reto lista "fusión dinámica de conocimiento" como línea de investigación |
| Pesos del q-FCM por intervalos + comparación con regresión logística | E6 | Reduce sobreajuste y fortalece la comparación |
| Calibración multiobjetivo precisión-tiempo (NSGA-II, MO-CMA-ES) | E6 | El reto pide recursos realistas y el tiempo es el desempate |
| Modelos auxiliares adicionales (LLM pequeño, OCR, NLI) | Varias | Permitidos por el organizador; limitados por el 1 GB |
