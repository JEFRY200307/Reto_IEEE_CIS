from dsqa.ingest.chunk import IdGen, chunk_fixed, chunk_section
from dsqa.ingest.clean import clean_doc
from dsqa.ingest.extract import ExtractionJob, extract_pymupdf, list_pdfs
from dsqa.runtime.config import IngestCfg
from dsqa.types import ExtractedDoc, Page


def _doc(pages: list[str]) -> ExtractedDoc:
    return ExtractedDoc("d1", "x.pdf", "Title", "", [Page("d1", i, t) for i, t in enumerate(pages)])


def test_dehyphen_keeps_technical_hyphens():
    out = clean_doc(_doc(["The tempera-\nture of Be-\n7 is high."]), ["dehyphen"])
    assert "temperature" in out.pages[0].text
    assert "Be-7" in out.pages[0].text


def test_repeated_headers_removed():
    body = "\n".join(f"Body line {j} of the section." for j in range(8))
    pages = [f"REPORT HEADER\nContent of page {i} with details.\n{body}\nPage {i + 1}" for i in range(4)]
    out = clean_doc(_doc(pages), ["headers"])
    assert all("REPORT HEADER" not in p.text for p in out.pages)
    assert all("Page " not in p.text.splitlines()[-1] for p in out.pages)  # pie con número de página
    assert all("Body line 4" in p.text for p in out.pages)  # el contenido del medio se conserva


def test_references_cut_only_near_the_end():
    body = "word " * 400
    out = clean_doc(_doc([body, body + "\nReferences\n[1] A. B. Paper."]), ["references"])
    assert "[1] A. B." not in "".join(p.text for p in out.pages)
    early = clean_doc(_doc(["References\nsee below", body, body]), ["references"])
    assert "References" in early.pages[0].text


def test_section_chunker_parent_child():
    text = ("1. Introduction\n" + "The lithium loop is described here. " * 30 + "\n\n2. Method\n" + "We compute values. " * 40)
    cs = chunk_section(_doc([text]), IdGen(), child_chars=300, parent_chars=800, overlap=50)
    assert cs.parents and cs.children
    parent_ids = {p.chunk_id for p in cs.parents}
    for c in cs.children:
        assert c.parent_id in parent_ids
        assert c.section in ("1. Introduction", "2. Method")
        assert len(c.raw) <= 300 + 60


def test_section_chunker_without_headings_falls_back():
    cs = chunk_section(_doc(["plain text without any heading. " * 50]), IdGen(), 300, 800, 50)
    assert cs.children and all(c.section == "" for c in cs.children)


def test_fixed_chunker_sizes():
    cs = chunk_fixed(_doc(["A paragraph of text. " * 200]), IdGen(), size=800, overlap=150)
    assert len(cs.children) > 3
    assert all(len(c.raw) <= 800 + 160 for c in cs.children)


def test_extraction_skips_broken_and_non_pdf(corpus_dir, tmp_path):
    paths = list_pdfs(corpus_dir)
    assert all(p.suffix == ".pdf" for p in paths) and len(paths) == 4
    job = ExtractionJob(str(corpus_dir), IngestCfg(workers=1), tmp_path)
    docs = job.collect()
    assert len(docs) == 3
    assert any("broken.pdf" in s[0] for s in job.skipped)


def test_extract_title_and_abstract(corpus_dir):
    doc = extract_pymupdf(str(corpus_dir / "winstat.pdf"), "w")
    assert "WinStat" in doc.title
    assert "window-based" in doc.abstract
