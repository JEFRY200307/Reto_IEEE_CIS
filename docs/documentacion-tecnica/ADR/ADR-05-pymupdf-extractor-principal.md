# ADR-05: PyMuPDF en paralelo como extractor principal

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Ingesta · **Relacionado:** RF-IN-02..04, [SPEC-005](../spec/SPEC-005-extraccion-pdf.md)

## Contexto
El baseline RAG con Docling tarda ~36 min en indexar y responder 50 preguntas, y Docling es la parte más lenta. Los PDF tienen texto nativo.

## Decisión
Desde E1, PyMuPDF extrae el texto por página con un pool de procesos. pdfplumber se usa solo en páginas con tablas. Docling queda disponible solo para reproducir E0.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Docling para todo | Demasiado lento para el límite |
| pypdf | Peor orden de lectura en columnas |
| OCR | Los PDF tienen texto nativo; costo alto |

## Consecuencias
- Positivas: ingesta mucho más rápida.
- Negativas: PyMuPDF puede desordenar tablas o columnas; se mitiga con pdfplumber y revisando muestras a mano.
- Verificación: CA-IN-02 y CA-IN-05.
