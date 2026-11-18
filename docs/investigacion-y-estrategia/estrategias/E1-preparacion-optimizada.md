# E1: Preparación optimizada

[← E0](E0-base-estandar.md) · [Visión general](../02-estrategia-vision-general.md) · Siguiente: [E2 →](E2-recuperacion-hibrida.md)

## Objetivo

Mejorar la **preparación del corpus** (etapa 1) y la **salida** (etapas 4 y 5) sin tocar todavía la lógica de recuperación, que sigue siendo solo densa. Es un bloque de ingeniería sin riesgo conceptual; por eso se agrupa en una sola estrategia.

## Qué cambia respecto de E0

| Subetapa | E0 | E1 |
|---|---|---|
| 1a Extracción | Docling | **PyMuPDF en paralelo** (32 núcleos) + pdfplumber solo en páginas con tablas |
| 1b Limpieza | Ninguna | **ftfy** + unir palabras cortadas por guion + quitar encabezados y pies repetidos + quitar la sección de referencias |
| 1c Chunking | Fijo, 800 caracteres | **Por sección**, con estructura padre-hijo (se busca con el chunk pequeño y se entrega el párrafo padre) + **tablas como chunks aparte** |
| 1d Enriquecimiento | Ninguno | **Título del documento + sección** antepuestos a cada chunk + metadatos (doc_id, página, sección) + etiqueta de dominio |
| 1e Embeddings | MiniLM en CPU | **bge-base-en-v1.5 en GPU**, en batch, antes de cargar OLMo |
| 1f Índices | Coseno | FAISS Flat (exacto) |
| 4 Contexto | Hasta 10k tokens | **Top-5, máximo 4k tokens**, el más relevante primero, etiquetas `[Doc: título, p. X]` |
| 5 Generación | Genérica, 2048 tokens | **Prompt por dominio**, formato "dato clave primero + justificación breve", ≈300 tokens |
| Control | Caché del modelo | + caché global del índice; liberar memoria tras indexar |

## Hipótesis y criterio de éxito

| Hipótesis | Criterio |
|---|---|
| La ingesta con PyMuPDF en paralelo es mucho más rápida que Docling | Tiempo de indexado menor |
| Menos contexto y respuestas cortas reducen el tiempo por pregunta | Tiempo por pregunta menor |
| Chunks con título y sección se recuperan mejor | Recall@5 igual o mayor |
| Respuestas concisas se alinean mejor con el juez | Precisión igual o mayor |

**Éxito:** menos tiempo total **sin perder** precisión. Si además sube la precisión, mejor.

## Cómo se mide

- Recall@5 en local (laptop), sin OLMo.
- Tiempo por etapa frente a E0.
- Precisión con juez local y luego un envío a Codabench.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| PyMuPDF desordena tablas o columnas | pdfplumber en páginas con tablas; revisar a mano algunos PDF públicos |
| Detectar secciones falla en algunos PDF | Fallback a chunking recursivo por párrafo |
| bge-base en GPU compite por memoria con OLMo | Embeber antes de cargar OLMo y liberar memoria |
| Contexto de 4k deja fuera información útil | Comparar 4k frente a 8k en el banco local |

## Espacio en el zip

bge-base ≈ 440 MB.

## Referencias

- [11] Liu et al., Lost in the middle (contexto corto y orden).
- [13] Xiao et al., C-Pack (familia BGE).
