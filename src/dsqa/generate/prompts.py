"""Plantillas de prompts en resources/prompts/*.txt.

Formato de cada archivo:
    ### system
    <mensaje de sistema>
    ### user
    <mensaje de usuario con {question}, {context}, ...>

Los marcadores se reemplazan con str.replace (no format), para no romperse con llaves de LaTeX.
"""

from __future__ import annotations

import re
from pathlib import Path

_SECTION_RE = re.compile(r"^###\s*(system|user)\s*$", re.MULTILINE | re.IGNORECASE)

KINDS = ("answer_generic", "answer_dones", "answer_ai", "zero_shot", "judge_s5", "pot", "pot_answer")


class Prompts:
    def __init__(self, directory: Path) -> None:
        self.templates: dict[str, tuple[str, str]] = {}
        for path in sorted(Path(directory).glob("*.txt")):
            self.templates[path.stem] = self._parse(path.read_text(encoding="utf-8"))

    @staticmethod
    def _parse(text: str) -> tuple[str, str]:
        parts = _SECTION_RE.split(text)
        sections: dict[str, str] = {}
        for i in range(1, len(parts) - 1, 2):
            sections[parts[i].lower()] = parts[i + 1].strip()
        return sections.get("system", ""), sections.get("user", "{question}")

    def has(self, kind: str) -> bool:
        return kind in self.templates

    def render(self, kind: str, **values: str) -> list[dict]:
        if kind not in self.templates:
            raise KeyError(f"no existe la plantilla de prompt '{kind}'")
        system, user = self.templates[kind]
        for key, value in values.items():
            system = system.replace("{" + key + "}", str(value))
            user = user.replace("{" + key + "}", str(value))
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": user})
        return messages
