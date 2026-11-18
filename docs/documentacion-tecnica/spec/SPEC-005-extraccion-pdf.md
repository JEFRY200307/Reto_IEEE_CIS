# SPEC-005: Extracción de PDF

**Módulo:** `dsqa/ingest/extract.py` · **Estrategia:** E0 (Docling), E1+ (PyMuPDF) · **Prioridad:** M
**Requisitos:** RF-IN-01..05, RF-IN-07, RF-IN-08 · **Criterios:** CA-IN-01, CA-IN-02, CA-IN-05 · **ADR:** ADR-05

## Propósito
Convertir cada PDF de `corpus_dir` en páginas de texto con metadatos.

## Interfaz
```python
class Extractor(Protocol):
    def extract(self, path: Path) -> ExtractedDoc: ...   # páginas + título + abstract + captions

def list_pdfs(corpus_dir: str) -> list[Path]: ...         # recursivo, orden estable
def extract_all(paths: list[Path], extractor: Extractor, workers: int) -> list[ExtractedDoc]: ...
```

## Comportamiento
1. `list_pdfs` recorre la carpeta de forma recursiva, filtra `.pdf` (sin distinguir mayúsculas) y ordena por ruta.
2. `PyMuPDFExtractor`: `page.get_text("text", sort=True)` por página; detecta páginas con tablas (`page.find_tables()`) y en esas usa pdfplumber para obtener las tablas como texto tabular separado por `|`.
3. Título: metadato del PDF si es plausible (> 10 caracteres); si no, la línea de fuente más grande de la página 1.
4. Abstract: texto tras el encabezado "Abstract" en las 2 primeras páginas (máx. 2 000 caracteres).
5. Captions: líneas que empiezan con "Fig.", "Figure", "Table" seguidas de número.
6. `DoclingExtractor` (E0): Docling a Markdown con `do_ocr=False`, `do_table_structure=False`.
7. `extract_all` usa un pool de procesos con tiempo máximo por documento.

## Reglas y casos borde
- `doc_id` = hash corto (SHA-1, 12 caracteres) de la ruta relativa: estable entre ejecuciones.
- PDF cifrado, corrupto, sin texto (< 200 caracteres en total) o que excede el tiempo → se omite y se registra.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `ingest.extractor` | `pymupdf` | `pymupdf` / `docling` |
| `ingest.tables` | `true` | bool |
| `ingest.doc_timeout_s` | 60 | 5-600 |
| `ingest.workers` | 30 | 1-64 |

## Errores y respaldo
- Error en pdfplumber en una página → se queda el texto de PyMuPDF de esa página.

## Pruebas
- Mini-corpus con PDF válido, cifrado, vacío y truncado → 1 extraído, 3 omitidos.
- Orden y `doc_id` estables en dos ejecuciones.
- Tiempo PyMuPDF < Docling sobre el corpus del banco.
