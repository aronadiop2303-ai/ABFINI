from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    kind: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime


class OmniMemory:
    """Small in-process memory store for OMNI V0.2.

    The interface is intentionally storage-agnostic. A future Supabase/Postgres
    adapter can implement the same operations without changing the agent Core.
    """

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def remember(
        self,
        content: str,
        *,
        kind: str = "context",
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        content = content.strip()
        kind = kind.strip()
        if not content:
            raise ValueError("Memory content cannot be empty")
        if not kind:
            raise ValueError("Memory kind cannot be empty")
        entry = MemoryEntry(
            id=str(uuid4()),
            kind=kind,
            content=content,
            metadata=dict(metadata or {}),
            created_at=datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        return entry

    def recent(self, *, limit: int = 20, kind: str | None = None) -> list[MemoryEntry]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        entries = self._entries
        if kind is not None:
            entries = [entry for entry in entries if entry.kind == kind]
        return list(reversed(entries[-limit:]))

    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]:
        query_terms = {term.lower() for term in query.split() if term.strip()}
        if not query_terms:
            raise ValueError("query cannot be empty")
        scored: list[tuple[int, int, MemoryEntry]] = []
        for index, entry in enumerate(self._entries):
            haystack = f"{entry.content} {entry.kind}".lower()
            score = sum(term in haystack for term in query_terms)
            if score:
                scored.append((score, index, entry))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [entry for _, _, entry in scored[:limit]]

    def clear(self) -> None:
        self._entries.clear()
