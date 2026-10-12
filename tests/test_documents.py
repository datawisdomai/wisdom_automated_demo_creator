from pathlib import Path

from demo_creator.documents import render_pdf

MD = """# Carrier Services Agreement
Letterhead: SummitTrail Logistics
Date: 2026-03-01
Reference: CSA-2026-017

## 1. Scope
This agreement covers **ground** parcel services for zones 2 through 8.

- Fuel surcharge applies weekly
- Residential surcharge: $4.20 per label

| Zone | Base rate | On-time target |
| --- | --- | --- |
| 2 | $7.10 | 96% |
| 8 | $12.40 | 92% |

---
## 2. Termination
Either party may terminate with 60 days notice.
"""


def test_render_pdf_is_deterministic(tmp_path: Path):
    src = tmp_path / "doc.md"
    src.write_text(MD)
    a = render_pdf(src, tmp_path / "a.pdf")
    b = render_pdf(src, tmp_path / "b.pdf")
    assert a.stat().st_size > 1500
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes().startswith(b"%PDF")
