# SPEC-016: Reranking y MMR

**Módulo:** `dsqa/retrieval/rerank.py` · **Estrategia:** E3 · **Prioridad:** M
**Requisitos:** RF-RK-01, RF-RK-02 · **Criterios:** CA-RK-01 · **ADR:** ADR-13

## Propósito
Reordenar los candidatos fusionados leyendo pregunta y pasaje juntos, y evitar pasajes redundantes.

## Interfaz
```python
class Reranker:
    @classmethod
    def load(cls, model_dir: Path, device: str) -> "Reranker": ...
    def rerank(self, query: str, cands: list[Candidate], chunks: list[Chunk], top_n: int) -> list[Candidate]: ...

def mmr(cands: list[Candidate], embeddings: np.ndarray, lam: float, k: int) -> list[Candidate]: ...
```

## Comportamiento
1. Cargar el cross-encoder (`FlagEmbedding.FlagReranker`, fp16, GPU) desde `models/reranker/`.
2. Puntuar pares `(pregunta original, texto del chunk hijo)` en lotes; aplicar sigmoide → `scores["rerank"] ∈ [0,1]`.
3. Ordenar por `rerank`.
4. MMR sobre el top-`top_n`: elegir iterativamente el candidato que maximiza $\lambda \cdot \text{rerank} - (1-\lambda) \cdot \max \text{sim}(\text{elegidos})$, con la similitud coseno de los embeddings ya calculados.

## Reglas y casos borde
- Menos de 2 candidatos → sin MMR.
- Longitud máxima del par: 512 tokens (se trunca el pasaje).

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `rerank.enabled` | `false` (E0-E2), `true` (E3+) | bool |
| `rerank.model` | `models/reranker` | ruta |
| `rerank.top_n` | 20 | 5-50 |
| `rerank.mmr_lambda` | 0.7 | 0-1 |
| `rerank.batch_size` | 32 | 4-128 |

## Errores y respaldo
- Error al cargar o al puntuar → se conserva el orden de la fusión y `scores["rerank"]` = puntaje fusionado normalizado.

## Pruebas
- Dos duplicados casi idénticos → no aparecen ambos en el top-5 tras MMR.
- Tiempo de 50 candidatos en GPU < 2 s (en AWS).
