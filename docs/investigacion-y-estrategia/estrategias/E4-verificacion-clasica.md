# E4: Verificación clásica

[← E3](E3-recuperacion-dos-fases.md) · [Visión general](../02-estrategia-vision-general.md) · Siguiente: [E5 →](E5-fusion-difusa.md)

## Objetivo

Agregar la **etapa 3 (verificación de la evidencia)**: antes de armar el contexto, juzgar si lo recuperado permite responder y actuar en consecuencia. En E4 el decisor usa **umbrales fijos**, al estilo de CRAG. Es la referencia necesaria para medir después el aporte de la versión difusa (E6).

## Por qué

En un RAG sin verificación, el LLM confía en lo recuperado aunque sea un distractor y responde con seguridad algo equivocado. Verificar da una segunda oportunidad a las preguntas cuya primera búsqueda falló, sin penalizar a las fáciles.

**Distinción:** se verifica la **evidencia recuperada**, no la respuesta generada.

## Qué cambia respecto de E3

### 3a. Señales (todas de costo casi nulo)

| Señal | Qué mide |
|---|---|
| $s_1$: puntaje del reranker del top-1 | Relevancia máxima |
| $s_2$: brecha top-1 − top-2 | Si hay un ganador claro o un empate |
| $s_3$: acuerdo BM25-denso | Solapamiento de sus top-10 |
| $s_4$: cobertura de entidades | % de términos clave de la pregunta presentes en la evidencia |

### 3b. Decisor con umbrales fijos

| Veredicto | Condición (valores iniciales a calibrar) |
|---|---|
| Correcta | $s_1 \geq \tau_{alto}$ y $s_4 \geq \kappa$ |
| Incorrecta | $s_1 < \tau_{bajo}$ |
| Ambigua | Cualquier otro caso |

### 3c. Acciones

| Veredicto | Acción |
|---|---|
| Correcta | Pasar a la etapa 4 |
| Ambigua | Filtrar oraciones irrelevantes + añadir chunks vecinos + subir k |
| Incorrecta | Reformular la consulta (glosario, multi-consulta) + quitar el filtro por documento + **1 reintento** |
| Sigue incorrecta | Responder con la mejor evidencia disponible (**nunca abstenerse**: el juez no premia el "no sé") |
| Pregunta numérica (cantidades o unidades) | Generar con **Program of Thoughts**: OLMo escribe Python, se ejecuta y se usa el resultado |

### Control de recursos

**Reloj global:** si el tiempo acumulado supera ~50 min, se pasa a modo rápido (sin reintento ni PoT, contexto mínimo).

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| El reintento recupera preguntas con evidencia débil | Mayor precisión en el subconjunto de preguntas reintentadas |
| PoT mejora las preguntas de cálculo | Mayor precisión en preguntas numéricas |
| El costo se concentra en pocas preguntas | Aumento de tiempo total acotado (fijar tolerancia antes) |

## Cómo se mide

- % de preguntas por veredicto (correcta / ambigua / incorrecta).
- Precisión antes y después del reintento en esas preguntas.
- Comparación pregunta por pregunta frente a E3 (McNemar).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El reintento reemplaza buena evidencia por peor | Conservar la mejor evidencia de ambos intentos |
| Umbrales mal elegidos (muchos o pocos reintentos) | Calibrarlos en el banco local |
| El código PoT falla o es inseguro | Ejecución con límite de tiempo y fallback a respuesta directa |

## Referencias

- [5] Yan et al., CRAG.
- [14] Chen et al., Program of Thoughts.
