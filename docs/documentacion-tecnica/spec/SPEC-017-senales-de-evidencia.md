# SPEC-017: Señales de evidencia $s_1$-$s_4$

**Módulo:** `dsqa/verify/signals.py` · **Estrategia:** E4 · **Prioridad:** M
**Requisitos:** RF-VE-01 · **Criterios:** CA-VE-01 · **ADR:** ADR-08

## Propósito
Describir con números baratos de calcular qué tan buena es la evidencia recuperada.

## Interfaz
```python
def compute_signals(query: Query, ranked: list[Candidate], lists: dict[str, list[Candidate]],
                    chunks: list[Chunk]) -> Signals: ...
```

## Comportamiento
| Señal | Cálculo | Rango |
|---|---|---|
| $s_1$ relevancia | `rerank` del top-1 (ya en [0,1]) | [0,1] |
| $s_2$ claridad | `rerank(top1) − rerank(top2)`; con un solo candidato, $s_1$ | [0,1] |
| $s_3$ acuerdo | Jaccard entre los top-10 de BM25 y denso; si falta un buscador, 0,5 | [0,1] |
| $s_4$ cobertura | Fracción de `query.key_terms` presentes (coincidencia exacta o `rapidfuzz` ≥ 90) en el texto de los top-3 | [0,1] |

`s5_judge` queda en `None` (lo rellena [SPEC-018](SPEC-018-juez-olmo-s5.md)).

## Reglas y casos borde
- Lista vacía → todas las señales en 0.
- Sin términos clave → $s_4 = 0{,}5$ (neutro).
- Nunca devuelve NaN.

## Configuración
| Clave | Por defecto |
|---|---|
| `verify.signals` | `[s1, s2, s3, s4]` (E4-E5) |
| `verify.agreement_topk` | 10 |
| `verify.coverage_topk` | 3 |

## Errores y respaldo
- Error en una señal → valor neutro 0,5 y registro.

## Pruebas
- Todas las señales en [0,1] para entradas aleatorias (prueba de propiedades).
- Un solo candidato → $s_2$ definido.
- Listas idénticas → $s_3 = 1$; disjuntas → 0.
