import pytest

from app.services.cache import ResolverCache
from app.services.resolvers import ResolverService


@pytest.mark.asyncio
async def test_validate_url_mocked(monkeypatch, tmp_path):
    service = ResolverService(ResolverCache(str(tmp_path / "cache.sqlite")))

    class MockResponse:
        status_code = 200
        url = "https://example.org/canonical"

    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def get(self, url):
            return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: MockClient())
    result = await service.validate_url("https://example.org")
    assert result["ok"] is True
    assert result["finalUrl"].endswith("canonical")
