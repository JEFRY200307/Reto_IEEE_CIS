# SPEC-012: Análisis de la consulta

**Módulo:** `dsqa/retrieval/query.py` · **Estrategia:** E2 (glosario, erratas, dominio), E3 (paper nombrado), E4 (numérica, términos clave, reformulación) · **Prioridad:** M
**Requisitos:** RF-CO-01..07 · **Criterios:** CA-CO-01..04 · **Specs relacionadas:** [SPEC-011](SPEC-011-indice-de-titulos.md), [SPEC-027](SPEC-027-glosario-dones.md)

## Propósito
Convertir la pregunta en un objeto `Query` con todo lo que necesitan la búsqueda y la verificación.

## Interfaz
```python
def analyze(question: str, res: Resources, cfg: Config) -> Query: ...
def reformulate(query: Query, res: Resources) -> list[str]: ...   # consultas para el reintento
```

## Comportamiento
1. **Normalizar:** `ftfy`, espacios, quitar `$` y comandos LaTeX simples (`\text{}`) conservando su contenido.
2. **Erratas** (E2): por cada palabra fuera de `lexical.vocabulary` y del vocabulario en inglés, buscar la más parecida del vocabulario con `rapidfuzz` (ratio ≥ 90); reemplazar solo en `normalized`.
3. **Glosario** (E2): por cada sigla del glosario presente en la pregunta, añadir su expansión a `expansions`.
4. **Dominio** (E2): pertenencias `{"DONES": μ, "AI": μ}` con los léxicos de [SPEC-008](SPEC-008-enriquecimiento-y-dominio.md) + coincidencias del glosario.
5. **Paper nombrado** (E3): `named_doc = titles.match(question)[0]` si existe.
6. **Numérica** (E4): `True` si la pregunta pide cantidad, valor, tasa, constante, volumen, temperatura, "how many/much", o contiene números con unidades.
7. **Términos clave** (E4): sustantivos y entidades (spaCy si hay modelo empaquetado; si no, tokens BM25 sin stopwords, con siglas y números).
8. **Reformulación** (E4): pregunta + expansiones; versión solo con términos clave; versión sin el nombre del paper.

## Reglas y casos borde
- Nunca se modifica `original`.
- Las siglas válidas presentes en el vocabulario no se corrigen.

## Configuración
| Clave | Por defecto |
|---|---|
| `retrieval.glossary` | `resources/glossary_dones.json` (E2+) |
| `retrieval.typo_fix` | `true` (E2+) |
| `retrieval.typo_threshold` | 90 |
| `retrieval.detect_paper` | `true` (E3+) |

## Errores y respaldo
- Cualquier paso que falle deja su campo con el valor neutro (lista vacía, `None`, `False`).

## Pruebas
- "ICS Branch" → expansión "Impurity Control System".
- "volumen" → "volume"; "ICS" no cambia.
- Pregunta 3 de muestra → `is_numeric=True`; pregunta 2 → `False`.
