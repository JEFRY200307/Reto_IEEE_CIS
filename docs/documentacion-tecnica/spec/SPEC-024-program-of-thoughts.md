# SPEC-024: Program of Thoughts

**Módulo:** `dsqa/generate/pot.py` · **Estrategia:** E4 · **Prioridad:** M
**Requisitos:** RF-PT-01..04 · **Criterios:** CA-PT-01, CA-PT-02 · **ADR:** ADR-11

## Propósito
Resolver preguntas numéricas haciendo que OLMo escriba un cálculo en Python que se ejecuta de forma segura.

## Interfaz
```python
def solve(llm: LLM, question: str, context: str, timeout_s: float) -> PoTResult | None: ...

@dataclass
class PoTResult:
    code: str; value: str; stdout: str
```

## Comportamiento
1. Solo si `query.is_numeric` y modo `NORMAL`.
2. Prompt `pot`: "Write a short Python program that computes the answer using values from the context. Store the final result with its unit in a variable `answer`. Use only the `math` module."
3. Extraer el bloque de código de la respuesta.
4. **Validación estática** con `ast`: rechazar `import` distinto de `math`, `open`, `exec`, `eval`, `__import__`, atributos con doble guion bajo, `while` sin límite.
5. Ejecutar en un subproceso nuevo (`python -I`) con: `builtins` restringidos, sin variables de entorno, límite de memoria (`resource.setrlimit`, 512 MB) y `timeout_s`.
6. Leer `answer` (impreso como JSON por el envoltorio).
7. Generar la respuesta final con un prompt que incluye el resultado calculado: valor con unidades primero y una justificación breve.

## Reglas y casos borde
- Código rechazado, error, tiempo agotado o `answer` ausente → `None`, y se responde por la vía directa.
- El subproceso no hereda la GPU (`CUDA_VISIBLE_DEVICES=""`).

## Configuración
| Clave | Por defecto |
|---|---|
| `generate.pot.enabled` | `false` (E0-E3), `true` (E4+) |
| `generate.pot.timeout_s` | 5 |
| `generate.pot.max_new_tokens` | 256 |

## Errores y respaldo
Ver "Reglas": cualquier fallo vuelve a la generación directa.

## Pruebas
- `import os`, `open(...)`, `socket`, `while True` → bloqueado o cortado.
- Pregunta 3 de muestra con contexto correcto → ≈ 0,01308 día⁻¹ (± 1 %).
- Tiempo total del PoT < 10 s.
