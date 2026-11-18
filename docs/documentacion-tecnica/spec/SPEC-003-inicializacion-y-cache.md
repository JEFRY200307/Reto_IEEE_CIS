# SPEC-003: Inicialización perezosa, paralela y caché

**Módulo:** `dsqa/runtime/state.py` · **Estrategia:** Todas (paralelismo desde E1) · **Prioridad:** M
**Requisitos:** RF-RT-02, RF-RT-03, RF-IF-04, RF-IX-05 · **Criterios:** CA-IF-04 · **ADR:** ADR-03, ADR-04

## Propósito
Construir una sola vez todo lo costoso (modelo, índices, modelos auxiliares) y compartirlo entre preguntas.

## Interfaz
```python
@dataclass
class Resources:
    llm: LLM | None; tokenizer: Any | None
    chunks: list[Chunk]; documents: dict[str, Document]
    dense: DenseIndex | None; lexical: LexicalIndex | None; titles: TitleIndex | None
    reranker: Reranker | None
    init_errors: list[str]

def get_or_init(corpus_dir: str, model_id: str, cfg: Config, root: Path) -> Resources: ...
```

## Comportamiento
1. Si ya existe un `Resources` para `(corpus_dir, model_id)`, devolverlo.
2. Si no:
   1. Lanzar un hilo que carga OLMo ([SPEC-023](SPEC-023-generacion-olmo.md)).
   2. En paralelo: extraer ([SPEC-005](SPEC-005-extraccion-pdf.md)) → limpiar → dividir → enriquecer con un `ProcessPoolExecutor`.
   3. Al terminar la ingesta: construir BM25 y títulos (CPU) y el índice denso (GPU).
   4. Esperar al hilo de OLMo.
   5. Cargar el reranker si la config lo pide.
3. Cada paso va dentro de `CLOCK.stage(...)`.
4. Guardar `Resources` en una variable global del módulo.

## Reglas y casos borde
- Cada componente que falla queda en `None` y su error se anota en `init_errors`; no se reintenta en cada pregunta.
- Si `corpus_dir` no existe o no tiene PDFs, los índices quedan vacíos (el sistema responde en N3, zero-shot).
- Número de procesos de ingesta: `min(cpu_count, cfg.ingest.workers)`.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `ingest.workers` | 30 | 1-64 |
| `runtime.parallel_init` | `true` | bool |

## Errores y respaldo
- Error al cargar OLMo → `llm=None`; `safe_answer` usará N4.
- Error en el índice denso → `dense=None`; la búsqueda sigue solo con BM25 (N2).

## Pruebas
- Tres llamadas → la inicialización se ejecuta una vez (contador con LLM simulado).
- Fallo inyectado en el embedder → `dense is None`, `init_errors` no vacío y las preguntas se responden.
- Con `parallel_init=false` se obtiene el mismo `Resources` (comparar chunks).
