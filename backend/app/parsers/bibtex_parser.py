from __future__ import annotations

import re
import uuid
from typing import List

import bibtexparser

from app.models.schema import CanonicalItem, Person


def _split_authors(authors: str) -> List[Person]:
    parts = [a.strip() for a in authors.split(" and ") if a.strip()]
    people: List[Person] = []
    for part in parts:
        if "," in part:
            family, given = [p.strip() for p in part.split(",", 1)]
            people.append(Person(family=family, given=given))
        else:
            toks = part.split()
            if len(toks) > 1:
                people.append(Person(given=" ".join(toks[:-1]), family=toks[-1]))
            else:
                people.append(Person(literal=part))
    return people


def _extract_doi(entry: dict) -> str | None:
    doi = entry.get("doi") or entry.get("DOI")
    if doi:
        return doi.strip().lower().removeprefix("https://doi.org/")
    url = entry.get("url", "")
    m = re.search(r"doi\.org/(10\.\S+)", url)
    return m.group(1).rstrip("}") if m else None


def parse_bibtex(content: str) -> List[CanonicalItem]:
    db = bibtexparser.loads(content)
    items: List[CanonicalItem] = []
    for entry in db.entries:
        key = entry.get("ID", str(uuid.uuid4()))
        items.append(
            CanonicalItem(
                id=str(uuid.uuid4()),
                inputKey=key,
                type=entry.get("ENTRYTYPE", "misc"),
                title=entry.get("title", ""),
                authors=_split_authors(entry.get("author", "")),
                issued=entry.get("year"),
                accessed=entry.get("urldate"),
                url=entry.get("url"),
                doi=_extract_doi(entry),
                publisher=entry.get("publisher"),
                containerTitle=entry.get("journal") or entry.get("booktitle"),
                tags=[t.strip() for t in entry.get("keywords", "").split(",") if t.strip()],
                identifiers={"bibtex_id": key},
            )
        )
    return items
