# SPEC-025: Configuración y estrategias

**Módulo:** `dsqa/runtime/config.py`, `configs/` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-CF-01..03 · **Criterios:** CA-CF-01, CA-CF-02 · **ADR:** ADR-02

## Propósito
Definir cada estrategia y cada ablación como datos validados, sin cambiar código.

## Interfaz
```python
class Config(pydantic.BaseModel):   # model_config = {"extra": "forbid"}
    strategy: str
    runtime: RuntimeCfg; ingest: IngestCfg; index: IndexCfg; retrieval: RetrievalCfg
    fusion: FusionCfg; rerank: RerankCfg; verify: VerifyCfg; context: ContextCfg; generate: GenerateCfg

def load_config(path: Path) -> Config: ...            # resuelve `extends` y valida
def resolve_to_file(path: Path, out: Path) -> None: ...  # escribe la config sin herencia (para el zip)
def diff_blocks(a: Config, b: Config) -> set[str]: ...   # bloques que cambian entre dos configs
```

## Comportamiento
1. `load_config` lee el YAML; si tiene `extends`, carga primero el padre (de forma recursiva) y fusiona en profundidad (el hijo gana).
2. Valida con `pydantic`: claves desconocidas, tipos y rangos.
3. Validaciones cruzadas: `t_emergency > t_fast`, pesos OWA que suman 1, `tau_low < tau_high`, archivos de recursos existentes.
4. `diff_blocks` permite comprobar que cada salto E(N-1) → EN cambia solo los bloques documentados.

### Mapa de estrategias
| Archivo | Hereda de | Bloques que cambia |
|---|---|---|
| `e0.yaml` | `base.yaml` | Todo (baseline del kit) |
| `e1.yaml` | `e0.yaml` | `ingest`, `index`, `context`, `generate`, `runtime` |
| `e2.yaml` | `e1.yaml` | `retrieval`, `fusion` (rrf) |
| `e3.yaml` | `e2.yaml` | `retrieval` (filtro), `rerank`, `context` |
| `e4.yaml` | `e3.yaml` | `verify` (umbrales), `generate` (PoT), `runtime` (modos) |
| `e5.yaml` | `e4.yaml` | `fusion` (owa) |
| `e6.yaml` | `e5.yaml` | `verify` (qfcm + s5) |

Las ablaciones leave-one-out viven en `configs/ablations/` y heredan de `e6.yaml`.

## Reglas y casos borde
- Herencia circular → error.
- Los textos que parecen booleanos van entre comillas (`"Yes"`).

## Errores y respaldo
- Config inválida → error en la construcción del zip ([SPEC-026](SPEC-026-empaquetado-y-chequeo.md)), nunca en Codabench.
- En tiempo de ejecución, si `config.yaml` falta o es inválido, se usan los valores por defecto de E1 y se registra.

## Pruebas
- Clave mal escrita → error que nombra la clave.
- `diff_blocks(e4, e5) == {"fusion"}`.
- Herencia de 3 niveles resuelve correctamente.
