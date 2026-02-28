from app.models.schema import CanonicalItem
from app.pipeline.steps import detect_duplicates


def test_duplicate_cluster_by_doi_and_title():
    a = CanonicalItem(id="1", inputKey="a", type="article", title="A Neural Approach", doi="10.1/x")
    b = CanonicalItem(id="2", inputKey="b", type="article", title="A neural approach", doi="10.1/x")
    c = CanonicalItem(id="3", inputKey="c", type="article", title="Graph Methods in IR")
    d = CanonicalItem(id="4", inputKey="d", type="article", title="Graph methods for IR")
    clusters = detect_duplicates([a,b,c,d], threshold=80)
    assert any(cl.reason == "Exact DOI match" for cl in clusters)
    assert any(cl.reason == "Fuzzy title cluster" for cl in clusters)
