import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


class ResolverCache:
    def __init__(self, path: str = "./resolver_cache.sqlite") -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.conn.commit()

    def get(self, key: str) -> Optional[Any]:
        cur = self.conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        self.conn.execute(
            "INSERT OR REPLACE INTO cache(key, value) VALUES (?, ?)", (key, payload)
        )
        self.conn.commit()
