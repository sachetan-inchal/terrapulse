"""GDELT Global News & Events Client."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


def _format_seendate(seendate: Optional[str]) -> str:
    """Format GDELT seendate string 'YYYYMMDDTHHMMSSZ' to 'YYYY-MM-DD'."""
    if not seendate or len(seendate) < 8:
        return ""
    year = seendate[0:4]
    month = seendate[4:6]
    day = seendate[6:8]
    return f"{year}-{month}-{day}"


class GDELTNewsClient(BaseResearchProvider):
    """Client for the GDELT 2.0 Doc API (Global Events, Language & Media Coverage)."""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(
        self,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="GDELT", timeout_seconds=timeout_seconds, session=session)

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        params = {
            "query": clean_q,
            "mode": "artlist",
            "maxrecords": min(max(1, limit), 25),
            "format": "json",
            "sort": "rel",
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "TerraPulse/2.0",
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("GDELT query failed: %s", exc)
            return []

        raw_articles = data.get("articles", []) if isinstance(data, dict) else []
        articles: List[ArticleMetadata] = []

        for item in raw_articles:
            title = clean_text(item.get("title", ""))
            url = item.get("url", "").strip()
            if not title or not url:
                continue

            pub_name = item.get("domain", "") or "Global News (GDELT)"
            pub_date = _format_seendate(item.get("seendate"))
            lang = item.get("language", "English")
            source_country = item.get("sourcecountry", "")

            articles.append(
                ArticleMetadata(
                    source_provider="GDELT",
                    title=title,
                    authors=[pub_name],
                    publication_name=pub_name,
                    publication_date=pub_date,
                    doi=None,
                    url=url,
                    abstract_or_summary=f"Global coverage detected by GDELT ({lang}, {source_country}).",
                    citation_count=None,
                    open_access=True,
                    extra_metadata={
                        "domain": pub_name,
                        "language": lang,
                        "sourcecountry": source_country,
                    },
                )
            )

        return articles

