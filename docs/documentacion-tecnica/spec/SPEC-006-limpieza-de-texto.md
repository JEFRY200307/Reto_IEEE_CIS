# SPEC-006: Limpieza de texto

**Módulo:** `dsqa/ingest/clean.py` · **Estrategia:** E1 · **Prioridad:** S
**Requisitos:** RF-IN-06 · **Criterios:** CA-IN-03

## Propósito
Quitar el ruido de extracción sin perder información técnica.

## Interfaz
```python
def clean_doc(doc: ExtractedDoc, steps: list[str]) -> ExtractedDoc: ...
```

## Comportamiento (cada paso es activable)
1. `ftfy`: reparar codificación y ligaduras (`ﬁ` → `fi`).
2. `dehyphen`: unir `palabra-\nresto` cuando `palabraresto` es una palabra en minúsculas; conservar guiones legítimos (`Be-7`, `RQ-Kmeans`).
3. `headers`: quitar líneas que se repiten en ≥ 50 % de las páginas (encabezados, pies, números de página).
4. `references`: cortar el texto desde el último encabezado "References" / "Bibliography" de la segunda mitad del documento.
5. `whitespace`: normalizar espacios y saltos de línea múltiples.

## Reglas y casos borde
- No cambia números, unidades ni símbolos matemáticos.
- Si el corte de referencias eliminaría > 50 % del texto, no se aplica.
- Documentos de 1 página: no se aplica `headers`.

## Configuración
| Clave | Por defecto |
|---|---|
| `ingest.clean_steps` | `[ftfy, dehyphen, headers, references, whitespace]` (E1+), `[]` (E0) |

## Errores y respaldo
- Un paso que lanza una excepción se omite para ese documento y se registra.

## Pruebas
- `"tempera-\nture"` → `"temperature"`; `"Be-\n7"` se conserva como `"Be-7"`.
- Encabezado repetido en 10 de 10 páginas → eliminado.
- Sección "References" al final → eliminada; "References" en la página 2 de 20 → no se corta.
