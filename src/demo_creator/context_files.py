"""Readers for the context files a demo ships: knowledge.csv, metrics.csv and the
wACE bootstrap markdown (whose later sections are turned into knowledge entries)."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    sql: str
    database: str | None = None

    @property
    def view(self) -> str | None:
        m = re.search(r"\b([A-Z_][A-Z0-9_]*)\.[A-Z_][A-Z0-9_]*", self.sql)
        return m.group(1) if m else None


def read_knowledge_csv(path: Path) -> list[str]:
    """`knowledge.csv` has a single `Knowledge` column (Wisdom's import format)."""
    with Path(path).open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    key = next((k for k in (rows[0].keys() if rows else []) if k.strip().lower() == "knowledge"), None)
    if key is None:
        raise ValueError(f"{path} needs a 'Knowledge' column")
    return [r[key].strip() for r in rows if r[key] and r[key].strip()]


def read_metrics_csv(path: Path) -> list[Metric]:
    """`metrics.csv`: Name, Description, SQL, Database (Wisdom's import format)."""
    with Path(path).open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        cols = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not cols.get("name"):
            continue
        out.append(Metric(cols["name"], cols.get("description", ""), cols.get("sql", ""), cols.get("database") or None))
    return out


_SECTION = re.compile(r"^##\s+(?:\d+[.)]?\s*)?(.+?)\s*$", re.M)
_KNOWLEDGE_SECTIONS = ("domain knowledge", "business nuances", "tribal knowledge", "query routing hints")


def bootstrap_sections(md: str) -> dict[str, str]:
    """{section title (lower): body} for every `## ` heading in the bootstrap."""
    out: dict[str, str] = {}
    matches = list(_SECTION.finditer(md))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        out[m.group(1).strip().lower()] = md[m.end():end].strip()
    return out


def bootstrap_to_knowledge(md: str) -> list[str]:
    """One knowledge entry per bullet/sentence in the knowledge-bearing sections
    (7 Domain Knowledge, 8 Business Nuances, 9 Tribal Knowledge, 10 Query Routing Hints)."""
    entries: list[str] = []
    for title, body in bootstrap_sections(md).items():
        if not any(k in title for k in _KNOWLEDGE_SECTIONS):
            continue
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("|"):
                continue
            s = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", s)
            s = s.replace("**", "").strip()
            if len(s) > 20:
                entries.append(s)
    return entries
