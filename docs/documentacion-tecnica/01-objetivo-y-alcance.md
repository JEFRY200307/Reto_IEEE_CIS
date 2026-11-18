# 1. Objetivo y alcance

[← Índice](README.md) · Siguiente: [Arquitectura →](02-arquitectura.md)

## 1.1 Problema

Un LLM de propósito general (OLMo 3.1 32B Instruct, fijo por el reto) debe responder preguntas de expertos sobre dos dominios muy especializados:

- **D — IFMIF-DONES:** instalación de irradiación de materiales de fusión en Granada (lazo de litio, intercambiadores, diagnósticos de haz, inventarios de Be-7 y tritio, edificios).
- **P — Papers de IA:** artículos de investigación muy específicos (FCM, GPAIS, Mamba, aprendizaje federado, matemática pura, etc.).

El conocimiento necesario no está en el modelo sino en un **corpus privado de PDFs con distractores**, que solo se puede leer durante la evaluación, en **una hora**, **sin internet** y con **una GPU**. Un juez LLM oculto marca cada respuesta como correcta o incorrecta.

## 1.2 Objetivo general

Construir un sistema de preguntas y respuestas basado en recuperación que **maximice la precisión balanceada por dominio** del modelo fijo dentro de los límites de recursos del reto, e incorpore una capa de **Inteligencia Computacional** original, medible y explicable.

## 1.3 Objetivos específicos

| ID | Objetivo | Indicador | Meta |
|---|---|---|---|
| OE-1 | Superar los baselines oficiales | Precisión balanceada en Codabench | > E0 (RAG del kit) y > zero-shot |
| OE-2 | Responder dentro del tiempo con margen | Tiempo total en el leaderboard público | ≤ 45 min (*objetivo*); < 60 min (*límite*) |
| OE-3 | Recuperar la evidencia correcta pese a los distractores | Recall@5 en el banco local | Mayor que E0 en ambos dominios |
| OE-4 | No descuidar ningún dominio | Precisión por dominio (D y P) | Ninguno por debajo de su valor en E0 |
| OE-5 | Aportar innovación en Inteligencia Computacional | Componentes CI implementados y medidos | OWA (E5), q-FCM (E6) y CMA-ES (E6) con ablación |
| OE-6 | Medir el aporte de cada componente | Ablación incremental y leave-one-out | Tabla de resultados E0 a E6 con estadística |
| OE-7 | Dejar material para la Fase 2 | Paper IEEE de 4 páginas | Figuras, tablas y parámetros exportados por el sistema |
| OE-8 | No perder envíos por fallos | Envíos con estado *Failed* | 0 por errores de código |

## 1.4 Alcance

### Dentro del alcance

| Bloque | Incluye |
|---|---|
| **Sistema en línea** (lo que corre en Codabench) | `main.py` + paquete `dsqa`: ingesta de PDFs, índices léxico/denso/títulos, procesamiento de la consulta, búsqueda, fusión (RRF/OWA), reranking, verificación (umbrales/q-FCM), construcción de contexto, generación con OLMo, PoT, control de recursos, tolerancia a fallos |
| **Herramientas fuera de línea** (lo que corre antes del envío) | Descarga y empaquetado de modelos auxiliares, glosario de DONES, QA sintético, calibración CMA-ES, construcción y verificación del zip |
| **Evaluación local** | Banco local, juez local, métricas de recuperación y de respuesta, estadística (McNemar, bootstrap), registro de experimentos y de envíos |
| **Infraestructura de desarrollo** | Entorno en AWS para correr OLMo (p5.4xlarge spot, S3, sesiones desechables, control de costos) y su guía de despliegue |
| **Estrategias** | E0 a E6 como configuraciones intercambiables |
| **Documentación** | Esta documentación técnica, registro de decisiones, material para el paper |

### Fuera del alcance (en esta versión)

| Elemento | Motivo |
|---|---|
| Cambiar el modelo base o hacer ajuste fino completo | Prohibido / inviable por las reglas |
| Ajuste fino LoRA de OLMo | No previsto en E0-E6; se registra como opción futura (RF marcado **W**) |
| OCR de figuras y tablas escaneadas | Los PDF son texto nativo; se reevalúa solo si se mide que muchas respuestas están en figuras |
| Preindexar el corpus oficial | El corpus de evaluación no es accesible antes |
| Interfaz gráfica, API web o servicio desplegado | El entregable es un `.zip` que llama Codabench |
| Modelos auxiliares generativos adicionales (LLM pequeño, NLI) | Permitidos, pero limitados por 1 GB; solo si una medición lo justifica |
| Variantes opcionales (OWA dinámico / Choquet, pesos por intervalos, calibración multiobjetivo) | Registradas como mejoras futuras (prioridad **C**) |
| Cualquier interacción dirigida al LLM juez | Prohibido (descalificación) |

## 1.5 Partes interesadas

| Parte | Interés | Cómo lo atiende el sistema |
|---|---|---|
| Equipo (desarrolladores) | Iterar rápido, no perder envíos | Configuración por YAML, pruebas locales, chequeo previo al envío |
| Plataforma Codabench | Ejecutar `answer()` dentro de los límites | Contrato de interfaz y límites de tiempo/espacio respetados |
| LLM juez (Fase 1) | Respuestas verificables contra una referencia concisa | Respuesta con el dato clave primero y justificación breve |
| Expertos de dominio (Fase 2, Q) | Respuestas correctas y fundamentadas | Respuestas basadas en evidencia, con razonamiento claro |
| Comité Científico (Fase 2, I) | Uso adecuado y original de CI | Componentes CI medidos, interpretables y documentados |
| Curso SCC0233 | Comparar estrategias de recuperación | Ablación E0-E6 con métricas de precisión y eficiencia |

## 1.6 Supuestos

| ID | Supuesto | Si no se cumple |
|---|---|---|
| SUP-01 | El corpus de evaluación es el mismo en las fases pública y privada | El índice se construye en cada ejecución igualmente; sin impacto en el diseño |
| SUP-02 | Los PDF tienen texto nativo (el kit usa `do_ocr=False`) | Fallback: documento sin texto se omite y se registra |
| SUP-03 | El modelo base se carga desde caché local con `from_pretrained(model_id)` | Se usa siempre el `model_id` recibido, nunca una ruta fija |
| SUP-04 | La fase pública evalúa ~50 preguntas y la privada ~100 | El reloj global protege el límite aunque el número cambie |
| SUP-05 | El límite privado (2 h) es blando: solo cuentan las preguntas respondidas a tiempo (aclaración en Discord, 2 oct 2026) | Si fuera duro, se baja el umbral del modo rápido |
| SUP-06 | Las versiones de `requirements-participant.txt` son las del entorno | Cualquier cambio anunciado en Discord se refleja en `requirements-runtime.txt` |
| SUP-07 | El sistema no sabe en qué fase está ni cuántas preguntas quedan | Ver [ADR-07](02-arquitectura.md#28-decisiones-de-arquitectura-adr) |

## 1.7 Restricciones

Vienen de las reglas oficiales ([03](../contexto-inicial/03-reglas-y-bases-oficiales.md), [05](../contexto-inicial/05-formato-de-envio.md), [08](../contexto-inicial/08-entorno-y-dependencias.md)) y **no son negociables**.

| ID | Restricción | Valor |
|---|---|---|
| RES-01 | Modelo base | `allenai/Olmo-3.1-32B-Instruct`, recibido en `model_id`; contexto máx. 65 536 tokens |
| RES-02 | Hardware | 1× H100 80 GB, 32 núcleos CPU, 128 GB RAM |
| RES-03 | Tiempo (reloj de pared, incluye carga del modelo e indexado) | 1 h pública (duro) · 2 h privada |
| RES-04 | Tamaño del envío | 1 GB descomprimido |
| RES-05 | Red | Sin internet durante la evaluación |
| RES-06 | Dependencias | Solo las preinstaladas; sin vLLM ni flash-attn (atención `sdpa`/`eager`) |
| RES-07 | Interfaz | `main.py` en la raíz del zip con `answer(question: str, corpus_dir: str, model_id: str) -> str` |
| RES-08 | Envíos | 1 por día por equipo; máx. 60; último el 30 nov 2026 23:55 UTC (Codabench) |
| RES-09 | Visibilidad | Solo se ve *Finished/Failed* y la puntuación; ninguna salida del código |
| RES-10 | Juego limpio | Datos externos solo públicos y citados; prohibido manipular al juez |
| RES-11 | Equipo | Máx. 4 miembros; registro y equipos hasta el 1 nov 2026 |

## 1.8 Hitos

| Fecha | Hito | Entregable técnico |
|---|---|---|
| 1 nov 2026 | Cierre de registro | Equipo inscrito; E0 enviado como referencia |
| 8 nov 2026 | E1-E2 listos | Paquete `dsqa` con ingesta e índices; banco local con recall@5 |
| 15 nov 2026 | E3-E4 listos | Reranker, verificación con umbrales, PoT, reloj global |
| 22 nov 2026 | E5-E6 listos | OWA, q-FCM, calibración CMA-ES, ablación leave-one-out |
| 30 nov 2026 | Último envío | Mejor configuración enviada con margen de tiempo |
| Dic 2026 | Fase 2 (si se clasifica) | Paper IEEE de 4 páginas con resultados y figuras |
