# E5: Fusión difusa (CI 1)

[← E4](E4-verificacion-clasica.md) · [Visión general](../02-estrategia-vision-general.md) · Siguiente: [E6 →](E6-verificacion-qfcm.md)

## Objetivo

Reemplazar la fusión RRF por una **agregación difusa OWA**. Es la **primera contribución de Inteligencia Computacional**. Solo cambia la subetapa 2c; todo lo demás es igual a E4.

## Por qué

- Los puntajes de BM25 y del denso son **inconmensurables** (escalas distintas) e **inciertos**. La lógica difusa existe para modelar ese tipo de evidencia.
- RRF usa solo el rango e ignora cuánto mejor es un candidato que otro.
- OWA permite controlar cuánto se premia el **acuerdo** entre buscadores.

## Qué cambia respecto de E4

| Subetapa | E4 | E5 |
|---|---|---|
| 2c Fusión | RRF | **OWA** |

## Formulación

**1. Puntajes a pertenencias.** Para cada buscador $r$, normalizar su puntaje sobre los candidatos y aplicar una función de pertenencia a "relevante":

$$
\mu_r(d) = \text{sigmoide}\big(a_r \cdot (\hat{s}_r(d) - c_r)\big)
$$

donde $\hat{s}_r(d)$ es el puntaje normalizado (min-max o z-score), y $a_r$, $c_r$ controlan la pendiente y el centro.

**2. Agregación OWA.** Ordenar las pertenencias de cada chunk de mayor a menor ($b_1 \geq b_2$) y combinarlas con pesos de posición:

$$
\text{OWA}(d) = \sum_{j} w_j \, b_j, \qquad \sum_j w_j = 1
$$

| Pesos | Comportamiento |
|---|---|
| $w = (1, 0)$ | Máximo: basta con que un buscador lo considere relevante |
| $w = (0, 1)$ | Mínimo: exige que ambos coincidan |
| $w = (0{,}5;\ 0{,}5)$ | Promedio |

Los pesos se fijan inicialmente cerca del promedio con sesgo hacia el acuerdo, y se calibran en E6.

**3. Candidatos fusionados.** Se toma el top-50 según $\text{OWA}(d)$ y se pasa al reranker.

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| OWA ordena mejor que RRF los candidatos antes del reranker | Recall@50 y recall@5 mayores |
| El costo es nulo | Sin cambio de tiempo medible |

**Éxito:** supera a RRF o iguala con una ventaja demostrable (por ejemplo, mejor en un dominio).

## Cómo se mide

- Recall@50 (entrada al reranker) y recall@5 (salida) frente a E4.
- **Leave-one-out:** comparar RRF y OWA **sin reranker**, para ver si el reranker absorbe la diferencia.
- Resultados por dominio.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El jurado lo ve como "un promedio con otro nombre" | Justificar con la incertidumbre de las evidencias; considerar la versión dinámica (ver abajo) |
| La diferencia frente a RRF desaparece tras el reranker | Reportarlo como resultado; medir sin reranker |
| Funciones de pertenencia mal calibradas | Calibrar $a_r$, $c_r$ y $w$ con CMA-ES (E6) |

## Mejora opcional registrada

**Fusión difusa dinámica:** que los pesos $w$ dependan de pertenencias difusas al dominio y al tipo de pregunta (por ejemplo, más peso a BM25 en preguntas de DONES con siglas). Alternativa técnica: integral de Choquet, que modela la interacción entre buscadores. El reto lista "fusión dinámica de conocimiento" como línea de investigación. No adoptada por ahora.

## Referencias

- [6] Yager, OWA.
- [4] Cormack et al., RRF (baseline).
