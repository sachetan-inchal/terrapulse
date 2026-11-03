"""Semantic Scholar Academic Graph Client."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


class SemanticScholarClient(BaseResearchProvider):
    """Client for the Semantic Scholar Graph API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="Semantic Scholar", timeout_seconds=timeout_seconds, session=session)
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        params = {
            "query": clean_q,
            "limit": min(max(1, limit), 25),
            "fields": "title,authors,year,venue,citationCount,abstract,url,openAccessPdf,externalIds",
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "TerraPulse/2.0",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429:
                logger.warning("Semantic Scholar rate limit reached (HTTP 429).")
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("Semantic Scholar query failed: %s", exc)
            return []

        items = data.get("data", [])
        articles: List[ArticleMetadata] = []

        for item in items:
            title = clean_text(item.get("title", ""))
            if not title:
                continue

            # Authors
            authors = [
                clean_text(a.get("name", "")) for a in item.get("authors", []) if a.get("name")
            ]

            venue = clean_text(item.get("venue", "") or "Semantic Scholar")
            pub_year = str(item.get("year") or "")
            external_ids = item.get("externalIds") or {}
            doi = external_ids.get("DOI")

            url = item.get("url") or (f"https://doi.org/{doi}" if doi else "")
            abstract = clean_text(item.get("abstract", ""))
            citation_count = item.get("citationCount")
            oa_pdf = item.get("openAccessPdf")

            articles.append(
                ArticleMetadata(
                    source_provider="Semantic Scholar",
                    title=title,
                    authors=authors,
                    publication_name=venue,
                    publication_date=pub_year,
                    doi=doi,
                    url=url,
                    abstract_or_summary=abstract,
                    citation_count=citation_count,
                    open_access=bool(oa_pdf),
                    extra_metadata={"external_ids": external_ids},
                )
            )

        return articles

