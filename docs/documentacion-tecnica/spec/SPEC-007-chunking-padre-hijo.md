# SPEC-007: Chunking (fijo y padre-hijo)

**Módulo:** `dsqa/ingest/chunk.py` · **Estrategia:** E0 (fijo), E1+ (por sección) · **Prioridad:** M
**Requisitos:** RF-IN-10..13 · **Criterios:** CA-IN-04

## Propósito
Dividir cada documento en fragmentos aptos para buscar (hijos) y para leer (padres).

## Interfaz
```python
class Chunker(Protocol):
    def chunk(self, doc: ExtractedDoc) -> list[Chunk]: ...
```

## Comportamiento
**`FixedChunker` (E0):** agrupa párrafos hasta ~800 caracteres con 150 de solape, cortando en límites de párrafo.

**`SectionChunker` (E1+):**
1. Detecta secciones por encabezados numerados (`1.`, `2.3`, `IV.`) o en mayúsculas.
2. Cada sección se divide en **padres** de hasta `parent_chars` en límites de párrafo.
3. Cada padre se divide en **hijos** de `child_chars` con `overlap` de solape; cada hijo apunta a su padre (`parent_id`).
4. Las tablas y los captions son chunks propios (`kind="table"` / `"caption"`), sin padre.

## Reglas y casos borde
- Sin secciones detectadas → división recursiva por párrafo (respaldo).
- Un párrafo más largo que `child_chars` se corta por oraciones.
- `chunk_id` secuencial y estable para el mismo corpus.
- Se descartan hijos de menos de 50 caracteres.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `ingest.chunker` | `section` | `fixed` / `section` |
| `ingest.child_chars` | 600 | 200-2000 |
| `ingest.parent_chars` | 2000 | ≥ `child_chars` |
| `ingest.overlap` | 100 | 0-500 |

## Errores y respaldo
- Error en `SectionChunker` → `FixedChunker` para ese documento.

## Pruebas
- Documento con 3 secciones → hijos con `parent_id` válido y sección correcta.
- Documento sin encabezados → respaldo sin error.
- Tabla → un chunk `kind="table"`.
