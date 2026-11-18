# SPEC-030: Evaluación local y estadística

**Módulo:** `eval/run_local.py`, `eval/retrieval_metrics.py`, `eval/judge.py`, `eval/stats.py`, `eval/report.py` · **Estrategia:** Todas · **Prioridad:** M
**Requisitos:** RF-EV-01..08, RNF-RP-03 · **Criterios:** CA-EV-01, CA-EV-02

## Propósito
Medir y comparar configuraciones de forma reproducible, sin depender de Codabench.

## Interfaz
```bash
# Varias configs en un solo proceso, reutilizando OLMo cargado
python eval/run_local.py --configs configs/e3.yaml configs/e4.yaml --bench eval/bench/ \
    --corpus data/public_pdfs/ --model-id allenai/Olmo-3.1-32B-Instruct \
    --out experiments/runs/2026-11-10-s04/ --resume [--sync-s3 s3://<bucket>/runs/]
python eval/retrieval_metrics.py --run experiments/runs/<...>/e3 --k 1 5 50
python eval/judge.py --run experiments/runs/<...>/e3 --backend olmo|manual|file
python eval/stats.py --a experiments/runs/<...>/e3 --b experiments/runs/<...>/e4
python eval/report.py --runs experiments/runs/ --out experiments/report/
```

## Comportamiento
1. **`run_local`:** por cada config, construye `Resources` (reutilizando el `LLM` entre configs) y llama `answer()` exactamente como Codabench. Escribe por pregunta una línea en `answers.jsonl` y una traza en `traces.jsonl` **en cuanto termina**.
2. **`--resume`:** omite las preguntas que ya están en `answers.jsonl` (permite continuar tras una interrupción spot).
3. **`--sync-s3`:** sube los archivos de resultados cada 5 min y al terminar (`aws s3 sync`).
4. **Métricas de recuperación:** recall@k, MRR por dominio usando el gold de [SPEC-028](SPEC-028-banco-local-y-qa-sintetico.md); no necesita LLM.
5. **Juez local:** veredicto binario de la respuesta frente a la referencia. Backends: `olmo` (prompt de comparación estricta), `manual` (CSV para revisión humana) o `file` (veredictos ya hechos). Se valida contra revisión manual en las 25 preguntas de muestra.
6. **Precisión balanceada:** misma fórmula que el reto.
7. **Estadística:** McNemar exacto pregunta por pregunta; IC 95 % por bootstrap (10 000 remuestreos).
8. **Reporte:** tabla de ablación E0-E6 y leave-one-out por dominio, tiempos por etapa, % de reintentos, figura del q-FCM.

## Reglas y casos borde
- Cada ejecución guarda `config_resolved.yaml`, commit y lista de preguntas.
- El juez local **no** es el juez oficial; sus números solo sirven para comparar.

## Errores y respaldo
- Error en una pregunta → se anota y se continúa con la siguiente.

## Pruebas
- D = 3/10 y P = 9/15 → $A = 0{,}45$.
- McNemar coincide con `scipy` en casos conocidos.
- Interrumpir a mitad y relanzar con `--resume` → mismo resultado final.
