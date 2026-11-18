# SPEC-009: Índice denso

**Módulo:** `dsqa/index/dense.py` · **Estrategia:** E0 (MiniLM CPU), E1+ (bge-base GPU) · **Prioridad:** M
**Requisitos:** RF-IX-01, RF-IX-02, RF-IX-05 · **Criterios:** CA-IX-02 · **ADR:** ADR-13

## Propósito
Recuperar chunks por similitud semántica con la pregunta.

## Interfaz
```python
class DenseIndex:
    @classmethod
    def build(cls, chunks: list[Chunk], model_dir: Path, device: str, batch: int) -> "DenseIndex": ...
    def search(self, query: str, k: int, doc_filter: set[str] | None = None) -> list[Candidate]: ...
```

## Comportamiento
1. Carga el embedder desde `models/embedder/` con `sentence-transformers` (fp16 en GPU).
2. Codifica los chunks hijo en lotes, normaliza (L2) y los guarda en `faiss.IndexFlatIP`.
3. Para bge, la consulta lleva la instrucción `"Represent this sentence for searching relevant passages: "`.
4. `search` devuelve los `k` mejores con su puntaje `dense` y rango.
5. Con `doc_filter`, busca sobre el subconjunto de ese documento (producto interno sobre los vectores en memoria).

## Reglas y casos borde
- Corpus vacío → índice vacío; `search` devuelve `[]`.
- `k` mayor que el número de chunks → devuelve todos.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `index.embedder` | `models/embedder` | ruta |
| `index.device` | `cuda` | `cuda` / `cpu` |
| `index.batch_size` | 256 | 8-1024 |
| `index.query_instruction` | (la de bge) | texto |

## Errores y respaldo
- Sin GPU disponible → CPU. Error al cargar el modelo → `dense=None` (nivel N2).

## Pruebas
- Buscar con el texto exacto de un chunk → top-1.
- Vectores con norma 1 (± 1e-3).
- Filtro por documento devuelve solo chunks de ese documento.
