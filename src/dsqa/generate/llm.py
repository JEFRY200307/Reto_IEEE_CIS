"""Carga de OLMo y generación (SPEC-023, ADR-01, ADR-06).

`HFLLM` es el modelo real (transformers, bf16, sdpa, greedy). `EchoLLM` es un sustituto sin GPU
para pruebas y para la prueba de humo local (DSQA_LLM_BACKEND=echo).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Protocol

log = logging.getLogger("dsqa.llm")


class LLM(Protocol):
    def generate(self, messages: list[dict], max_new_tokens: int) -> str: ...
    def next_token_probs(self, messages: list[dict], words: list[str]) -> dict[str, float]: ...
    def count_tokens(self, text: str) -> int: ...
    def truncate(self, text: str, max_tokens: int) -> str: ...


class HFLLM:
    def __init__(self, model_id: str, attn_implementation: str = "sdpa", quantization: str = "none") -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        kwargs: dict = {"device_map": "cuda" if torch.cuda.is_available() else "cpu",
                        "attn_implementation": attn_implementation}
        if quantization in ("4bit", "8bit"):
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = (
                BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4")
                if quantization == "4bit" else BitsAndBytesConfig(load_in_8bit=True)
            )
        # bf16 en GPU (Codabench, ADR-01). Sin GPU, bf16 es emulado y muy lento: fp32 (solo pruebas locales).
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        try:
            self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype, **kwargs)
        except TypeError:  # transformers < 4.56 usa torch_dtype
            self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype, **kwargs)
        self.model.eval()
        self.pad_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id

    def _inputs(self, messages: list[dict]):
        prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        enc = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        return {k: v.to(self.model.device) for k, v in enc.items()}

    def generate(self, messages: list[dict], max_new_tokens: int) -> str:
        inputs = self._inputs(messages)
        with self.torch.inference_mode():
            out = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                      pad_token_id=self.pad_id)
        new = out[0, inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new, skip_special_tokens=True)

    def next_token_probs(self, messages: list[dict], words: list[str]) -> dict[str, float]:
        inputs = self._inputs(messages)
        with self.torch.inference_mode():
            logits = self.model(**inputs).logits[0, -1].float()
        probs = self.torch.softmax(logits, dim=-1)
        out: dict[str, float] = {}
        for w in words:
            ids = set()
            for variant in (w, " " + w, w.lower(), " " + w.lower(), w.upper()):
                toks = self.tokenizer.encode(variant, add_special_tokens=False)
                if toks:
                    ids.add(toks[0])
            out[w] = float(sum(probs[i].item() for i in ids))
        return out

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def truncate(self, text: str, max_tokens: int) -> str:
        ids = self.tokenizer.encode(text, add_special_tokens=False)
        return text if len(ids) <= max_tokens else self.tokenizer.decode(ids[:max_tokens])

    def free_cache(self) -> None:
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


class EchoLLM:
    """Sin modelo: devuelve una respuesta construida con la primera oración del contexto."""

    def generate(self, messages: list[dict], max_new_tokens: int) -> str:
        user = messages[-1]["content"] if messages else ""
        m = re.search(r"\[Doc: [^\]]*\]\n(.+?)(?:\n|$)", user)
        if "```python" in (messages[0].get("content", "") if messages else "") or "Python program" in user:
            return "```python\nanswer = '42'\n```"
        return (m.group(1)[:300] if m else "No context available.").strip()

    def next_token_probs(self, messages: list[dict], words: list[str]) -> dict[str, float]:
        return {w: (0.7 if w.lower() == "yes" else 0.3) for w in words}

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def truncate(self, text: str, max_tokens: int) -> str:
        return " ".join(text.split()[:max_tokens])

    def free_cache(self) -> None:
        pass


def load_llm(model_id: str, gcfg) -> LLM:
    backend = os.environ.get("DSQA_LLM_BACKEND", "hf").lower()
    if backend == "echo":
        log.warning("DSQA_LLM_BACKEND=echo: se usa EchoLLM (solo pruebas)")
        return EchoLLM()
    return HFLLM(model_id, gcfg.attn_implementation, gcfg.quantization)


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_SPECIAL_RE = re.compile(r"<\|[^|>]{1,40}\|>")
_LEAD_RE = re.compile(
    r"^\s*(?:\*\*(?:final\s+)?answer\s*[:：]?\s*\*\*\s*[:：]?|(?:final\s+)?answer\s*[:：])\s*", re.IGNORECASE
)


def postprocess(text: str) -> str:
    original = text
    text = _THINK_RE.sub("", text)
    text = _SPECIAL_RE.sub("", text)
    text = re.sub(r"^(?:assistant|Assistant)\s*:?\s*\n", "", text)
    text = _LEAD_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or original.strip()
