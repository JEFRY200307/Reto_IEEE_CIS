# SPEC-008: Enriquecimiento y dominio del documento

**Módulo:** `dsqa/ingest/enrich.py` · **Estrategia:** E1 · **Prioridad:** M
**Requisitos:** RF-IN-09, RF-IN-14 · **Criterios:** CA-IN-04

## Propósito
Dar a cada chunk el contexto de su documento y estimar el dominio del documento.

## Interfaz
```python
def enrich(chunks: list[Chunk], doc: Document) -> list[Chunk]: ...
def document_domain(doc: ExtractedDoc, lexicon: DomainLexicon) -> dict[str, float]: ...
```

## Comportamiento
1. `enrich`: antepone `"<título> | <sección>\n"` al texto que se indexa de cada chunk y copia `doc_id`, página, sección, tipo y dominio.
2. `document_domain`: cuenta términos de dos léxicos (DONES: *lithium loop, deuteron, accelerator, IFMIF, target, neutron…*; IA: *neural, dataset, transformer, learning, benchmark…*) en título + abstract + primeras 2 páginas y devuelve pertenencias normalizadas `{"DONES": μ, "AI": μ}` con `μ ∈ [0,1]`.

## Reglas y casos borde
- El texto entregado al LLM es el del padre **sin** el prefijo repetido; el prefijo solo sirve para buscar.
- Si ninguna pertenencia supera 0,3, el dominio es `UNKNOWN` (p. ej. distractores médicos).

## Configuración
| Clave | Por defecto |
|---|---|
| `ingest.enrich` | `true` (E1+), `false` (E0) |
| `ingest.domain_lexicon` | `resources/domain_lexicon.json` |

## Errores y respaldo
- Sin título → se usa el nombre del archivo.

## Pruebas
- Chunk enriquecido empieza con título y sección.
- Abstract de un paper de DONES → `μ_DONES > μ_AI`; un paper de IA → al revés; un paper de medicina → `UNKNOWN`.
