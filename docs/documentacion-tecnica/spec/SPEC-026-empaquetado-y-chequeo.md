# SPEC-026: Empaquetado y chequeo del envío

**Módulo:** `scripts/build_submission.py`, `scripts/check_submission.py` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-EM-01..04, RNF-RC-01/02, RNF-PO-01 · **Criterios:** CA-EM-01, CA-EM-02, CA-RT-05 · **ADR:** ADR-13

## Propósito
Generar un zip válido para Codabench y detectar cualquier problema **antes** de gastar el envío del día.

## Interfaz (línea de comandos)
```bash
python scripts/build_submission.py --config configs/e6.yaml --out dist/
python scripts/check_submission.py dist/dsqa_e6_2026-11-22.zip [--smoke --model-id <modelo-pequeño> --corpus <carpeta>]
```

## Comportamiento
**build:**
1. Cargar y validar la config ([SPEC-025](SPEC-025-configuracion-y-estrategias.md)) y escribirla resuelta como `config.yaml`.
2. Copiar `submission/main.py` a la raíz, `src/dsqa/` a `dsqa/` (sin `__pycache__`, `*.pyc` ni pruebas).
3. Copiar solo los recursos y modelos que la config referencia.
4. Escribir `BUILD_INFO.json`: commit (`git rev-parse HEAD`), si hay cambios sin commit, fecha UTC, config, tamaño por carpeta.
5. Comprimir y nombrar `dsqa_<estrategia>_<AAAA-MM-DD>.zip`.

**check:**
1. `main.py` existe en la raíz del zip.
2. Tamaño descomprimido ≤ 950 MB (avisa desde 900 MB).
3. Análisis de imports (`ast`) de todos los `.py`: cada módulo de terceros está en `requirements-runtime.txt`.
4. `config.yaml` válido.
5. Ningún archivo con ruta absoluta en su contenido de config.
6. Con `--smoke`: descomprimir en una carpeta temporal limpia, bloquear la red, importar `main` y llamar `answer()` con 5 preguntas del banco; todas deben devolver `str` no vacío.

## Reglas y casos borde
- Si hay cambios sin commit, `build` avisa y lo anota en `BUILD_INFO.json` (no bloquea, pero el chequeo previo al envío exige un commit etiquetado).

## Errores y respaldo
- `check` termina con código distinto de 0 y un mensaje por cada fallo.

## Pruebas
- Zip con `main.py` en subcarpeta → falla.
- Zip de 960 MB → falla.
- `import vllm` en un módulo → falla nombrando el archivo.
