# SPEC-013: Búsqueda y filtro documento → pasaje

**Módulo:** `dsqa/retrieval/search.py` · **Estrategia:** Todas (búsqueda), E3 (filtro) · **Prioridad:** M
**Requisitos:** RF-RE-01, RF-RE-02 · **Criterios:** CA-RE-01

## Propósito
Ejecutar los buscadores activos y, si la pregunta nombra un documento con confianza, restringir la búsqueda a él.

## Interfaz
```python
def search(query: Query, res: Resources, cfg: Config, use_doc_filter: bool = True) -> dict[str, list[Candidate]]:
    """Devuelve {"bm25": [...], "dense": [...]} con los buscadores activos."""
```

## Comportamiento
1. Texto de búsqueda = `normalized` + `expansions`.
2. Si `use_doc_filter` y `query.named_doc` tiene confianza ≥ `doc_filter_threshold` → `doc_filter = {doc_id}`; si no, `None`.
3. Ejecutar cada buscador activo con `top_k` y el filtro.
4. **Filtro blando:** si con el filtro un buscador devuelve menos de `min_hits` candidatos, completar con una búsqueda global.
5. Devolver un diccionario por buscador.

## Reglas y casos borde
- Buscador desactivado o no disponible (`None`) → no aparece en el diccionario.
- Ningún buscador disponible → diccionario vacío (el contexto quedará vacío y se usa zero-shot).

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `retrieval.retrievers` | `[dense]` (E0-E1), `[bm25, dense]` (E2+) | lista |
| `retrieval.top_k` | 50 | 5-200 |
| `retrieval.doc_filter_threshold` | 0.7 | 0-1 |
| `retrieval.min_hits` | 5 | 1-50 |

## Errores y respaldo
- Error en un buscador → se omite y se registra; los demás siguen.

## Pruebas
- Confianza 0,5 con umbral 0,7 → búsqueda global.
- Confianza 0,9 → todos los candidatos del documento.
- Documento con 2 chunks y `min_hits=5` → se completa con búsqueda global.
