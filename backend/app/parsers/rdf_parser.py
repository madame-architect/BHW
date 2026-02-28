from __future__ import annotations

import uuid
from typing import List

from lxml import etree

from app.models.schema import CanonicalItem, Person

NS = {
    "bib": "http://purl.org/net/biblio#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "z": "http://www.zotero.org/namespaces/export#",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


def parse_rdf(content: str) -> List[CanonicalItem]:
    root = etree.fromstring(content.encode("utf-8"))
    items: List[CanonicalItem] = []
    for node in root.xpath("//bib:*", namespaces=NS):
        typ = etree.QName(node).localname
        title = "".join(node.xpath("./dc:title/text()", namespaces=NS))
        url = "".join(node.xpath("./dc:identifier[contains(text(),'http')]/text()", namespaces=NS))
        doi = "".join(node.xpath("./dc:identifier[contains(text(),'10.')]/text()", namespaces=NS))
        if doi.startswith("doi:"):
            doi = doi[4:]
        creators = []
        for c in node.xpath("./bib:authors//foaf:Person", namespaces=NS):
            creators.append(
                Person(
                    family="".join(c.xpath("./foaf:surname/text()", namespaces=NS)) or None,
                    given="".join(c.xpath("./foaf:givenname/text()", namespaces=NS)) or None,
                )
            )
        about = node.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", str(uuid.uuid4()))
        tags = node.xpath("./dc:subject/text()", namespaces=NS)
        items.append(
            CanonicalItem(
                id=str(uuid.uuid4()),
                inputKey=about.split("#")[-1],
                type=typ,
                title=title,
                authors=creators,
                issued="".join(node.xpath("./dc:date/text()", namespaces=NS)) or None,
                accessed="".join(node.xpath("./dcterms:dateSubmitted/text()", namespaces=NS)) or None,
                url=url or None,
                doi=doi or None,
                publisher="".join(node.xpath("./dc:publisher/text()", namespaces=NS)) or None,
                containerTitle="".join(node.xpath("./dcterms:isPartOf/text()", namespaces=NS)) or None,
                tags=tags,
                identifiers={"rdf_about": about},
            )
        )
    return items
