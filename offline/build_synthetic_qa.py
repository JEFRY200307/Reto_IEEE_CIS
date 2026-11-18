"""Genera QA sintético desde PDFs públicos con OLMo (SPEC-028). Corre en AWS (necesita GPU).

Elige pasajes (chunks padre) repartidos por dominio, pide a OLMo una pregunta de cada tipo y guarda
el pasaje de origen como texto correcto (gold). Con --filter-zero-shot descarta las preguntas que
OLMo ya responde bien sin contexto (no sirven para medir la recuperación).

Uso (lista de trabajos de una sesión):
    python offline/build_synthetic_qa.py --pdfs data/public_pdfs --n 150 \
        --out eval/bench/synthetic_qa.json --filter-zero-shot
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dsqa.generate.llm import load_llm, postprocess  # noqa: E402
from dsqa.generate.prompts import Prompts  # noqa: E402
from dsqa.ingest.chunk import IdGen, chunk_section  # noqa: E402
from dsqa.ingest.clean import clean_doc  # noqa: E402
from dsqa.ingest.enrich import DomainLexicon, document_domain  # noqa: E402
from dsqa.ingest.extract import extract_pymupdf, list_pdfs  # noqa: E402
from dsqa.runtime.config import Config  # noqa: E402

QTYPES = {
    "factual": "recall a specific fact or value",
    "comparative": "compare two components, methods or values",
    "procedural": "explain how something is done or computed, possibly with a short calculation",
    "causal": "explain why something happens or was designed that way",
    "predictive": "infer what would happen or what value to expect under a condition",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdfs", type=Path, required=True)
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--out", type=Path, default=REPO / "eval" / "bench" / "synthetic_qa.json")
    ap.add_argument("--model-id", default="allenai/Olmo-3.1-32B-Instruct")
    ap.add_argument("--filter-zero-shot", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    cfg = Config()
    lexicon = DomainLexicon.load(REPO / "resources" / "domain_lexicon.json")
    pools: dict[str, list[tuple[str, str, str]]] = {"DONES": [], "AI Papers": []}
    ids = IdGen()
    for pdf in list_pdfs(a.pdfs):
        try:
            doc = clean_doc(extract_pymupdf(str(pdf), pdf.stem), cfg.ingest.clean_steps)
        except Exception as exc:
            print(f"omitido {pdf.name}: {exc}")
            continue
        mu = document_domain(doc, lexicon)
        if max(mu.values()) < 0.3:
            continue  # distractor
        domain = "DONES" if mu.get("DONES", 0) >= mu.get("AI", 0) else "AI Papers"
        for p in chunk_section(doc, ids, 600, 2000, 100).parents:
            if 800 <= len(p.raw) <= 2500:
                pools[domain].append((doc.title, pdf.name, p.raw))

    llm = load_llm(a.model_id, cfg.generate)
    prompts = Prompts(REPO / "resources" / "prompts")
    types = list(QTYPES)
    out, attempts = [], 0
    per_domain = {d: a.n // 2 for d in pools}
    for domain, pool in pools.items():
        rng.shuffle(pool)
        made = 0
        for title, fname, passage in pool:
            if made >= per_domain[domain] or attempts > 4 * a.n:
                break
            attempts += 1
            qtype = types[made % len(types)]
            raw = llm.generate(prompts.render("synth_qa", qtype=qtype, qtype_description=QTYPES[qtype], domain=domain,
                                              title=title, context=passage), 400)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            try:
                item = json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                item = None
            if not item or not item.get("question") or not item.get("answer"):
                continue
            if a.filter_zero_shot:
                zs = postprocess(llm.generate(prompts.render("zero_shot", question=item["question"]), 200))
                verdict = llm.generate(prompts.render("judge_local", question=item["question"],
                                                      reference=item["answer"], answer=zs), 5).upper()
                if "INCORRECT" not in verdict and "CORRECT" in verdict:
                    continue
            made += 1
            out.append({"id": f"syn-{len(out) + 1:03d}", "domain": domain, "question_type": qtype,
                        "question": item["question"].strip(), "answer": item["answer"].strip(),
                        "source_doc": fname, "gold_text": passage[:600]})
            print(f"{len(out)}: [{domain}/{qtype}] {item['question'][:90]}")
    a.out.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    gold_path = a.out.with_name(a.out.stem + "_gold.json")
    gold_path.write_text(json.dumps([{"id": q["id"], "gold_texts": [q["gold_text"][:300]]} for q in out],
                                    indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} preguntas en {a.out}; gold en {gold_path}. Revisa a mano al menos el 20 %.")


if __name__ == "__main__":
    main()
