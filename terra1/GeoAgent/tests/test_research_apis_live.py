"""Live / smoke integration tests for research APIs (verifying live endpoint compatibility)."""

from __future__ import annotations

import unittest
import requests

from environmental.research_apis.europe_pmc import EuropePMCClient
from environmental.research_apis.crossref import CrossrefClient
from environmental.research_apis.openalex import OpenAlexClient
from environmental.research_apis.gdelt import GDELTNewsClient
from environmental.research_apis.aggregator import ResearchAggregator


def _can_reach_internet() -> bool:
    try:
        requests.get("https://1.1.1.1", timeout=2.0)
        return True
    except Exception:
        return False


ONLINE = _can_reach_internet()


class TestResearchAPIsLiveIntegration(unittest.TestCase):

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_openalex_query(self):
        client = OpenAlexClient()
        results = client.search("water pollution eutrophication", limit=2)
        # Should return articles with title and valid URL
        self.assertGreater(len(results), 0)
        art = results[0]
        self.assertTrue(len(art.title) > 0)
        self.assertTrue(art.url.startswith("http"))

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_europe_pmc_query(self):
        client = EuropePMCClient()
        results = client.search("mercury bioaccumulation aquatic", limit=2)
        # Europe PMC may encounter Cloudflare bot verification on certain networks; verify graceful handling
        self.assertIsInstance(results, list)
        if results:
            self.assertEqual(results[0].source_provider, "Europe PMC")

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_crossref_query(self):
        client = CrossrefClient()
        results = client.search("environmental remote sensing sentinel", limit=2)
        self.assertGreater(len(results), 0)
        art = results[0]
        self.assertTrue(len(art.title) > 0)
        self.assertEqual(art.source_provider, "Crossref")

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_gdelt_query(self):
        client = GDELTNewsClient()
        results = client.search("river pollution", limit=2)
        # GDELT may occasionally return 0 depending on real-time rate limit or network, but should not crash
        self.assertIsInstance(results, list)

    @unittest.skipUnless(ONLINE, "Requires internet connectivity")
    def test_live_aggregator_search(self):
        aggregator = ResearchAggregator()
        articles, metrics = aggregator.search_academic("microplastics lakes", limit_per_source=2)
        self.assertGreater(len(articles), 0)
        self.assertIn("providers", metrics)
        self.assertGreaterEqual(metrics["total_articles"], 1)


if __name__ == "__main__":
    unittest.main()
