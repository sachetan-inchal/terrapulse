"""Crossref Scientific Literature Client."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


class CrossrefClient(BaseResearchProvider):
    """Client for the Crossref REST API (DOI & Scholarly Publication Index)."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(
        self,
        polite_email: Optional[str] = None,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="Crossref", timeout_seconds=timeout_seconds, session=session)
        self.polite_email = polite_email or os.getenv("CROSSREF_POLITE_EMAIL", "terrapulse-research@ccvr.org")

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        params = {
            "query": clean_q,
            "rows": min(max(1, limit), 25),
            "sort": "relevance",
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": f"TerraPulse/2.0 (mailto:{self.polite_email})",
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
            logger.warning("Crossref query failed: %s", exc)
            return []

        items = data.get("message", {}).get("items", [])
        articles: List[ArticleMetadata] = []

        for item in items:
            titles = item.get("title", [])
            title = clean_text(titles[0] if titles else "")
            if not title:
                continue

            # Authors
            authors: List[str] = []
            for author_entry in item.get("author", []):
                given = author_entry.get("given", "").strip()
                family = author_entry.get("family", "").strip()
                name = author_entry.get("name", "").strip()
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)
                elif name:
                    authors.append(name)

            # Publication container
            containers = item.get("container-title", [])
            pub_name = clean_text(containers[0] if containers else "Scholarly Publication")

            # Publication date
            date_parts = item.get("issued", {}).get("date-parts", [[]])[0]
            pub_date = "-".join(str(p).zfill(2) for p in date_parts) if date_parts else ""

            doi = item.get("DOI")
            url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
            abstract = clean_text(item.get("abstract", ""))
            citation_count = item.get("is-referenced-by-count")

            articles.append(
                ArticleMetadata(
                    source_provider="Crossref",
                    title=title,
                    authors=authors,
                    publication_name=pub_name,
                    publication_date=pub_date,
                    doi=doi,
                    url=url,
                    abstract_or_summary=abstract,
                    citation_count=citation_count,
                    open_access=bool(item.get("license")),
                    relevance_score=item.get("score"),
                )
            )

        return articles

