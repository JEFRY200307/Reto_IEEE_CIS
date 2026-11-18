# E6: Verificación con q-FCM (CI 2 y 3), propuesta final

[← E5](E5-fusion-difusa.md) · [Visión general](../02-estrategia-vision-general.md)

## Objetivo

Reemplazar los umbrales fijos de la verificación (E4) por un **mapa cognitivo difuso cuasi-no lineal (q-FCM)** que combina las señales de evidencia, incluida una señal semántica del propio OLMo, y decide la acción. Sus parámetros se **calibran offline con CMA-ES**.

Contiene dos contribuciones de CI:
- **CI 2:** decisión con q-FCM.
- **CI 3:** calibración evolutiva.

## Por qué

- Las categorías correcta / ambigua / incorrecta de CRAG son **naturalmente difusas**; los cortes duros pierden información.
- El q-FCM combina señales de forma **no lineal e interpretable** (el grafo se puede mostrar en el paper).
- La regla cuasi-no lineal evita el problema del FCM sigmoide clásico, que converge a un punto fijo único y "olvida" la evidencia de entrada.
- Los pesos se pueden fijar con **conocimiento experto, sin datos de entrenamiento**, lo que es clave con solo 25 preguntas de muestra.

## Qué cambia respecto de E5

| Subetapa | E5 | E6 |
|---|---|---|
| 3a Señales | $s_1$ a $s_4$ | + **$s_5$: juez OLMo** |
| 3b Decisor | Umbrales fijos | **q-FCM** |
| Calibración | Manual | **CMA-ES offline** |

## Señal nueva: juez OLMo ($s_5$)

Una sola pasada de OLMo, **sin generar texto**, con el prompt:

```
Pregunta: <pregunta>
Evidencia: <top-3 chunks>
¿La evidencia contiene la información necesaria para responder? Responde Sí o No.
```

$$
s_5 = \frac{P(\text{"Sí"})}{P(\text{"Sí"}) + P(\text{"No"})} \in [0, 1]
$$

El valor funciona directamente como grado de pertenencia. Es la idea de "decisiones con probabilidad calibrada" (como los *System One models* tipo Jev), implementada con el modelo fijo. Su juicio **no decide solo**: es una entrada más del q-FCM, porque los LLM tienden a sobreestimar si la evidencia alcanza.

## Formulación del q-FCM

**Conceptos:**

| Concepto | Tipo | Valor inicial $A^{(0)}$ |
|---|---|---|
| $C_1$ Relevancia (reranker top-1) | Entrada | $s_1$ normalizado |
| $C_2$ Claridad (brecha top-1/top-2) | Entrada | $s_2$ normalizado |
| $C_3$ Acuerdo entre buscadores | Entrada | $s_3$ |
| $C_4$ Cobertura de entidades | Entrada | $s_4$ |
| $C_5$ Suficiencia semántica (juez OLMo) | Entrada | $s_5$ |
| $C_6$ Confianza en la evidencia | Salida | 0 |

**Regla de razonamiento cuasi-no lineal:**

$$
A^{(t+1)} = \varphi \, f\!\left(A^{(t)} W\right) + (1 - \varphi) \, A^{(0)}, \qquad f = \text{sigmoide}, \quad \varphi \in [0, 1]
$$

- $W$: matriz de pesos causales $w_{ij} \in [-1, 1]$, inicializada con conocimiento experto (por ejemplo, relevancia y suficiencia semántica → confianza con peso positivo alto; baja cobertura → confianza con peso negativo).
- $\varphi$: controla cuánta evidencia inicial se conserva. Con $\varphi = 1$ se recupera el FCM clásico.
- Iteraciones: ~10 (costo despreciable).

**Decisión:** la activación final de $C_6$ se mapea a pertenencias difusas a **correcta / ambigua / incorrecta**, que activan las mismas acciones de E4.

## Calibración con CMA-ES (offline)

| Elemento | Detalle |
|---|---|
| Variables | $\varphi$, pesos de $W$ (dentro de rangos de experto), funciones de pertenencia de salida, pesos OWA de E5 |
| Función objetivo | Precisión en el banco local (25 de muestra + QA sintético) |
| Control del sobreajuste | Validación cruzada; pesos restringidos a intervalos de experto |
| Dónde corre | Offline, antes del envío; solo se envían los parámetros finales |

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| El q-FCM decide mejor que los umbrales cuándo reintentar | Mayor precisión que E5, o igual con menos reintentos |
| El juez OLMo aporta información que las señales numéricas no tienen | Leave-one-out: quitar $s_5$ reduce la precisión |
| El sistema sigue dentro del tiempo | Público < ~45-50 min |

## Cómo se mide

- Comparación pregunta por pregunta frente a E5 (McNemar).
- Leave-one-out de cada señal y del q-FCM completo.
- Comparación frente a una **regresión logística** sobre las mismas señales (alternativa no difusa).
- Figura del grafo del q-FCM con sus pesos finales para el paper.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Sobreajuste por pocas preguntas | QA sintético, validación cruzada, intervalos de experto |
| La pasada extra de OLMo aumenta el tiempo | Contexto corto (top-3) en el juez; desactivar en modo rápido |
| Los pesos de experto se perciben como arbitrarios | Documentar el razonamiento de cada peso; mostrar los valores calibrados |
| No supera a los umbrales | Reportarlo; destacar la interpretabilidad como aporte |

## Mejoras opcionales registradas

- **Pesos por intervalos** ($w_{ij} \in [l_{ij}, u_{ij}]$) con calibración restringida.
- **Calibración multiobjetivo** precisión-tiempo (NSGA-II o MO-CMA-ES) para obtener el frente de Pareto; el reto pide recursos realistas y el tiempo es el desempate.

## Referencias

- [7] Nápoles et al. 2022, regla cuasi-no lineal (núcleo).
- [8] Wu et al., EC + LLM (núcleo).
- [5] Yan et al., CRAG (verificación).
- [9] Kosko, FCM.
- [10] Hansen, CMA-ES.
- [15] Nápoles et al. 2025, FCM sin datos de entrenamiento.
- [16] Zheng et al., LLM-as-a-judge.
