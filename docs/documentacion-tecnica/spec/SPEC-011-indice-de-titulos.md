# SPEC-011: Índice de títulos

**Módulo:** `dsqa/index/titles.py` · **Estrategia:** E3 · **Prioridad:** M
**Requisitos:** RF-IX-04, RF-CO-03 · **Criterios:** CA-CO-03

## Propósito
Identificar qué documento menciona la pregunta (papers o métodos con nombre propio).

## Interfaz
```python
class TitleIndex:
    @classmethod
    def build(cls, docs: list[Document]) -> "TitleIndex": ...
    def match(self, question: str, top: int = 3) -> list[tuple[str, float]]: ...   # (doc_id, confianza ∈ [0,1])
```

## Comportamiento
1. Por documento indexa título + abstract con BM25 y guarda los **nombres propios** del título (tokens con mayúsculas internas o siglas: `WinStat`, `ZeroDiff`, `REVEL`, `OneSearch`).
2. `match`:
   1. Coincidencia exacta o difusa (`rapidfuzz.fuzz.partial_ratio ≥ 90`) de nombres propios de la pregunta con los del título → confianza alta.
   2. BM25 sobre título + abstract, normalizado por el máximo.
   3. Confianza = combinación de ambas, en `[0,1]`.
3. Si los dos primeros documentos tienen confianza parecida (diferencia < `ambiguity_gap`), la confianza del primero se reduce (caso de homónimos, p. ej. dos ZeroDiff).

## Reglas y casos borde
- Pregunta sin nombres propios → confianza basada solo en BM25 (normalmente baja).

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `index.titles.fuzzy_threshold` | 90 | 70-100 |
| `index.titles.ambiguity_gap` | 0.1 | 0-0.5 |

## Errores y respaldo
- Error → `titles=None`; no se aplica el filtro por documento.

## Pruebas
- "WinStat window size for L = 512" con un documento "WinStat: …" → ese documento, confianza ≥ 0,8.
- Dos documentos con "ZeroDiff" en el título → confianza reducida.
