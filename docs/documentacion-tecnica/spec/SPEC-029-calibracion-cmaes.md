# SPEC-029: Calibración CMA-ES (CI 3)

**Módulo:** `offline/calibrate_cmaes.py` · **Estrategia:** E6 · **Prioridad:** M
**Requisitos:** RF-OF-05, RNF-RP-04 · **ADR:** ADR-10 · **Specs relacionadas:** [SPEC-015](SPEC-015-fusion-owa.md), [SPEC-020](SPEC-020-decisor-qfcm.md)

## Propósito
Ajustar los parámetros de OWA y del q-FCM dentro de rangos de experto, maximizando la precisión del banco local sin sobreajustar.

## Interfaz
```bash
python offline/calibrate_cmaes.py --cache experiments/runs/<sesion>/signal_cache.parquet \
    --target owa|qfcm|both --folds 5 --seed 42 --budget 2000 --out resources/
```

## Comportamiento
1. **Caché de señales (en AWS, una vez):** para cada pregunta del banco y cada intento posible, guardar puntajes BM25/denso por candidato, señales $s_1$-$s_5$ y el veredicto del juez local para la respuesta **con** y **sin** reintento. Así la calibración corre en la laptop sin GPU.
2. **Variables:** OWA (`a_r`, `c_r`, `w`) y q-FCM (`phi`, pesos no nulos de `W`, parámetros de las funciones de pertenencia de salida), codificados en `[0,1]` y mapeados a sus rangos de experto.
3. **Objetivo:** precisión balanceada por dominio simulada con la caché (la acción elegida determina qué veredicto cuenta), con una penalización pequeña por el porcentaje de reintentos (costo de tiempo).
4. **Optimización:** `cma.CMAEvolutionStrategy` con semilla fija y `budget` evaluaciones, validación cruzada de 5 particiones: se calibra en 4 y se mide en 1.
5. **Salida:** parámetros de la mejor configuración media en validación, más el historial y las métricas de calibración vs validación en `experiments/runs/…/cmaes_report.json`.

## Reglas y casos borde
- Ninguna variable puede salir de su rango de experto.
- Si la brecha calibración − validación supera 10 puntos, se guardan los pesos de experto en lugar de los calibrados y se informa.
- `cma` es una dependencia solo de `requirements-dev.txt`.

## Errores y respaldo
- Caché incompleta → error con la lista de preguntas faltantes.

## Pruebas
- Con una función objetivo sintética de óptimo conocido, CMA-ES lo encuentra (± 5 %).
- Misma semilla → mismos parámetros.
- Los parámetros exportados cargan sin error en `OWA` y `QFCMDecider`.
