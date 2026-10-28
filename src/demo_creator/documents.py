"""Render a demo's unstructured documents (contracts, memos, reports) from small
markdown specs to deterministic PDFs with reportlab.

Pattern from `people_analytics_poc/03_generate_unstructured.py` and
`Wahl Clippers/.../06_lab_pdfs.py`, generalised: the markdown subset is
`# Title`, `## Heading`, paragraphs, `- bullets`, pipe tables, `---` page break,
and an optional header block of `Key: value` lines (Letterhead, Date, Reference)
before the first heading. Output is byte-stable for the same input (invariant
PDF metadata) so reruns do not churn files.
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HEADER_LINE = re.compile(r"^([A-Za-z][A-Za-z ]{0,30}):\s*(.+)$")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontSize=17, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13),
        "meta": ParagraphStyle("m", parent=ss["BodyText"], fontSize=8.5, textColor=colors.HexColor("#555555"), leading=11),
        "bullet": ParagraphStyle("bl", parent=ss["BodyText"], fontSize=9.5, leading=13, leftIndent=14, bulletIndent=4),
        "cell": ParagraphStyle("c", parent=ss["BodyText"], fontSize=8.5, leading=10.5),
    }


def _inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<i>\1</i>", text)
    return text


def _table(rows: list[list[str]], st) -> Table:
    data = [[Paragraph(_inline(c), st["cell"]) for c in r] for r in rows]
    t = Table(data, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EDF3")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C2CC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def markdown_to_flowables(md: str):
    st = _styles()
    flow = []
    lines = md.splitlines()
    i = 0
    header_done = False
    para: list[str] = []

    def flush_para():
        if para:
            flow.append(Paragraph(_inline(" ".join(para)), st["body"]))
            flow.append(Spacer(1, 5))
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            flush_para(); i += 1; continue
        if s.startswith("# "):
            flush_para(); flow.append(Paragraph(_inline(s[2:]), st["title"])); header_done = False; i += 1; continue
        if not header_done and _HEADER_LINE.match(s) and not s.startswith("|"):
            flush_para(); flow.append(Paragraph(_inline(s), st["meta"])); i += 1
            if i < len(lines) and not _HEADER_LINE.match(lines[i].strip()):
                header_done = True; flow.append(Spacer(1, 8))
            continue
        header_done = True
        if s.startswith("## "):
            flush_para(); flow.append(Paragraph(_inline(s[3:]), st["h2"])); i += 1; continue
        if s == "---":
            flush_para(); flow.append(PageBreak()); i += 1; continue
        if s.startswith(("- ", "* ")):
            flush_para()
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                flow.append(Paragraph(_inline(lines[i].strip()[2:]), st["bullet"], bulletText="•"))
                i += 1
            flow.append(Spacer(1, 4)); continue
        if s.startswith("|"):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                flow.append(_table(rows, st)); flow.append(Spacer(1, 8))
            continue
        para.append(s); i += 1
    flush_para()
    return flow


def render_pdf(md_path: Path, out_path: Path, *, title: str | None = None) -> Path:
    md = Path(md_path).read_text()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=LETTER, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch, title=title or md_path.stem,
                            author="", subject="", creator="", invariant=1)
    doc.build(markdown_to_flowables(md))
    return out_path


def context_assets(spec) -> list[dict]:
    """`context_assets[]` in demo.yaml: specs rendered like documents but uploaded to the
    domain's context extractor (glossary, metric standards, wiki pages, chat exports)
    instead of the dataset. Optional; loading is tolerant of its absence."""
    return list(spec.raw.get("context_assets") or [])


def render_all(spec, *, echo: bool = True) -> list[dict]:
    """Render every `documents[]` and `context_assets[]` spec to build/docs/<name>.pdf
    (a spec listed in both is rendered once)."""
    out = []
    seen = set()
    for d in list(spec.documents) + context_assets(spec):
        if d["spec"] in seen:
            continue
        seen.add(d["spec"])
        src = spec.dir / d["spec"]
        pdf = spec.paths.docs_out / (Path(d["spec"]).stem + ".pdf")
        try:
            from .context_assets import TEXT_KINDS, asset_output_path
            if str(d.get("kind") or "") in TEXT_KINDS:   # uploaded as the text itself (.sql / .txt), never a PDF
                pdf = asset_output_path(spec, d)
                pdf.parent.mkdir(parents=True, exist_ok=True)
                pdf.write_text(src.read_text())
                out.append({"spec": d["spec"], "pdf": str(pdf), "kind": d.get("kind"), "ok": True})
                if echo:
                    print(f"  copied {pdf.name} ({pdf.stat().st_size:,} bytes)")
                continue
            render_pdf(src, pdf, title=d.get("title"))
            out.append({"spec": d["spec"], "pdf": str(pdf), "kind": d.get("kind"), "ok": True})
            if echo:
                print(f"  rendered {pdf.name} ({pdf.stat().st_size:,} bytes)")
        except Exception as exc:  # noqa: BLE001
            out.append({"spec": d["spec"], "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
            if echo:
                print(f"  FAILED {d['spec']}: {out[-1]['error']}")
    return out
