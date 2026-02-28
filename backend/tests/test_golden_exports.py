from pathlib import Path

from app.exporters.bibtex_exporter import export_bibtex
from app.exporters.rdf_exporter import export_rdf
from app.models.schema import CanonicalItem, Person


def test_bib_export_golden_contains_required_fields():
    item = CanonicalItem(id="1", inputKey="smith2020", type="article", title="Example Title", authors=[Person(family="Smith", given="Jane")], url="https://example.org", doi="10.1000/xyz123", accessed="2024-01-01", issued="2020")
    out = export_bibtex([item])
    assert "url = {https://example.org}" in out
    assert "doi = {10.1000/xyz123}" in out
    assert "urldate = {2024-01-01}" in out


def test_rdf_export_golden_edge_case():
    item = CanonicalItem(id="1", inputKey="k", type="Article", title="T", accessed="2024-01-01")
    out = export_rdf([item])
    assert "<dc:date></dc:date>" in out or "<dc:date/>" in out
    assert "<dcterms:dateSubmitted>2024-01-01</dcterms:dateSubmitted>" in out
    golden = Path(__file__).parent / "golden" / "sample.rdf"
    assert "bib:Article" in golden.read_text()
