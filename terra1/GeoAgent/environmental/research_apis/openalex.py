"""OpenAlex Scholarly Works Client."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


def _reconstruct_inverted_index(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstruct continuous abstract text from OpenAlex inverted index representation."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    pos_map: List[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        if isinstance(positions, list):
            for pos in positions:
                pos_map.append((pos, word))
    pos_map.sort(key=lambda x: x[0])
    return " ".join(word for _, word in pos_map)


class OpenAlexClient(BaseResearchProvider):
    """Client for the OpenAlex Works API (Open Scholarly Knowledge Graph)."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(
        self,
        polite_email: Optional[str] = None,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="OpenAlex", timeout_seconds=timeout_seconds, session=session)
        self.polite_email = polite_email or os.getenv("OPENALEX_POLITE_EMAIL", "terrapulse-research@ccvr.org")

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        params = {
            "search": clean_q,
            "per_page": min(max(1, limit), 25),
            "mailto": self.polite_email,
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
            logger.warning("OpenAlex query failed: %s", exc)
            return []

        results = data.get("results", [])
        articles: List[ArticleMetadata] = []

        for item in results:
            title = clean_text(item.get("display_name") or item.get("title", ""))
            if not title:
                continue

            # Authors
            authors: List[str] = []
            for authorship in item.get("authorships", []):
                name = authorship.get("author", {}).get("display_name")
                if name:
                    authors.append(name.strip())

            # Primary Location / Source Journal
            primary_loc = item.get("primary_location") or {}
            source = primary_loc.get("source") or {}
            pub_name = clean_text(source.get("display_name", "") or "OpenAlex Index")

            # Date
            pub_year = str(item.get("publication_year") or "")

            # Identifiers & URLs
            doi_raw = item.get("doi")
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None
            url = primary_loc.get("landing_page_url") or doi_raw or item.get("id", "")

            # Abstract from inverted index
            abstract_inv = item.get("abstract_inverted_index")
            abstract = clean_text(_reconstruct_inverted_index(abstract_inv))

            citation_count = item.get("cited_by_count")
            is_oa = bool(item.get("open_access", {}).get("is_oa"))

            # Concepts / Topics
            concepts = [
                c.get("display_name") for c in item.get("concepts", [])[:5] if c.get("display_name")
            ]

            articles.append(
                ArticleMetadata(
                    source_provider="OpenAlex",
                    title=title,
                    authors=authors,
                    publication_name=pub_name,
                    publication_date=pub_year,
                    doi=doi,
                    url=url,
                    abstract_or_summary=abstract,
                    citation_count=citation_count,
                    open_access=is_oa,
                    relevance_score=item.get("relevance_score"),
                    extra_metadata={"concepts": concepts},
                )
            )

        return articles

