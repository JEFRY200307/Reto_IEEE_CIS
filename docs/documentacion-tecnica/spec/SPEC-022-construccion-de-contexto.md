# SPEC-022: Construcción del contexto

**Módulo:** `dsqa/context/builder.py` · **Estrategia:** Todas (reglas por estrategia) · **Prioridad:** M
**Requisitos:** RF-CX-01..05 · **Criterios:** CA-CX-01, CA-CX-02

## Propósito
Decidir qué texto lee OLMo: qué pasajes, cuántos, en qué orden y con qué formato, sin pasar el presupuesto de tokens.

## Interfaz
```python
def build_context(evidence: Evidence, res: Resources, cfg: Config, mode: Mode) -> tuple[str, int]:
    """Devuelve (contexto, tokens)."""
```

## Comportamiento
1. **Selección:**
   - E0: candidatos en orden hasta ~10 000 tokens.
   - E1-E2: top-5.
   - E3+: candidatos con `rerank ≥ min_score`, con un mínimo de `min_chunks` y un máximo de `max_chunks`.
2. **Expansión** (E1+): reemplazar cada hijo por su **padre**; si `neighbors > 0`, añadir los chunks vecinos ±1 del mismo documento.
3. **Deduplicar** padres repetidos (dos hijos con el mismo padre → un solo pasaje).
4. **Ordenar:** el más relevante primero.
5. **Formato:** `[Doc: <título>, p. <página>]\n<texto>` separados por una línea en blanco.
6. **Presupuesto:** contar tokens con el tokenizador de OLMo; quitar pasajes desde el final hasta cumplir `max_tokens`; si un único pasaje lo supera, truncarlo.

## Reglas y casos borde
- Modo `FAST`: máximo 3 pasajes; `EMERGENCY`: máximo 3 pasajes de BM25.
- Sin evidencia → contexto vacío y 0 tokens.

## Configuración
| Clave | E0 | E1-E2 | E3+ |
|---|---|---|---|
| `context.max_tokens` | 10000 | 4000 | 6000 |
| `context.min_chunks` | — | 5 | 3 |
| `context.max_chunks` | — | 5 | 8 |
| `context.min_score` | — | — | 0.3 |
| `context.neighbors` | 0 | 0 | 1 |
| `context.use_parent` | `false` | `true` | `true` |

## Errores y respaldo
- Error del tokenizador → estimación con 4 caracteres por token y un margen del 10 %.

## Pruebas
- Contexto ≤ `max_tokens` en todo el banco.
- Cada pasaje empieza con `[Doc: …, p. N]`.
- Dos hijos del mismo padre → un pasaje.
