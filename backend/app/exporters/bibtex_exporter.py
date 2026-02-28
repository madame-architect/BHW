from __future__ import annotations

from typing import List

from app.models.schema import CanonicalItem


def _citekey(item: CanonicalItem) -> str:
    author = item.authors[0].family.lower() if item.authors and item.authors[0].family else "item"
    year = (item.issued or "nd")[:4]
    token = ''.join(ch for ch in (item.title or "untitled").lower() if ch.isalnum())[:8]
    return f"{author}{year}{token}"


def export_bibtex(items: List[CanonicalItem]) -> str:
    lines = []
    for item in items:
        key = _citekey(item)
        lines.append(f"@{item.type}{{{key},")
        lines.append(f"  title = {{{item.title}}},")
        if item.authors:
            authors = " and ".join(
                [f"{a.family}, {a.given}" if a.family else (a.literal or "") for a in item.authors]
            )
            lines.append(f"  author = {{{authors}}},")
        if item.url:
            lines.append(f"  url = {{{item.url}}},")
        if item.doi:
            lines.append(f"  doi = {{{item.doi}}},")
        if item.accessed:
            lines.append(f"  urldate = {{{item.accessed}}},")
        if item.issued:
            lines.append(f"  year = {{{item.issued[:4]}}},")
        lines.append("}\n")
    return "\n".join(lines)
