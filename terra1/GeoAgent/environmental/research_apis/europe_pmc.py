"""Europe PMC Scientific Literature Client."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text

logger = logging.getLogger(__name__)


class EuropePMCClient(BaseResearchProvider):
    """Client for the Europe PMC REST API (Biomedical & Environmental Health Research)."""

    BASE_URL = "https://europepmc.org/RestWebService/rest/search"

    def __init__(
        self,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(name="Europe PMC", timeout_seconds=timeout_seconds, session=session)

    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        clean_q = query.strip()
        if not clean_q:
            return []

        params = {
            "query": clean_q,
            "format": "json",
            "pageSize": min(max(1, limit), 25),
            "resultType": "core",
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout_seconds,
                headers={"Accept": "application/json", "User-Agent": "TerraPulse/2.0"},
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("Europe PMC query failed: %s", exc)
            return []

        results = data.get("resultList", {}).get("result", [])
        articles: List[ArticleMetadata] = []

        for item in results:
            title = clean_text(item.get("title", ""))
            if not title:
                continue

            # Authors
            author_str = item.get("authorString", "")
            authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []

            # Journal / Publication
            journal = (
                item.get("journalTitle")
                or item.get("journalInfo", {}).get("journal", {}).get("title", "")
                or "Europe PMC"
            )

            # Year
            pub_year = str(item.get("pubYear", ""))

            # DOI & Identifiers
            doi = item.get("doi")
            pmid = item.get("pmid")

            # Link URL
            url = ""
            if doi:
                url = f"https://doi.org/{doi}"
            elif pmid:
                url = f"https://europepmc.org/article/MED/{pmid}"
            elif item.get("id"):
                url = f"https://europepmc.org/article/{item.get('source', 'MED')}/{item.get('id')}"

            # Abstract & Citations
            abstract = clean_text(item.get("abstractText", ""))
            cited_by = item.get("citedByCount")
            is_oa = item.get("isOpenAccess", "").upper() == "Y"

            articles.append(
                ArticleMetadata(
                    source_provider="Europe PMC",
                    title=title,
                    authors=authors,
                    publication_name=clean_text(journal),
                    publication_date=pub_year,
                    doi=doi,
                    url=url,
                    abstract_or_summary=abstract,
                    citation_count=cited_by,
                    open_access=is_oa,
                    extra_metadata={"pmid": pmid, "source": item.get("source")},
                )
            )

        return articles

