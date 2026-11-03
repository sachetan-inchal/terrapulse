"""The Guardian Open Platform News Client."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


class GuardianNewsClient(BaseResearchProvider):
    """Client for The Guardian Open Platform API (Investigative Environmental Journalism)."""

    BASE_URL = "https://content.guardianapis.com/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="The Guardian", timeout_seconds=timeout_seconds, session=session)
        self.api_key = api_key or os.getenv("GUARDIAN_API_KEY")

    def is_available(self) -> bool:
        """The Guardian Open Platform requires a valid API key."""
        return bool(self.api_key and self.api_key.strip())

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        if not self.is_available():
            logger.info("GuardianNewsClient: GUARDIAN_API_KEY is not configured. Skipping.")
            return []

        params = {
            "q": clean_q,
            "page-size": min(max(1, limit), 25),
            "show-fields": "headline,standfirst,trailText,byline,publication,shortUrl",
            "api-key": self.api_key,
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("The Guardian query failed: %s", exc)
            return []

        results = data.get("response", {}).get("results", [])
        articles: List[ArticleMetadata] = []

        for item in results:
            fields = item.get("fields") or {}
            headline = fields.get("headline") or item.get("webTitle", "")
            title = clean_text(headline)
            if not title:
                continue

            byline = fields.get("byline", "")
            authors = [clean_text(byline)] if byline else ["The Guardian"]

            pub_date = item.get("webPublicationDate", "")
            if pub_date and "T" in pub_date:
                pub_date = pub_date.split("T")[0]

            url = fields.get("shortUrl") or item.get("webUrl", "")
            summary = clean_text(fields.get("trailText") or fields.get("standfirst") or "")
            pub_name = fields.get("publication") or "The Guardian"

            articles.append(
                ArticleMetadata(
                    source_provider="The Guardian",
                    title=title,
                    authors=authors,
                    publication_name=pub_name,
                    publication_date=pub_date,
                    doi=None,
                    url=url,
                    abstract_or_summary=summary,
                    citation_count=None,
                    open_access=True,
                    extra_metadata={"sectionName": item.get("sectionName")},
                )
            )

        return articles

