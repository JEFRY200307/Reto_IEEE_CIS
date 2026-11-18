"""Program of Thoughts en un subproceso aislado (SPEC-024, ADR-11)."""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llm import LLM
    from .prompts import Prompts

log = logging.getLogger("dsqa.pot")

_CODE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr",
                    "setattr", "delattr", "input", "breakpoint", "exit", "quit", "help", "memoryview"}

# Se ejecuta con `python -I -c`; recibe el código por stdin e imprime {"answer": ...}.
_RUNNER = r"""
import json, math, sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
except Exception:
    pass
code = sys.stdin.read()
safe = {n: getattr(__builtins__, n) for n in (
    "abs", "min", "max", "round", "sum", "len", "range", "float", "int", "pow", "print", "enumerate", "zip",
    "sorted", "list", "dict", "tuple", "set", "str", "bool", "map", "filter", "any", "all", "isinstance",
    "divmod", "reversed", "ValueError", "ZeroDivisionError", "Exception")}
g = {"__builtins__": safe, "math": math}
exec(code, g)
print(json.dumps({"answer": None if g.get("answer") is None else str(g.get("answer"))}))
"""


@dataclass
class PoTResult:
    code: str
    value: str


def extract_code(text: str) -> str | None:
    m = _CODE_RE.search(text)
    code = m.group(1) if m else (text if "answer" in text and "=" in text else None)
    return code.strip() if code else None


def validate(code: str) -> str:
    """Valida con ast y devuelve el código sin `import math` (math ya está disponible)."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if any(n != "math" for n in names):
                raise ValueError(f"import no permitido: {names}")
        elif isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise ValueError(f"nombre no permitido: {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError(f"atributo no permitido: {node.attr}")
        elif isinstance(node, (ast.While, ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Global, ast.Nonlocal)):
            raise ValueError(f"construcción no permitida: {type(node).__name__}")
    lines = [ln for ln in code.splitlines() if not re.match(r"^\s*(import math|from math import .*)\s*$", ln)]
    return "\n".join(lines)


def run_sandboxed(code: str, timeout_s: float) -> str | None:
    env = {"PATH": os.environ.get("PATH", ""), "CUDA_VISIBLE_DEVICES": "", "PYTHONIOENCODING": "utf-8"}
    if os.name == "nt":  # Windows necesita SYSTEMROOT para arrancar Python
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
    try:
        proc = subprocess.run([sys.executable, "-I", "-c", _RUNNER], input=code, capture_output=True,
                              text=True, timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired:
        log.warning("PoT: tiempo agotado")
        return None
    if proc.returncode != 0:
        log.warning("PoT: error de ejecución: %s", proc.stderr.strip()[-300:])
        return None
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1]).get("answer")
    except Exception:
        return None


def solve(llm: "LLM", prompts: "Prompts", question: str, context: str, timeout_s: float, max_new_tokens: int) -> PoTResult | None:
    try:
        raw = llm.generate(prompts.render("pot", question=question, context=context), max_new_tokens)
        code = extract_code(raw)
        if not code:
            return None
        value = run_sandboxed(validate(code), timeout_s)
        return PoTResult(code, value) if value not in (None, "", "None") else None
    except Exception as exc:
        log.warning("PoT descartado: %s", exc)
        return None
