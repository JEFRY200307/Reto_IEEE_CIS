# SPEC-020: Decisor q-FCM (CI 2)

**Módulo:** `dsqa/verify/qfcm.py` · **Estrategia:** E6 · **Prioridad:** M
**Requisitos:** RF-VE-04, RF-VE-05, RF-VE-08 · **Criterios:** CA-VE-03 · **ADR:** ADR-09, ADR-10

## Propósito
Combinar las señales de forma no lineal e interpretable con un mapa cognitivo difuso cuasi-no lineal, y producir pertenencias difusas a cada veredicto.

## Interfaz
```python
@dataclass
class QFCMParams:
    phi: float                 # ∈ [0,1]
    W: np.ndarray              # 6×6, w_ij ∈ [-1,1]
    lam: float                 # pendiente de la sigmoide
    iterations: int
    out_mf: dict[str, tuple]   # funciones de pertenencia de C6: incorrect / ambiguous / correct

class QFCMDecider(Decider):
    def __init__(self, params: QFCMParams): ...
    def decide(self, s: Signals) -> Verdict: ...
    def activations(self, s: Signals) -> np.ndarray: ...   # para trazas y figuras
```

## Comportamiento
1. $A^{(0)} = [s_1, s_2, s_3, s_4, s_5, 0]$ (si $s_5$ es `None`, se usa 0,5).
2. Iterar $A^{(t+1)} = \varphi \, \sigma_\lambda(A^{(t)} W) + (1-\varphi) A^{(0)}$ durante `iterations` pasos o hasta que $\lVert A^{(t+1)} - A^{(t)} \rVert_\infty < 10^{-4}$.
3. La activación final de $C_6$ (confianza) se evalúa en tres funciones de pertenencia trapezoidales → `memberships`.
4. Veredicto = la pertenencia más alta; `confidence` = activación de $C_6$.

### Pesos iniciales de experto (antes de calibrar)
| Desde → $C_6$ | Signo | Rango permitido | Razón |
|---|---|---|---|
| $C_1$ relevancia | + | [0,4; 0,9] | Un buen pasaje top-1 es la mejor evidencia |
| $C_2$ claridad | + | [0,1; 0,5] | Un ganador claro reduce el riesgo de distractores |
| $C_3$ acuerdo | + | [0,1; 0,5] | Coincidencia de dos buscadores independientes |
| $C_4$ cobertura | + | [0,2; 0,7] | Baja cobertura indica que falta información |
| $C_5$ juez OLMo | + | [0,3; 0,8] | Señal semántica, acotada por el sesgo del LLM |

Las demás conexiones son 0, salvo $C_1 \to C_5$ (+, [0; 0,3]), que modela que un pasaje relevante refuerza la suficiencia.

## Reglas y casos borde
- $\varphi = 1$ → FCM clásico; $\varphi = 0$ → $A = A^{(0)}$.
- Pesos fuera de rango en el JSON → error al cargar.

## Configuración
| Clave | Por defecto |
|---|---|
| `verify.decider` | `qfcm` (E6) |
| `verify.qfcm.params_file` | `resources/qfcm_params.json` |
| `verify.qfcm.iterations` | 10 |

## Errores y respaldo
- Parámetros ausentes → pesos de experto con $\varphi = 0{,}7$ y aviso.
- Error durante la inferencia → `ThresholdDecider` con valores por defecto.

## Pruebas
- Casos límite de $\varphi$ (0 y 1).
- Señales todas en 1 → `correct`; todas en 0 → `incorrect`.
- Costo < 1 ms por pregunta.
- Exportar el grafo con los pesos (para la figura del paper).
