# SPEC-002: Reloj global y modos

**Módulo:** `dsqa/runtime/clock.py` · **Estrategia:** E1 (reloj), E4 (modos) · **Prioridad:** M
**Requisitos:** RF-RT-01, RF-RT-04 · **Criterios:** CA-RT-01 · **ADR:** ADR-07

## Propósito
Medir el tiempo desde el arranque del proceso y decidir en qué modo opera cada pregunta.

## Interfaz
```python
class Mode(Enum): NORMAL, FAST, EMERGENCY

class Clock:
    def elapsed(self) -> float: ...            # segundos desde la importación
    def mode(self) -> Mode: ...
    def remaining(self, limit_s: float) -> float: ...
    def stage(self, name: str) -> ContextManager: ...   # mide una etapa

CLOCK: Clock   # instancia única creada al importar
```

## Comportamiento
1. Guarda `time.monotonic()` al importarse.
2. `mode()`: `EMERGENCY` si `elapsed ≥ t_emergency`; si no, `FAST` si `elapsed ≥ t_fast`; si no, `NORMAL`.
3. `stage(name)` acumula la duración en un diccionario de tiempos por etapa (para la traza).
4. Los modos nunca retroceden: una vez en `FAST`, no se vuelve a `NORMAL`.

## Reglas y casos borde
- Usa `time.monotonic()`, no la hora del sistema.
- Se puede inyectar un reloj falso en las pruebas.

## Configuración
| Clave | Por defecto | Rango |
|---|---|---|
| `runtime.t_fast_s` | 3000 (50 min) | 600-6600 |
| `runtime.t_emergency_s` | 3360 (56 min) | > `t_fast_s` |

## Errores y respaldo
- Sin fallos posibles; si la config no trae valores, usa los de por defecto.

## Pruebas
- Reloj falso en 2999, 3001 y 3361 s → `NORMAL`, `FAST`, `EMERGENCY`.
- No retrocede de modo.
- `stage()` acumula correctamente en llamadas anidadas y repetidas.
