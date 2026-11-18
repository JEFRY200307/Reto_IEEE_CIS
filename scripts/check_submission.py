"""Chequeo previo al envío (SPEC-026, §6.3 de los criterios de aceptación).

Estático (siempre):
  main.py en la raíz · firma de answer() · tamaño ≤ 950 MB · config.yaml válido ·
  todos los imports están en el entorno de Codabench (requirements-runtime.txt) o en la librería estándar.

Prueba de humo (--smoke): descomprime en una carpeta limpia, bloquea la red, importa main.py como lo
haría Codabench y llama answer() con N preguntas del banco. Falla si alguna respuesta no es str o está vacía.

Uso:
    python scripts/check_submission.py dist/dsqa_e3_2026-11-20.zip
    # Local, sin GPU ni modelos:
    DSQA_LLM_BACKEND=echo DSQA_ENCODER_BACKEND=hash DSQA_RERANKER_BACKEND=overlap \
      python scripts/check_submission.py dist/x.zip --smoke --corpus data/public_pdfs --n 5
    # En AWS, ensayo general real:
    python scripts/check_submission.py dist/x.zip --smoke --model-id allenai/Olmo-3.1-32B-Instruct \
      --corpus data/public_pdfs --n 50 --timed
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIMIT_BYTES = 950 * 1024 * 1024

# Nombre de import → nombre del paquete en requirements-runtime.txt
IMPORT_TO_DIST = {
    "yaml": "pyyaml", "fitz": "pymupdf", "sklearn": "scikit-learn", "faiss": "faiss-cpu", "rank_bm25": "rank-bm25",
    "bs4": "beautifulsoup4", "docx": "python-docx", "FlagEmbedding": "flagembedding", "dotenv": "python-dotenv",
    "huggingface_hub": "huggingface-hub", "sentence_transformers": "sentence-transformers",
    "llama_index": "llama-index-core", "langchain_community": "langchain-community",
    "langchain_text_splitters": "langchain-text-splitters", "lm_format_enforcer": "lm-format-enforcer",
    "rouge_score": "rouge-score", "bert_score": "bert-score", "qdrant_client": "qdrant-client",
}
INTERNAL = {"dsqa", "main"}


def runtime_packages() -> set[str]:
    names = set()
    for line in (REPO / "requirements-runtime.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.add(re.split(r"[=<>\[ ]", line)[0].lower().replace("_", "-"))
    return names


def imports_of(source: str) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.add(node.module.split(".")[0])
    return out


def static_checks(zip_path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if "main.py" not in names:
            errors.append("main.py no está en la raíz del zip")
        total = sum(i.file_size for i in zf.infolist())
        print(f"tamaño sin comprimir: {total / 2**20:.1f} MB")
        if total > LIMIT_BYTES:
            errors.append(f"el envío ocupa {total / 2**20:.0f} MB > 950 MB")
        if "main.py" in names:
            tree = ast.parse(zf.read("main.py").decode("utf-8"))
            fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "answer"), None)
            if fn is None:
                errors.append("main.py no define answer()")
            elif [a.arg for a in fn.args.args] != ["question", "corpus_dir", "model_id"]:
                errors.append(f"firma incorrecta: answer({', '.join(a.arg for a in fn.args.args)})")
        if "config.yaml" not in names:
            errors.append("falta config.yaml")
        else:
            sys.path.insert(0, str(REPO / "src"))
            from dsqa.runtime.config import Config
            import yaml

            try:
                Config.model_validate(yaml.safe_load(zf.read("config.yaml")))
            except Exception as exc:
                errors.append(f"config.yaml inválido: {exc}")

        allowed = runtime_packages()
        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        for name in names:
            if not name.endswith(".py"):
                continue
            for mod in imports_of(zf.read(name).decode("utf-8")):
                dist = IMPORT_TO_DIST.get(mod, mod).lower().replace("_", "-")
                if mod in stdlib or mod in INTERNAL or dist in allowed:
                    continue
                errors.append(f"{name}: import '{mod}' no está en el entorno de Codabench")
    return errors


_SMOKE = r"""
import importlib.util, json, socket, sys, time
def _blocked(*a, **k):
    raise OSError("red bloqueada en la prueba de humo")
socket.socket.connect = _blocked
socket.create_connection = _blocked
root, corpus, model_id, qfile = sys.argv[1:5]
questions = json.load(open(qfile, encoding="utf-8"))
t0 = time.monotonic()
spec = importlib.util.spec_from_file_location("main", root + "/main.py")
main = importlib.util.module_from_spec(spec); sys.modules["main"] = main; spec.loader.exec_module(main)
bad = 0
for i, q in enumerate(questions, 1):
    t = time.monotonic()
    out = main.answer(q["question"], corpus, model_id)
    ok = isinstance(out, str) and out.strip() != ""
    bad += 0 if ok else 1
    print(json.dumps({"i": i, "id": q.get("id"), "ok": ok, "seconds": round(time.monotonic() - t, 2),
                      "answer": (out[:160] if isinstance(out, str) else repr(out))}, ensure_ascii=False), flush=True)
print(json.dumps({"total_seconds": round(time.monotonic() - t0, 1), "n": len(questions), "bad": bad}), flush=True)
sys.exit(1 if bad else 0)
"""


def smoke(zip_path: Path, corpus: Path, model_id: str, bench: Path, n: int, timed: bool) -> bool:
    questions = json.loads(bench.read_text(encoding="utf-8"))
    questions = (questions * (n // max(1, len(questions)) + 1))[:n]
    with tempfile.TemporaryDirectory(prefix="dsqa-smoke-") as tmp:
        root = Path(tmp) / "submission"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(root)
        qfile = Path(tmp) / "questions.json"
        qfile.write_text(json.dumps(questions), encoding="utf-8")
        env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"}
        print(f"prueba de humo: {n} preguntas, corpus={corpus}, model_id={model_id}")
        proc = subprocess.run([sys.executable, "-c", _SMOKE, str(root), str(corpus.resolve()), model_id, str(qfile)],
                              cwd=tmp, env=env, text=True, capture_output=True)
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr[-3000:])
        if timed and proc.stdout.strip():
            last = json.loads(proc.stdout.strip().splitlines()[-1])
            per_q = last["total_seconds"] / max(1, last["n"])
            print(f"tiempo total {last['total_seconds']:.0f} s (incluye inicialización); "
                  f"estimado para 50 preguntas ≈ {last['total_seconds'] / 60:.1f} min si n=50 "
                  f"(media {per_q:.1f} s/pregunta). Objetivo: ≤ 45 min.")
        return proc.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", type=Path)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--corpus", type=Path, default=REPO / "data" / "public_pdfs")
    ap.add_argument("--model-id", default="allenai/Olmo-3.1-32B-Instruct")
    ap.add_argument("--bench", type=Path, default=REPO / "eval" / "bench" / "sample_qa.json")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--timed", action="store_true")
    a = ap.parse_args()

    errors = static_checks(a.zip)
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        raise SystemExit(1)
    print("chequeo estático: OK")
    if a.smoke and not smoke(a.zip, a.corpus, a.model_id, a.bench, a.n, a.timed):
        raise SystemExit("prueba de humo: FALLÓ")
    if a.smoke:
        print("prueba de humo: OK")


if __name__ == "__main__":
    main()
