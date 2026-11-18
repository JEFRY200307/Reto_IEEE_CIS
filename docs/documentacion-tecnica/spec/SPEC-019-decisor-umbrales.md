# SPEC-019: Decisor por umbrales

**Módulo:** `dsqa/verify/threshold.py` · **Estrategia:** E4-E5 · **Prioridad:** M
**Requisitos:** RF-VE-03 · **Criterios:** CA-VE-04 (vía acciones)

## Propósito
Clasificar la evidencia en correcta / ambigua / incorrecta con reglas fijas (referencia estilo CRAG para comparar con el q-FCM).

## Interfaz
```python
class Decider(Protocol):
    def decide(self, s: Signals) -> Verdict: ...

class ThresholdDecider(Decider):
    def __init__(self, tau_high: float, tau_low: float, kappa: float): ...

class NoVerify(Decider): ...   # E0-E3: siempre "correct"
```

## Comportamiento
| Veredicto | Condición |
|---|---|
| `correct` | $s_1 \ge \tau_{alto}$ y $s_4 \ge \kappa$ |
| `incorrect` | $s_1 < \tau_{bajo}$ |
| `ambiguous` | cualquier otro caso |

`memberships` = 1 para el veredicto elegido y 0 para los demás; `confidence` = $s_1$.

## Reglas y casos borde
- Requiere $\tau_{bajo} < \tau_{alto}$; si no, error al cargar la config.

## Configuración
| Clave | Por defecto (a calibrar) |
|---|---|
| `verify.decider` | `none` (E0-E3), `threshold` (E4-E5) |
| `verify.threshold.tau_high` | 0.7 |
| `verify.threshold.tau_low` | 0.3 |
| `verify.threshold.kappa` | 0.5 |

## Errores y respaldo
Función pura; no falla.

## Pruebas
- Tabla de verdad con valores en los bordes (= umbral).
- Config con $\tau_{bajo} \ge \tau_{alto}$ → error de validación.
