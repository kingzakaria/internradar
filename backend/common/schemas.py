"""Standard offer format shared by every connector and the rest of the pipeline."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import UTC, datetime

from pydantic import BaseModel, Field


def normalize_text(text: str | None) -> str:
    """Lowercase, remove accents and punctuation, collapse spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


class Offer(BaseModel):
    source: str  # connector name, e.g. "greenhouse"
    source_id: str | None = None  # id of the offer on that source, if any
    title: str
    company: str | None = None
    city: str | None = None
    country: str | None = None  # "MA", "FR", or None when unknown
    url: str
    description: str = ""
    posted_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def offer_id(self) -> str:
        """Stable id of this offer on its source (avoids inserting it twice)."""
        key = f"{self.source}:{self.source_id or self.url}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    @property
    def dedup_key(self) -> str:
        """Same offer published on several sites gets the same key."""
        parts = (
            normalize_text(self.title),
            normalize_text(self.company),
            normalize_text(self.city),
        )
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]