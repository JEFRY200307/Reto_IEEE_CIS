# SPEC-010: Índice BM25

**Módulo:** `dsqa/index/lexical.py` · **Estrategia:** E2 · **Prioridad:** M
**Requisitos:** RF-IX-03 · **Criterios:** CA-IX-01

## Propósito
Recuperar chunks por coincidencia exacta de términos técnicos (siglas, isótopos, valores, nombres de métodos).

## Interfaz
```python
def tokenize(text: str) -> list[str]: ...
class LexicalIndex:
    @classmethod
    def build(cls, chunks: list[Chunk], k1: float, b: float) -> "LexicalIndex": ...
    def search(self, query_tokens: list[str], k: int, doc_filter: set[str] | None = None) -> list[Candidate]: ...
    @property
    def vocabulary(self) -> set[str]: ...
```

## Comportamiento
1. `tokenize`: minúsculas; conserva tokens con guion o dígitos (`be-7`, `rq-kmeans`, `40mev`) y además emite su forma sin guion (`be7`); quita stopwords en inglés (NLTK, lista embebida); sin stemming agresivo.
2. `build`: `rank_bm25.BM25Okapi` sobre los chunks hijo.
3. `search`: puntajes BM25; top-`k` con puntaje `bm25` y rango.

## Reglas y casos borde
- Consulta sin tokens tras filtrar → `[]`.
- La lista de stopwords va dentro del paquete (no se descarga de NLTK en tiempo de ejecución).

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `index.bm25.k1` | 1.5 | 0.5-3 |
| `index.bm25.b` | 0.75 | 0-1 |

## Errores y respaldo
- Error al construir → `lexical=None`; la búsqueda sigue solo densa.

## Pruebas
- `"Be-7 inventory in the ICS"` → contiene `be-7`, `be7`, `inventory`, `ics`.
- Un chunk con "ICS bypass ratio" queda primero para la consulta "ICS bypass".
- `vocabulary` contiene los tokens del corpus.
