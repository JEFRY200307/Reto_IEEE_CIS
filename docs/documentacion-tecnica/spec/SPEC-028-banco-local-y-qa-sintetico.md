# SPEC-028: Banco local y QA sintético

**Módulo:** `offline/fetch_public_pdfs.py`, `offline/build_synthetic_qa.py`, `eval/bench/` · **Estrategia:** E1 (banco), E4 (sintético) · **Prioridad:** M
**Requisitos:** RF-OF-03, RF-OF-04, RNF-CU-02

## Propósito
Tener un conjunto propio de preguntas, respuestas y chunks correctos para comparar estrategias sin gastar envíos.

## Interfaz
```bash
python offline/fetch_public_pdfs.py --list eval/bench/pdf_list.csv --out data/public_pdfs/
python offline/build_synthetic_qa.py --pdfs data/public_pdfs/ --n 150 --out eval/bench/synthetic_qa.json
```

Formato de cada pregunta (compatible con `sample_qa.json`):
```json
{"id": "syn-042", "domain": "DONES", "question": "…", "question_type": "procedural",
 "answer": "…", "source_doc": "…pdf", "source_page": 7, "gold_text": "…"}
```

## Comportamiento
1. **Corpus público:** lista curada de PDFs de los sitios de `sites.txt` relacionados con las 25 preguntas de muestra (IFMIF-DONES en JACoW/EUROfusion; los papers de IA nombrados) + distractores de otros dominios. Se guardan URL y licencia.
2. **Gold de la muestra:** para las 25 preguntas oficiales, marcar a mano el pasaje que contiene la respuesta (`eval/bench/gold_chunks.json`, por texto, no por `chunk_id`, para que sobreviva a cambios de chunking).
3. **QA sintético:** con OLMo (en AWS), generar preguntas de los 5 tipos desde pasajes elegidos, con respuesta concisa y el pasaje de origen como gold. Proporción por dominio ≈ 50/50 y por tipo ≈ igual.
4. **Filtro de calidad:** descartar preguntas que se respondan sin contexto (zero-shot correcto) o cuya respuesta no esté en el pasaje; revisar a mano una muestra del 20 %.
5. **Particiones:** 5 particiones estratificadas por dominio y tipo (para la calibración) + un conjunto de prueba fijo.

## Reglas y casos borde
- Las 25 preguntas oficiales nunca se usan para generar sintéticas parecidas (evita fuga).
- El gold se resuelve a `chunk_id` en tiempo de evaluación por coincidencia de texto (`rapidfuzz` ≥ 85).

## Errores y respaldo
- PDF no descargable → se registra y se continúa.

## Pruebas
- Esquema JSON válido para todas las preguntas.
- Distribución por dominio y tipo dentro de ± 10 % del objetivo.
