"""Environmental research, literature, and news API integration package."""

from environmental.research_apis.base import ArticleMetadata, BaseResearchProvider, clean_text
from environmental.research_apis.europe_pmc import EuropePMCClient
from environmental.research_apis.crossref import CrossrefClient
from environmental.research_apis.openalex import OpenAlexClient
from environmental.research_apis.semantic_scholar import SemanticScholarClient
from environmental.research_apis.the_guardian import GuardianNewsClient
from environmental.research_apis.gdelt import GDELTNewsClient
from environmental.research_apis.aggregator import ResearchAggregator

_default_aggregator = ResearchAggregator()


def search_academic_literature(query: str, limit_per_source: int = 4):
    """Search peer-reviewed academic literature (OpenAlex, Europe PMC, Crossref, Semantic Scholar)."""
    return _default_aggregator.search_academic(query, limit_per_source)


def search_environmental_news(query: str, limit_per_source: int = 4):
    """Search news archives and global media (The Guardian, GDELT)."""
    return _default_aggregator.search_news(query, limit_per_source)


def search_all_research(query: str, limit_per_source: int = 3):
    """Search across both scientific journals and news platforms concurrently."""
    return _default_aggregator.search_all(query, limit_per_source)


__all__ = [
    "ArticleMetadata",
    "BaseResearchProvider",
    "clean_text",
    "EuropePMCClient",
    "CrossrefClient",
    "OpenAlexClient",
    "SemanticScholarClient",
    "GuardianNewsClient",
    "GDELTNewsClient",
    "ResearchAggregator",
    "search_academic_literature",
    "search_environmental_news",
    "search_all_research",
]

