from app.parsers.bibtex_parser import parse_bibtex
from app.parsers.rdf_parser import parse_rdf


def test_parse_bibtex_extracts_fields():
    bib = """@article{smith2020,title={Example Title},author={Smith, Jane and Doe, John},url={https://example.org},doi={10.1000/xyz123},year={2020}}"""
    items = parse_bibtex(bib)
    assert len(items) == 1
    assert items[0].title == "Example Title"
    assert items[0].doi == "10.1000/xyz123"


def test_parse_rdf_extracts_dc_date_and_accessed():
    rdf = '''<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:bib="http://purl.org/net/biblio#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
  <bib:Article rdf:about="#item1"><dc:title>T</dc:title><dc:date>2024</dc:date><dcterms:dateSubmitted>2024-09-01</dcterms:dateSubmitted><dc:identifier>https://example.com</dc:identifier></bib:Article>
</rdf:RDF>'''
    items = parse_rdf(rdf)
    assert items[0].issued == "2024"
    assert items[0].accessed == "2024-09-01"
