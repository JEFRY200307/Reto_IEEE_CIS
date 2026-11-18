# E3: Recuperación en dos fases

[← E2](E2-recuperacion-hibrida.md) · [Visión general](../02-estrategia-vision-general.md) · Siguiente: [E4 →](E4-verificacion-clasica.md)

## Objetivo

Filtrar los distractores del corpus con dos mecanismos:

1. **Filtro jerárquico documento → pasaje:** identificar primero el documento relevante (muy útil cuando la pregunta nombra un paper).
2. **Reordenamiento con cross-encoder:** releer pregunta + pasaje juntos y quedarse con los mejores.

Y ajustar la **selección del contexto** a la calidad de la evidencia.

## Por qué

- El corpus incluye **documentos distractores** y hay **homónimos** (por ejemplo, dos papers distintos llamados ZeroDiff y dos REVEL).
- Las preguntas de AI Papers suelen nombrar el paper o el método.
- El buscador rápido (fase 1) es barato pero impreciso; el cross-encoder (fase 2) es preciso pero caro, por eso solo revisa los 50 candidatos.

## Qué cambia respecto de E2

| Subetapa | E2 | E3 |
|---|---|---|
| 1f Índices | FAISS + BM25 | + **índice de títulos** (título y abstract de cada documento) |
| 2a Consulta | Glosario + erratas | + **detección del paper nombrado** (BM25 + `rapidfuzz` sobre títulos) |
| 2b Buscadores | BM25 + denso | + **filtro doc → pasaje blando**: si la confianza en el documento es alta, se busca dentro de él; si no, búsqueda global |
| 2d Reranker | No | **bge-reranker-base** sobre el top-50 fusionado + **MMR** para evitar pasajes redundantes |
| 4 Contexto | Top-5, máx. 4k | **Umbral sobre el puntaje del reranker** (entre 3 y 8 chunks) + **chunks vecinos ±1** |

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| El filtro por documento elimina distractores en AI Papers | Recall@5 mayor en Papers |
| El reranker mejora el orden en ambos dominios | Recall@1 y recall@5 mayores |
| El umbral adapta la cantidad de contexto a la evidencia | Menos tokens promedio sin perder precisión |

**Éxito:** más recall@5 y más precisión, con un aumento de tiempo de pocos segundos por pregunta.

## Cómo se mide

- Recall@1 y recall@5 con y sin reranker, y con y sin filtro por documento (en local, CPU).
- Tiempo del reranker por pregunta.
- Precisión con juez local y envío a Codabench.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El filtro elige el documento equivocado | Filtro blando con umbral de confianza; fallback a búsqueda global |
| El reranker general no entiende física nuclear | Comparar frente a E2 por dominio; alternativa MiniLM más liviana |
| Espacio: bge-base (~440 MB) + bge-reranker-base (~550 MB fp16) ≈ 1 GB | Verificar con `du -sh`; alternativas bge-small (~130 MB) o reranker MiniLM (~90 MB) |

## Referencias

- [12] Nogueira y Cho, reranking con cross-encoder.
- [11] Liu et al., Lost in the middle (orden y tamaño del contexto).
- [13] Xiao et al., C-Pack (bge-reranker).
