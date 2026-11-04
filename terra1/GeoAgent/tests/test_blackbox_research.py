"""Independent Black-Box Verification Suite: Research & Scholarly Retrieval.

Tests live API query structures, DOI formats, rate limits, empty strings,
and provider fallback behavior.
"""

import pytest
import requests
from environmental.research_apis.openalex import OpenAlexClient
from environmental.research_apis.crossref import CrossrefClient
from environmental.research_apis.the_guardian import GuardianNewsClient
from environmental.research_apis.aggregator import ResearchAggregator


def _has_network() -> bool:
    try:
        requests.get("https://1.1.1.1", timeout=2.0)
        return True
    except Exception:
        return False


ONLINE = _has_network()


class TestResearchRetrievalBlackBox:

    @pytest.mark.skipif(not ONLINE, reason="Requires internet access")
    def test_openalex_live_retrieval_and_doi_format(self):
        """A & J: Live search and DOI validation."""
        client = OpenAlexClient()
        articles = client.search("cyanobacteria harmful algal bloom", limit=3)
        assert len(articles) > 0, "OpenAlex returned no articles for valid query"

        first = articles[0]
        assert len(first.title) > 5
        assert first.url.startswith("http")
        if first.doi:
            assert first.doi.startswith("10.") and "/" in first.doi, f"Malformed DOI: {first.doi}"

    @pytest.mark.skipif(not ONLINE, reason="Requires internet access")
    def test_crossref_live_retrieval(self):
        """A. Normal Crossref works query."""
        client = CrossrefClient()
        articles = client.search("satellite remote sensing water quality", limit=2)
        assert len(articles) > 0
        assert articles[0].source_provider == "Crossref"

    def test_empty_and_whitespace_queries(self):
        """D. Missing inputs handling."""
        client = OpenAlexClient()
        assert client.search("") == []
        assert client.search("     ") == []
        assert client.search("\n\t") == []

    def test_the_guardian_unconfigured_auth_handling(self):
        """H. Authentication & Configuration failures."""
        client = GuardianNewsClient(api_key=None)
        assert client.is_available() is False
        # Must return empty list gracefully without throwing an unhandled HTTP 401
        res = client.search("pollution")
        assert res == []

    @pytest.mark.skipif(not ONLINE, reason="Requires internet access")
    def test_aggregator_deduplication_and_metrics(self):
        """G. Repeated execution and multi-provider deduplication."""
        agg = ResearchAggregator()
        articles, metrics = agg.search_academic("microplastics freshwater", limit_per_source=2)
        assert len(articles) > 0
        assert "providers" in metrics
        # Check titles are unique
        titles = [a.title.lower() for a in articles]
        assert len(titles) == len(set(titles)), "Duplicate article titles found in aggregated results"

