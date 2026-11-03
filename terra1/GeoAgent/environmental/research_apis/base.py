"""Base models, interfaces, and utilities for scientific & news research providers."""

from __future__ import annotations

import re
import html
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import requests


@dataclass
class ArticleMetadata:
    """Standardized metadata structure for an academic paper or news article."""
    source_provider: str
    title: str
    authors: List[str] = field(default_factory=list)
    publication_name: str = ""
    publication_date: str = ""
    doi: Optional[str] = None
    url: str = ""
    abstract_or_summary: str = ""
    citation_count: Optional[int] = None
    open_access: bool = False
    relevance_score: Optional[float] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "source_provider": self.source_provider,
            "title": self.title,
            "authors": self.authors,
            "publication_name": self.publication_name,
            "publication_date": self.publication_date,
            "doi": self.doi,
            "url": self.url,
            "abstract_or_summary": self.abstract_or_summary,
            "citation_count": self.citation_count,
            "open_access": self.open_access,
            "relevance_score": self.relevance_score,
            "extra_metadata": self.extra_metadata,
        }


def clean_text(raw_text: Optional[str]) -> str:
    """Strip XML/HTML tags and decode HTML entities from text snippets."""
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    # Remove HTML/XML tags like <i>, </i>, <jats:p>, etc.
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize excessive whitespace
    return re.sub(r"\s+", " ", text).strip()


class BaseResearchProvider(ABC):
    """Abstract base class for research and newspaper data providers."""

    def __init__(
        self,
        name: str,
        timeout_seconds: float = 8.0,
        session: Optional[requests.Session] = None,
    ):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[ArticleMetadata]:
        """Execute a search query against the provider's API.
        
        Args:
            query: The search keywords or phrases.
            limit: Maximum number of results to retrieve.
            
        Returns:
            List of standardized ArticleMetadata objects.
        """
        pass

    def is_available(self) -> bool:
        """Check if any mandatory credentials or prerequisites are met."""
        return True

