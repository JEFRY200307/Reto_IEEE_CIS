# E2: Recuperación híbrida

[← E1](E1-preparacion-optimizada.md) · [Visión general](../02-estrategia-vision-general.md) · Siguiente: [E3 →](E3-recuperacion-dos-fases.md)

## Objetivo

Combinar la **recuperación léxica (BM25)** con la **densa**, y fusionar sus resultados con **RRF**. Además, procesar la consulta para corregir erratas y expandir siglas.

## Por qué

| Buscador | Fuerte en | Débil en |
|---|---|---|
| BM25 | Siglas, isótopos, valores, nombres propios ("ICS", "Be-7", "RQ-Kmeans") | Paráfrasis y sinónimos |
| Denso | Significado y paráfrasis | Términos raros o muy técnicos |

En IFMIF-DONES abundan los términos exactos; en AI Papers importan más la semántica y los nombres de métodos. Sus errores son complementarios.

## Qué cambia respecto de E1

| Subetapa | E1 | E2 |
|---|---|---|
| 1f Índices | FAISS | FAISS **+ BM25** (`rank-bm25`) |
| 1g Recursos offline | — | **Glosario de siglas de DONES** (ICS → Impurity Control System, HEBT, TIR, etc.) preparado desde literatura pública |
| 2a Consulta | Original | **Expansión con glosario** + **corrección de erratas** (`rapidfuzz` contra el vocabulario del corpus) |
| 2b Buscadores | Denso | **BM25 + denso**, top-50 cada uno |
| 2c Fusión | — | **RRF** |

## Fusión RRF

Para cada chunk $d$ y cada buscador $r$ con rango $\text{rank}_r(d)$:

$$
\text{RRF}(d) = \sum_{r \in \{\text{BM25}, \text{denso}\}} \frac{1}{k + \text{rank}_r(d)}, \qquad k = 60
$$

Un chunk que aparece arriba en ambas listas queda primero. Usa solo el rango, no la magnitud del puntaje.

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| BM25 recupera chunks con siglas y valores que el denso pierde | Recall@5 mayor, sobre todo en DONES |
| La fusión supera a cada buscador por separado | Recall@5 de la fusión mayor que el de BM25 y el del denso |
| El costo de tiempo es casi nulo | Aumento de tiempo por pregunta < 1 s |

**Éxito:** más recall@5 y más precisión, especialmente en DONES.

## Cómo se mide

- Recall@5 de tres configuraciones en local: solo BM25, solo denso, híbrido con RRF.
- Resultados separados por dominio.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| BM25 empeora AI Papers | Revisar por dominio; ajustar después con E5 |
| La corrección de erratas "corrige" términos válidos | Umbral de similitud alto; solo palabras ausentes del vocabulario |
| El glosario no cubre siglas del corpus real | Ampliarlo con siglas detectadas en los PDF públicos |

## Referencias

- [3] Robertson y Zaragoza, BM25.
- [4] Cormack et al., RRF.
