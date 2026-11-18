# SPEC-001: Interfaz `answer()`

**Módulo:** `submission/main.py` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-IF-01..05, RF-RT-07 · **Criterios:** CA-IF-01, CA-IF-02, CA-IF-05 · **ADR:** ADR-03

## Propósito
Cumplir el contrato de Codabench y aislar al sistema de cualquier excepción.

## Interfaz
```python
def answer(question: str, corpus_dir: str, model_id: str) -> str: ...
```

## Comportamiento
1. Al importar: fijar `HF_HUB_OFFLINE=1` y `TRANSFORMERS_OFFLINE=1` (sin pisar valores existentes), añadir la carpeta de `main.py` a `sys.path` e importar `dsqa.runtime.clock` (arranca el reloj).
2. En cada llamada: delegar en `dsqa.runtime.safety.safe_answer(question, corpus_dir, model_id, root)`.
3. Devolver el `str` resultante.

## Reglas y casos borde
- `main.py` no contiene lógica del pipeline: menos de 30 líneas.
- Si `question` no es `str` (p. ej. `None`), se convierte con `str()` antes de seguir.
- Todas las rutas son relativas a `Path(__file__).resolve().parent`.
- No se imprime nada en `stdout` (Codabench no lo muestra y puede ralentizar).

## Configuración
Ninguna. `config.yaml` se busca junto a `main.py`.

## Errores y respaldo
- Cualquier excepción que escape de `safe_answer` se captura aquí y se devuelve la respuesta de nivel N4 ([SPEC-004](SPEC-004-degradacion-y-respaldo.md)).

## Pruebas
- Firma exacta con `inspect.signature`.
- Entradas extremas: vacía, 10 000 caracteres, LaTeX, Unicode, `None`, `corpus_dir` inexistente → siempre `str` no vacío.
- Importar `main.py` no carga `torch` ni modelos (tiempo de importación < 2 s).
