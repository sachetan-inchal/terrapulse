"""Unit and regression tests for environmental research APIs (Phase 1)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import requests

from environmental.research_apis.base import ArticleMetadata, clean_text
from environmental.research_apis.europe_pmc import EuropePMCClient
from environmental.research_apis.crossref import CrossrefClient
from environmental.research_apis.openalex import OpenAlexClient, _reconstruct_inverted_index
from environmental.research_apis.semantic_scholar import SemanticScholarClient
from environmental.research_apis.the_guardian import GuardianNewsClient
from environmental.research_apis.gdelt import GDELTNewsClient, _format_seendate
from environmental.research_apis.aggregator import ResearchAggregator


class TestResearchAPIs(unittest.TestCase):

    def test_clean_text(self):
        raw = "<jats:p>Heavy metals such as <i>mercury</i> &amp; lead.</jats:p>"
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "Heavy metals such as mercury & lead.")
        self.assertEqual(clean_text(None), "")

    def test_europe_pmc_success(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultList": {
                "result": [
                    {
                        "title": "Bioaccumulation of mercury in aquatic ecosystems",
                        "authorString": "Kumar A, Rao S, Smith J",
                        "journalTitle": "Environmental Science & Technology",
                        "pubYear": "2023",
                        "doi": "10.1021/acs.est.12345",
                        "pmid": "37123456",
                        "abstractText": "Mercury concentrations were measured in fish tissues.",
                        "citedByCount": 42,
                        "isOpenAccess": "Y",
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response

        client = EuropePMCClient(session=mock_session)
        articles = client.search("mercury pollution")

        self.assertEqual(len(articles), 1)
        art = articles[0]
        self.assertEqual(art.source_provider, "Europe PMC")
        self.assertEqual(art.title, "Bioaccumulation of mercury in aquatic ecosystems")
        self.assertEqual(art.authors, ["Kumar A", "Rao S", "Smith J"])
        self.assertEqual(art.publication_name, "Environmental Science & Technology")
        self.assertEqual(art.publication_date, "2023")
        self.assertEqual(art.doi, "10.1021/acs.est.12345")
        self.assertEqual(art.url, "https://doi.org/10.1021/acs.est.12345")
        self.assertEqual(art.citation_count, 42)
        self.assertTrue(art.open_access)

    def test_europe_pmc_error_handling(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timed out")

        client = EuropePMCClient(session=mock_session)
        articles = client.search("mercury")
        self.assertEqual(articles, [])

    def test_crossref_success(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "title": ["Urban lake eutrophication and chemical foam events"],
                        "author": [
                            {"given": "TV", "family": "Ramachandra"},
                            {"name": "Energy & Wetlands Research Group"},
                        ],
                        "container-title": ["Journal of Hydrology"],
                        "issued": {"date-parts": [[2022, 6, 15]]},
                        "DOI": "10.1016/j.jhydrol.2022.100",
                        "URL": "https://doi.org/10.1016/j.jhydrol.2022.100",
                        "abstract": "<jats:p>Investigation into surfactant discharges in Bellandur lake.</jats:p>",
                        "is-referenced-by-count": 28,
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response

        client = CrossrefClient(session=mock_session)
        articles = client.search("bellandur lake foam")

        self.assertEqual(len(articles), 1)
        art = articles[0]
        self.assertEqual(art.source_provider, "Crossref")
        self.assertEqual(art.title, "Urban lake eutrophication and chemical foam events")
        self.assertIn("TV Ramachandra", art.authors)
        self.assertEqual(art.publication_name, "Journal of Hydrology")
        self.assertEqual(art.publication_date, "2022-06-15")
        self.assertEqual(art.doi, "10.1016/j.jhydrol.2022.100")
        self.assertEqual(art.citation_count, 28)

    def test_openalex_inverted_index_and_search(self):
        inv_idx = {
            "Microplastics": [0],
            "in": [1],
            "freshwater": [2],
            "lakes": [3],
            "cause": [4],
            "ecological": [5],
            "stress.": [6],
        }
        reconstructed = _reconstruct_inverted_index(inv_idx)
        self.assertEqual(reconstructed, "Microplastics in freshwater lakes cause ecological stress.")

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "display_name": "Microplastics in Indian Urban Water Bodies",
                    "authorships": [
                        {"author": {"display_name": "Priya Sharma"}}
                    ],
                    "primary_location": {
                        "source": {"display_name": "Water Research"},
                        "landing_page_url": "https://openalex.org/W123456",
                    },
                    "publication_year": 2024,
                    "doi": "https://doi.org/10.1016/j.watres.2024.12",
                    "abstract_inverted_index": inv_idx,
                    "cited_by_count": 15,
                    "open_access": {"is_oa": True},
                    "concepts": [{"display_name": "Microplastics"}, {"display_name": "Ecosystem"}],
                }
            ]
        }
        mock_session.get.return_value = mock_response

        client = OpenAlexClient(session=mock_session)
        articles = client.search("microplastics urban water")

        self.assertEqual(len(articles), 1)
        art = articles[0]
        self.assertEqual(art.source_provider, "OpenAlex")
        self.assertEqual(art.title, "Microplastics in Indian Urban Water Bodies")
        self.assertEqual(art.doi, "10.1016/j.watres.2024.12")
        self.assertTrue(art.open_access)
        self.assertIn("Microplastics in freshwater lakes", art.abstract_or_summary)

    def test_semantic_scholar_search_and_rate_limit(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429  # Rate limited
        mock_session.get.return_value = mock_response

        client = SemanticScholarClient(session=mock_session)
        articles = client.search("sulfur dioxide emissions")
        self.assertEqual(articles, [])

        # Success case
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Satellite monitoring of atmospheric SO2 plumes",
                    "authors": [{"name": "C. Li"}, {"name": "N. Krotkov"}],
                    "year": 2021,
                    "venue": "Atmospheric Measurement Techniques",
                    "citationCount": 95,
                    "url": "https://api.semanticscholar.org/CorpusId:9999",
                    "abstract": "Sentinel-5P TROPOMI observations of sulfur dioxide.",
                    "openAccessPdf": {"url": "https://amt.copernicus.org/paper.pdf"},
                    "externalIds": {"DOI": "10.5194/amt-2021-1"},
                }
            ]
        }
        articles = client.search("sulfur dioxide emissions")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].doi, "10.5194/amt-2021-1")
        self.assertEqual(articles[0].citation_count, 95)

    def test_guardian_client(self):
        # Without API key
        client_no_key = GuardianNewsClient(api_key=None)
        self.assertFalse(client_no_key.is_available())
        self.assertEqual(client_no_key.search("pollution"), [])

        # With API key
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "results": [
                    {
                        "webTitle": "Toxic foam blankets Bengaluru lake as monsoon begins",
                        "webPublicationDate": "2023-08-14T10:00:00Z",
                        "fields": {
                            "byline": "South Asia Correspondent",
                            "headline": "Toxic foam blankets Bengaluru lake as monsoon begins",
                            "trailText": "Residents complain of chemical stench and respiratory issues.",
                            "shortUrl": "https://gu.com/p/abcde",
                            "publication": "The Guardian",
                        },
                    }
                ]
            }
        }
        mock_session.get.return_value = mock_response

        client = GuardianNewsClient(api_key="test-api-key", session=mock_session)
        self.assertTrue(client.is_available())
        articles = client.search("bengaluru lake foam")

        self.assertEqual(len(articles), 1)
        art = articles[0]
        self.assertEqual(art.source_provider, "The Guardian")
        self.assertEqual(art.publication_date, "2023-08-14")
        self.assertIn("respiratory issues", art.abstract_or_summary)

    def test_gdelt_client(self):
        self.assertEqual(_format_seendate("20240415T120000Z"), "2024-04-15")
        self.assertEqual(_format_seendate(""), "")

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Industrial wastewater discharge raises alarms in southern lakes",
                    "url": "https://deccanherald.com/news/article-12345.html",
                    "seendate": "20240502T083000Z",
                    "domain": "deccanherald.com",
                    "language": "English",
                    "sourcecountry": "IN",
                }
            ]
        }
        mock_session.get.return_value = mock_response

        client = GDELTNewsClient(session=mock_session)
        articles = client.search("industrial wastewater")

        self.assertEqual(len(articles), 1)
        art = articles[0]
        self.assertEqual(art.source_provider, "GDELT")
        self.assertEqual(art.publication_date, "2024-05-02")
        self.assertEqual(art.publication_name, "deccanherald.com")

    def test_research_aggregator_deduplication_and_sorting(self):
        # Create mock providers
        mock_p1 = MagicMock(spec=EuropePMCClient)
        mock_p1.name = "Europe PMC"
        mock_p1.is_available.return_value = True
        mock_p1.search.return_value = [
            ArticleMetadata(
                source_provider="Europe PMC",
                title="Mercury in Indian Lakes",
                authors=["Scientist A"],
                doi="10.1000/182",
                citation_count=10,
                publication_date="2021",
            ),
            ArticleMetadata(
                source_provider="Europe PMC",
                title="Unique Study on Water",
                authors=["Scientist B"],
                doi="10.1000/999",
                citation_count=50,
                publication_date="2023",
            ),
        ]

        mock_p2 = MagicMock(spec=CrossrefClient)
        mock_p2.name = "Crossref"
        mock_p2.is_available.return_value = True
        mock_p2.search.return_value = [
            # Duplicate DOI from p1
            ArticleMetadata(
                source_provider="Crossref",
                title="Mercury in Indian Lakes (Publisher Record)",
                authors=["Scientist A"],
                doi="10.1000/182",
                citation_count=10,
                publication_date="2021",
            ),
            ArticleMetadata(
                source_provider="Crossref",
                title="Airborne particulate impacts",
                authors=["Scientist C"],
                doi="10.1000/777",
                citation_count=100,
                publication_date="2022",
            ),
        ]

        mock_openalex = MagicMock(spec=OpenAlexClient)
        mock_openalex.name = "OpenAlex"
        mock_openalex.is_available.return_value = False

        mock_ss = MagicMock(spec=SemanticScholarClient)
        mock_ss.name = "Semantic Scholar"
        mock_ss.is_available.return_value = False

        mock_guardian = MagicMock(spec=GuardianNewsClient)
        mock_guardian.name = "The Guardian"
        mock_guardian.is_available.return_value = False

        mock_gdelt = MagicMock(spec=GDELTNewsClient)
        mock_gdelt.name = "GDELT"
        mock_gdelt.is_available.return_value = False

        aggregator = ResearchAggregator(
            europe_pmc=mock_p1,
            crossref=mock_p2,
            openalex=mock_openalex,
            semantic_scholar=mock_ss,
            guardian=mock_guardian,
            gdelt=mock_gdelt,
        )

        articles, metrics = aggregator.search_all("pollution", limit_per_source=2)

        # Total unique articles should be 3 (10.1000/999, 10.1000/777, 10.1000/182)
        self.assertEqual(len(articles), 3)
        dois = [a.doi for a in articles]
        self.assertIn("10.1000/182", dois)
        self.assertIn("10.1000/999", dois)
        self.assertIn("10.1000/777", dois)

        # Sorted by citations descending: 100 first, then 50, then 10
        self.assertEqual(articles[0].citation_count, 100)
        self.assertEqual(articles[1].citation_count, 50)
        self.assertEqual(articles[2].citation_count, 10)

        # Metrics verify status reporting for activity tray
        self.assertEqual(metrics["providers"]["Europe PMC"]["status"], "SUCCESS")
        self.assertEqual(metrics["providers"]["Crossref"]["status"], "SUCCESS")
        self.assertEqual(metrics["providers"]["OpenAlex"]["status"], "SKIPPED_UNCONFIGURED")


if __name__ == "__main__":
    unittest.main()
