# SPEC-004: Cadena de degradación N0-N4

**Módulo:** `dsqa/runtime/safety.py` · **Estrategia:** E1 · **Prioridad:** M
**Requisitos:** RF-IF-02, RF-RT-05, RF-RT-06 · **Criterios:** CA-IF-02, CA-IF-03, CA-RT-03 · **ADR:** ADR-12

## Propósito
Garantizar que cada pregunta reciba un `str` útil aunque falle cualquier parte del sistema.

## Interfaz
```python
def safe_answer(question: str, corpus_dir: str, model_id: str, root: Path) -> str: ...
```

## Comportamiento
1. Cargar la config (una vez) y obtener `Resources` ([SPEC-003](SPEC-003-inicializacion-y-cache.md)).
2. Elegir el nivel de partida según el modo del reloj y los recursos disponibles:

| Nivel | Pipeline | Se usa si |
|---|---|---|
| N0 | Completo según la config | Modo `NORMAL` o `FAST` y todo disponible |
| N1 | Sin verificación ni PoT, contexto top-3 | Error en N0 |
| N2 | Solo BM25 top-3 + respuesta corta | Error en N1, sin índice denso o modo `EMERGENCY` |
| N3 | Zero-shot con el prompt del dominio | Sin índices |
| N4 | Texto fijo construido con la pregunta | Sin LLM |

3. Ejecutar el nivel; ante una excepción, registrarla y bajar un nivel.
4. Ante `torch.cuda.OutOfMemoryError`: `torch.cuda.empty_cache()` y repetir el **mismo** nivel con la mitad del presupuesto de contexto (una sola vez).
5. Validar la salida: si no es `str` o queda vacía tras `strip()`, bajar un nivel.

## Reglas y casos borde
- N4 devuelve una frase no vacía que reutiliza los términos clave de la pregunta. No es una abstención explícita.
- Nunca relanza excepciones.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `runtime.oom_context_factor` | 0.5 | 0.1-0.9 |

## Errores y respaldo
Es el respaldo del sistema; no tiene respaldo propio salvo el `try/except` de `main.py`.

## Pruebas
- Fallo inyectado en cada etapa → nivel esperado y `str` no vacío.
- OOM simulado → un reintento con contexto menor.
- Salida vacía del LLM → baja de nivel.
