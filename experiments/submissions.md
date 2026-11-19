# Registro de envíos a Codabench

Una fila por envío (máx. 1 por día). Ver §7.5 de la documentación técnica.

| Fecha (UTC) | Config | Commit / tag | Cambio / hipótesis | Estado | Precisión | Tiempo (s) | Notas |
|---|---|---|---|---|---|---|---|
| 2026-11-18 | e1 (`dsqa-E1-optimized-prep-v1`), ID 1058805 | `50476d3` / `sub-2026-11-18-e1` | Primer envío: base segura (PyMuPDF, padre-hijo, bge-base, top-5, prompts por dominio) | Finished | 46,670 | (pendiente) | Referencia para E2-E6. Sin BM25, reranker, verificación ni CI |
| 2026-11-19 | e2 (`dsqa-E2-hybrid-rrf-v1`), ID 1059606 | zip `dsqa_e2_2026-11-18` | E1 + BM25 + RRF + glosario + corrección de erratas | Finished | 38,100 | (pendiente) | Baja 8,57 pts frente a E1 pese a mejor recall local (r@5 30 % vs 25 %). No se añadió al leaderboard; queda E1 |
