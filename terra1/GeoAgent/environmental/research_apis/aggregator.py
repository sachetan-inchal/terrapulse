"""Research and news aggregation coordinator."""

from __future__ import annotations

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider
from environmental.research_apis.europe_pmc import EuropePMCClient
from environmental.research_apis.crossref import CrossrefClient
from environmental.research_apis.openalex import OpenAlexClient
from environmental.research_apis.semantic_scholar import SemanticScholarClient
from environmental.research_apis.the_guardian import GuardianNewsClient
from environmental.research_apis.gdelt import GDELTNewsClient

logger = logging.getLogger(__name__)


def _normalize_title(title: str) -> str:
    """Normalize title for fuzzy deduplication."""
    import re
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


class ResearchAggregator:
    """Aggregates and coordinates scientific and newspaper research providers."""

    def __init__(
        self,
        europe_pmc: Optional[EuropePMCClient] = None,
        crossref: Optional[CrossrefClient] = None,
        openalex: Optional[OpenAlexClient] = None,
        semantic_scholar: Optional[SemanticScholarClient] = None,
        guardian: Optional[GuardianNewsClient] = None,
        gdelt: Optional[GDELTNewsClient] = None,
    ):
        self.europe_pmc = europe_pmc or EuropePMCClient()
        self.crossref = crossref or CrossrefClient()
        self.openalex = openalex or OpenAlexClient()
        self.semantic_scholar = semantic_scholar or SemanticScholarClient()
        self.guardian = guardian or GuardianNewsClient()
        self.gdelt = gdelt or GDELTNewsClient()

        self._cache: Dict[str, Tuple[float, List[ArticleMetadata], Dict[str, Any]]] = {}
        self._cache_ttl_seconds = 300.0  # 5 minutes TTL

    @property
    def academic_providers(self) -> List[BaseResearchProvider]:
        return [self.openalex, self.europe_pmc, self.crossref, self.semantic_scholar]

    @property
    def news_providers(self) -> List[BaseResearchProvider]:
        return [self.guardian, self.gdelt]

    def _query_provider(
        self, provider: BaseResearchProvider, query: str, limit: int
    ) -> Tuple[str, List[ArticleMetadata], Dict[str, Any]]:
        """Query a single provider and measure execution metrics."""
        start_t = time.perf_counter()
        if not provider.is_available():
            return (
                provider.name,
                [],
                {
                    "status": "SKIPPED_UNCONFIGURED",
                    "latency_ms": 0.0,
                    "count": 0,
                    "message": "API key or prerequisite not configured.",
                },
            )

        try:
            results = provider.search(query=query, limit=limit)
            latency = round((time.perf_counter() - start_t) * 1000, 1)
            return (
                provider.name,
                results,
                {"status": "SUCCESS", "latency_ms": latency, "count": len(results)},
            )
        except Exception as exc:
            latency = round((time.perf_counter() - start_t) * 1000, 1)
            logger.warning("Provider %s failed: %s", provider.name, exc)
            return (
                provider.name,
                [],
                {"status": "ERROR", "latency_ms": latency, "count": 0, "error": str(exc)},
            )

    def search_academic(
        self, query: str, limit_per_source: int = 4
    ) -> Tuple[List[ArticleMetadata], Dict[str, Any]]:
        """Search across all academic and scientific journal providers."""
        return self._search_providers(self.academic_providers, query, limit_per_source)

    def search_news(
        self, query: str, limit_per_source: int = 4
    ) -> Tuple[List[ArticleMetadata], Dict[str, Any]]:
        """Search across all newspaper and media providers."""
        return self._search_providers(self.news_providers, query, limit_per_source)

    def search_all(
        self, query: str, limit_per_source: int = 3
    ) -> Tuple[List[ArticleMetadata], Dict[str, Any]]:
        """Search across all academic journals and news providers concurrently."""
        cache_key = f"all:{query.strip().lower()}:{limit_per_source}"
        now = time.time()
        if cache_key in self._cache:
            ts, cached_articles, cached_metrics = self._cache[cache_key]
            if now - ts < self._cache_ttl_seconds:
                return cached_articles, cached_metrics

        all_providers = self.academic_providers + self.news_providers
        articles, metrics = self._search_providers(all_providers, query, limit_per_source)
        self._cache[cache_key] = (now, articles, metrics)
        return articles, metrics

    def _search_providers(
        self, providers: List[BaseResearchProvider], query: str, limit_per_source: int
    ) -> Tuple[List[ArticleMetadata], Dict[str, Any]]:
        results_by_provider: Dict[str, List[ArticleMetadata]] = {}
        provider_metrics: Dict[str, Any] = {}

        # Concurrently execute queries with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            futures = {
                executor.submit(self._query_provider, p, query, limit_per_source): p
                for p in providers
            }
            for fut in as_completed(futures):
                prov_name, items, metrics = fut.result()
                results_by_provider[prov_name] = items
                provider_metrics[prov_name] = metrics

        # Deduplicate results across providers
        seen_dois = set()
        seen_titles = set()
        combined: List[ArticleMetadata] = []

        for prov in providers:
            for item in results_by_provider.get(prov.name, []):
                norm_title = _normalize_title(item.title)
                if item.doi and item.doi.lower() in seen_dois:
                    continue
                if norm_title in seen_titles and len(norm_title) > 10:
                    continue

                if item.doi:
                    seen_dois.add(item.doi.lower())
                if norm_title:
                    seen_titles.add(norm_title)

                combined.append(item)

        # Sort: academic papers with citation counts first, then by date
        combined.sort(
            key=lambda x: (
                x.citation_count or 0 if x.source_provider in ["Europe PMC", "OpenAlex", "Crossref", "Semantic Scholar"] else -1,
                x.publication_date or "",
            ),
            reverse=True,
        )

        overall_metrics = {
            "query": query,
            "total_articles": len(combined),
            "providers": provider_metrics,
        }

        return combined, overall_metrics

