# SPEC-015: Fusión difusa OWA (CI 1)

**Módulo:** `dsqa/retrieval/fusion.py` · **Estrategia:** E5 · **Prioridad:** M
**Requisitos:** RF-FU-02, RF-FU-03 · **Criterios:** CA-FU-02 · **Specs relacionadas:** [SPEC-029](SPEC-029-calibracion-cmaes.md)

## Propósito
Combinar los puntajes (no solo los rangos) de BM25 y denso como grados de pertenencia a "relevante", controlando cuánto se premia el acuerdo.

## Interfaz
```python
class OWA(Fusion):
    def __init__(self, params: OWAParams): ...

@dataclass
class OWAParams:
    norm: Literal["minmax", "zscore"]
    a: dict[str, float]; c: dict[str, float]   # pendiente y centro por buscador
    w: list[float]                              # pesos de posición, suman 1
```

## Comportamiento
1. Por buscador $r$, normalizar los puntajes de sus candidatos: $\hat s_r(d)$.
2. Pertenencia: $\mu_r(d) = \sigma(a_r(\hat s_r(d) - c_r))$. Si el candidato no está en la lista de $r$, $\mu_r(d) = 0$.
3. Ordenar las pertenencias de cada candidato de mayor a menor: $b_1 \ge b_2$.
4. $\text{OWA}(d) = \sum_j w_j b_j$.
5. Ordenar por OWA (empate por `chunk_id`) y devolver el top-`top_n` con `scores["fused"]`.

## Reglas y casos borde
- `w` debe sumar 1 (± 1e-6) y tener tantos pesos como buscadores; si no, error al cargar la config.
- Todos los puntajes iguales en un buscador → $\hat s_r = 0{,}5$ para todos.
- Con un solo buscador, OWA = su pertenencia.

## Configuración
| Clave | Por defecto |
|---|---|
| `fusion.method` | `owa` (E5+) |
| `fusion.owa_params` | `resources/owa_params.json` |

Valores iniciales (antes de calibrar): `norm=minmax`, `a=8`, `c=0.5` para ambos, `w=[0.4, 0.6]` (sesgo hacia el acuerdo).

## Errores y respaldo
- Archivo de parámetros ausente o inválido → valores iniciales y aviso en la traza.

## Pruebas
- `w=[1,0]` → máximo; `w=[0,1]` → mínimo; `w=[0.5,0.5]` → promedio.
- `w` que no suma 1 → error al cargar.
- Costo < 50 ms para 100 candidatos.
