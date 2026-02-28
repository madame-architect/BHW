from __future__ import annotations

from typing import List

from lxml import etree

from app.models.schema import CanonicalItem

NSMAP = {
    None: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "bib": "http://purl.org/net/biblio#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "z": "http://www.zotero.org/namespaces/export#",
    "foaf": "http://xmlns.com/foaf/0.1/",
}


def export_rdf(items: List[CanonicalItem]) -> str:
    root = etree.Element("RDF", nsmap=NSMAP)
    rdf_ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    for item in items:
        node = etree.SubElement(root, f"{{{NSMAP['bib']}}}{item.type or 'Document'}")
        node.set(f"{{{rdf_ns}}}about", f"#{item.inputKey}")
        etree.SubElement(node, f"{{{NSMAP['dc']}}}title").text = item.title
        etree.SubElement(node, f"{{{NSMAP['dc']}}}date").text = item.issued or ""
        if item.accessed:
            etree.SubElement(node, f"{{{NSMAP['dcterms']}}}dateSubmitted").text = item.accessed
        if item.url:
            etree.SubElement(node, f"{{{NSMAP['dc']}}}identifier").text = item.url
        if item.doi:
            etree.SubElement(node, f"{{{NSMAP['dc']}}}identifier").text = f"doi:{item.doi}"
        for t in item.tags:
            etree.SubElement(node, f"{{{NSMAP['dc']}}}subject").text = t
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode("utf-8")
