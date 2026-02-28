from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.services.cache import ResolverCache


class ResolverService:
    def __init__(self, cache: ResolverCache):
        self.cache = cache

    async def resolve_doi_csl(self, doi: str) -> Optional[Dict[str, Any]]:
        key = f"doi:{doi}"
        if cached := self.cache.get(key):
            return cached
        url = f"https://doi.org/{doi}"
        headers = {"accept": "application/vnd.citationstyles.csl+json"}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                r = await client.get(url, headers=headers)
                if r.status_code >= 400:
                    return None
                data = r.json()
                data["_retrievedAt"] = datetime.now(timezone.utc).isoformat()
                self.cache.set(key, data)
                return data
        except Exception:
            return None

    async def validate_url(self, url: str) -> Dict[str, Any]:
        key = f"url:{url}"
        if cached := self.cache.get(key):
            return cached
        result: Dict[str, Any] = {"ok": False, "status": None, "finalUrl": url}
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                r = await client.get(url)
                result = {
                    "ok": r.status_code < 400,
                    "status": r.status_code,
                    "finalUrl": str(r.url),
                    "redirected": str(r.url) != url,
                }
        except Exception as exc:
            result["error"] = str(exc)
        self.cache.set(key, result)
        return result

    async def resolve_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        q = title.strip()
        if not q:
            return None
        key = f"crossref:{q.lower()}"
        if cached := self.cache.get(key):
            return cached
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get("https://api.crossref.org/works", params={"query.title": q, "rows": 1})
                if r.status_code >= 400:
                    return None
                data = r.json()
                msg = data.get("message", {})
                items = msg.get("items", [])
                if not items:
                    return None
                out = items[0]
                self.cache.set(key, out)
                return out
        except Exception:
            return None
