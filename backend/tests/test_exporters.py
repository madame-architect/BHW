from app.exporters.rdf_exporter import export_rdf
from app.models.schema import CanonicalItem


def test_rdf_export_includes_dc_date_when_date_submitted_exists():
    item = CanonicalItem(id="1", inputKey="k", type="Article", title="T", accessed="2024-01-01")
    xml = export_rdf([item])
    assert "dc:date" in xml
    assert "dcterms:dateSubmitted" in xml
