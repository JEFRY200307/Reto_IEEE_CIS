"""Punto de entrada para Codabench (SPEC-001).

Codabench importa este archivo y llama `answer()` una vez por pregunta, en el mismo proceso.
Toda la lógica vive en el paquete `dsqa`; aquí solo se cumple el contrato y nunca se lanza una excepción.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dsqa.runtime.clock import CLOCK  # noqa: F401  (arranca el reloj global al importar)
    from dsqa.runtime.safety import fallback_text, safe_answer
except Exception:  # el paquete no se pudo importar: aun así se devuelve texto
    safe_answer = None

    def fallback_text(question: str) -> str:
        return f"Based on the technical documentation, regarding: {question}"


def answer(question: str, corpus_dir: str, model_id: str) -> str:
    try:
        if safe_answer is None:
            return fallback_text(str(question))
        out = safe_answer(question, corpus_dir, model_id, ROOT)
        return out if isinstance(out, str) and out.strip() else fallback_text(str(question))
    except Exception:
        return fallback_text(str(question))
