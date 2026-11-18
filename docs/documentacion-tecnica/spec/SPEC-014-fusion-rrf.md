# SPEC-014: Fusión RRF

**Módulo:** `dsqa/retrieval/fusion.py` · **Estrategia:** E2-E4 · **Prioridad:** M
**Requisitos:** RF-FU-01 · **Criterios:** CA-FU-01

## Propósito
Combinar las listas de los buscadores usando solo los rangos.

## Interfaz
```python
class Fusion(Protocol):
    def fuse(self, lists: dict[str, list[Candidate]], top_n: int) -> list[Candidate]: ...

class RRF(Fusion):
    def __init__(self, k: int = 60): ...

class NoFusion(Fusion): ...   # E0-E1: devuelve la única lista
```

## Comportamiento
$$\text{RRF}(d) = \sum_{r} \frac{1}{k + \text{rank}_r(d)}$$

1. Para cada candidato presente en alguna lista, sumar $1/(k + \text{rank})$ de cada lista donde aparece (rangos desde 1).
2. Ordenar de mayor a menor; en empate, por `chunk_id` (determinismo).
3. Guardar el puntaje en `scores["fused"]` y conservar los puntajes originales.

## Reglas y casos borde
- Un candidato ausente de una lista no suma nada por ella.
- Una sola lista → mismo orden que esa lista.

## Configuración
| Clave | Por defecto |
|---|---|
| `fusion.method` | `none` (E0-E1), `rrf` (E2-E4) |
| `fusion.rrf_k` | 60 |
| `fusion.top_n` | 50 |

## Errores y respaldo
Función pura; no falla con entradas válidas.

## Pruebas
- Dos listas de 3 elementos → puntajes iguales al cálculo manual (tolerancia 1e-9).
- Empates resueltos por `chunk_id`.
