# ADR-02: Cada estrategia E0-E6 es un archivo YAML sobre el mismo código

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Configuración · **Relacionado:** RF-CF-01..03, [SPEC-025](../spec/SPEC-025-configuracion-y-estrategias.md)

## Contexto
La investigación compara 7 estrategias con ablación incremental y leave-one-out. Cada salto debe cambiar **un solo bloque** del pipeline. Duplicar código por estrategia hace imposible garantizarlo.

## Decisión
Un único paquete `dsqa` con componentes que se activan por configuración. Cada estrategia es `configs/eN.yaml` y hereda (`extends`) de la anterior. La config se valida con `pydantic` y viaja resuelta (sin herencia) dentro del zip.

### Por qué YAML
- `pyyaml` está preinstalado en el entorno de Codabench, así que no añade dependencias.
- Admite comentarios (JSON no), útiles para justificar umbrales en el paper.
- Se lee y se compara con `diff` fácilmente entre estrategias.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| Una carpeta de código por estrategia | Duplicación; no garantiza que solo cambie un bloque |
| JSON | Sin comentarios |
| `config.py` con diccionarios | Mezcla configuración y lógica |
| TOML | Válido, pero menos cómodo con anidación profunda |

## Consecuencias
- Positivas: ablación sin tocar código; reproducibilidad (la config viaja en el zip).
- Negativas: `pyyaml` interpreta `yes`/`no` sin comillas como booleanos, así que los textos van entre comillas.
- Verificación: CA-CF-01 y CA-CF-02.
