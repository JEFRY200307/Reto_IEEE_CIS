# SPEC-021: Acciones de verificación y reintento

**Módulo:** `dsqa/verify/actions.py` · **Estrategia:** E4 · **Prioridad:** M
**Requisitos:** RF-VE-06..08 · **Criterios:** CA-VE-04, CA-VE-05 · **ADR:** ADR-08, ADR-12

## Propósito
Actuar según el veredicto para mejorar la evidencia antes de construir el contexto.

## Interfaz
```python
@dataclass
class Evidence:
    candidates: list[Candidate]; verdict: Verdict; attempt: int; refined: bool

def run_verification(query: Query, res: Resources, cfg: Config, decider: Decider) -> Evidence: ...
```

## Comportamiento
1. Intento 0: buscar → fusionar → rerank → señales → decidir.
2. Según el veredicto:
   - **correct:** devolver la evidencia.
   - **ambiguous:** marcar `refined=True`: subir `max_chunks` en 2, añadir vecinos ±1 y filtrar oraciones con baja coincidencia léxica con la pregunta.
   - **incorrect** (y modo `NORMAL` y `attempt < max_retries`): reformular ([SPEC-012](SPEC-012-analisis-de-consulta.md)), buscar **sin** filtro por documento y repetir desde el paso 1 con `attempt+1`.
3. Si tras los intentos sigue `incorrect`: devolver la evidencia con mayor `confidence` entre todos los intentos.
4. Registrar señales, pertenencias y acción de cada intento en la traza.

## Reglas y casos borde
- Máximo `max_retries` = 1.
- En modo `FAST`/`EMERGENCY`, `incorrect` no reintenta.
- Nunca devuelve evidencia vacía si algún intento tuvo candidatos.

## Configuración
| Clave | Por defecto |
|---|---|
| `verify.enabled` | `false` (E0-E3), `true` (E4+) |
| `verify.max_retries` | 1 |
| `verify.ambiguous_extra_chunks` | 2 |

## Errores y respaldo
- Error en el reintento → se conserva la evidencia del intento 0.

## Pruebas
- Decisor simulado que devuelve `incorrect` dos veces → exactamente un reintento y se elige la evidencia de mayor confianza.
- Modo `FAST` → sin reintento.
- `ambiguous` → contexto con vecinos.
