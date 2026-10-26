# 6. Kit de inicio (Starter Kit)

**Fuente:** [github.com/jucls/IEEE-CIS-DSQA-Starter-Kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit) (licencia MIT)

## Qué incluye

- **Dataset de muestra:** 25 pares pregunta–respuesta de dificultad creciente, de los mismos dominios y con la misma metodología que el benchmark.
- **Modelo base fijo:** `OLMo 3.1 32B Instruct` ([`allenai/Olmo-3.1-32B-Instruct`](https://huggingface.co/allenai/Olmo-3.1-32B-Instruct)), disponible en el entorno de evaluación. Contexto máximo: 65 536 tokens.
- **Código de inicio** y scripts para construir y probar el envío.
- **Lista de sitios web** de donde se tomaron los documentos del corpus.

## Estructura del repositorio

```
IEEE-CIS-DSQA-Starter-Kit/
├── 01_zero_shot/
│   ├── build.sh          → genera ../01_zero_shot_submission.zip
│   └── main.py           → baseline sin recuperación
├── 02_rag/
│   ├── build.sh          → descarga modelos auxiliares y genera ../02_rag_submission.zip
│   └── main.py           → baseline RAG
├── sample/
│   ├── sample_qa.json    → 25 preguntas de ejemplo
│   └── sites.txt         → dominios fuente del corpus
├── requirements-participant.txt → versiones exactas del entorno de evaluación
├── LICENSE (MIT)
└── README.md
```

## Baseline 1 — `01_zero_shot`

Responde **solo con el conocimiento del modelo**, sin consultar el corpus. Es el **piso de referencia** que cualquier otro enfoque debe superar.

- Prompt de sistema: *"You are a scientific expert. Answer the following question as accurately and concisely as possible based on your knowledge."*
- Carga el modelo en `bfloat16` con `device_map="cuda"` y lo **cachea** en un diccionario global (`answer()` se llama una vez por pregunta en el mismo proceso).
- Decodificación greedy (`do_sample=False`), `max_new_tokens=2048`.
- El zip solo contiene `main.py`.

## Baseline 2 — `02_rag`

**Recuperación "a ciegas"** sobre todo el corpus (nada le dice de qué documento sale cada pregunta) y añade los fragmentos al prompt.

Flujo:

1. **Parseo:** cada PDF de `corpus_dir` se convierte a Markdown con **Docling** (`do_ocr=False` porque los PDF son texto nativo; `do_table_structure=False` para evitar dependencias de `cv2/libGL` que no están en la imagen).
2. **Chunking:** agrupa párrafos en fragmentos de ~**800 caracteres** con **150 de solapamiento**, cortando en límites de párrafo.
3. **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` en **CPU**, normalizados.
4. **Recuperación:** similitud coseno pregunta–fragmentos; se toman los mejores hasta llenar un presupuesto de **10 000 tokens** de contexto.
5. **Generación:** igual que zero-shot, con el contexto antepuesto a la pregunta.

Datos útiles medidos por los organizadores:

- Ejecución completa (indexar todo el corpus + 50 preguntas): **~36 minutos**, dentro del límite de 1 hora.
- Llenar el contexto cerca de 65 536 tokens **agota la memoria de la GPU (80 GB)** durante el prefill, y contextos largos con respuestas largas pueden tardar minutos por pregunta. Por eso usan 10 000 tokens.
- El índice se construye **en cada ejecución** (dentro de la hora). Una mejora obvia es **preconstruirlo offline**, pero el corpus de evaluación no es accesible directamente (ver [07-dataset-de-muestra-y-corpus.md](07-dataset-de-muestra-y-corpus.md)).

### Por qué `build.sh` empaqueta modelos

Las librerías `docling` y `sentence-transformers` ya están en el entorno, pero **los pesos** del modelo de layout de Docling y de `all-MiniLM-L6-v2` **no**. Como no hay internet, `build.sh` los descarga localmente y los mete en el zip:

```bash
docling-tools models download layout -o ./docling_models
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').save('embed_model')"
zip -q -r ../02_rag_submission.zip main.py docling_models embed_model -x '__pycache__/*' '*.pyc'
```

Requiere tener `docling` y `sentence-transformers` instalados localmente, en las versiones fijadas en [requirements-participant.txt](recursos/requirements-participant.txt).

## Construir un envío

```bash
cd 01_zero_shot && ./build.sh   # -> ../01_zero_shot_submission.zip
```

```bash
cd 02_rag && ./build.sh         # -> ../02_rag_submission.zip
```

Los zips y los pesos descargados **no** se guardan en el repo (están en `.gitignore`).
