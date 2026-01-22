"""Keyword-based filtering utilities for app classification."""

import re
from dataclasses import dataclass, field
from typing import List

from .models import AppDetails


@dataclass
class KeywordFilter:
    """Configurable keyword filter for app descriptions."""

    name: str
    include_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    case_sensitive: bool = False

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not self.case_sensitive:
            return text.lower()
        return text

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        normalized = self._normalize_text(text)
        for keyword in keywords:
            pattern = self._normalize_text(keyword)
            # Use word boundary matching for better accuracy
            if re.search(r'\b' + re.escape(pattern) + r'\b', normalized):
                return True
        return False

    def matches(self, app: AppDetails) -> bool:
        """Check if app matches the filter criteria.

        Returns True if:
        - Description contains at least one include keyword AND
        - Description contains NO exclude keywords
        """
        description = app.description or ""

        # Must have at least one include keyword
        if self.include_keywords:
            if not self._contains_any(description, self.include_keywords):
                return False

        # Must not have any exclude keywords
        if self.exclude_keywords:
            if self._contains_any(description, self.exclude_keywords):
                return False

        return True

    def get_matched_keywords(self, app: AppDetails) -> List[str]:
        """Return list of matched include keywords for reporting."""
        description = self._normalize_text(app.description or "")
        matched = []
        for keyword in self.include_keywords:
            pattern = self._normalize_text(keyword)
            if re.search(r'\b' + re.escape(pattern) + r'\b', description):
                matched.append(keyword)
        return matched


# Pre-configured filters
SINGLE_PLAYER_FILTER = KeywordFilter(
    name="single_player",
    include_keywords=[
        "single player",
        "singleplayer",
        "single-player",
        "solo",
        "offline",
        "campaign",
        "story mode"
    ],
    exclude_keywords=[
        "multiplayer",
        "multi-player",
        "pvp",
        "co-op",
        "coop",
        "battle royale",
        "mmo",
        "online multiplayer",
        "versus",
        "online pvp"
    ]
)

UNITY_FILTER = KeywordFilter(
    name="unity",
    include_keywords=[
        "unity",
        "made with unity",
        "powered by unity"
    ],
    exclude_keywords=[],
    case_sensitive=False
)


@dataclass
class FilterResult:
    """Result of filtering operation with statistics."""

    filtered_apps: List[AppDetails]
    total_scanned: int
    matched_count: int
    excluded_count: int
    filter_name: str
    category_breakdown: dict = field(default_factory=dict)

    @property
    def match_rate(self) -> float:
        """Percentage of apps that matched."""
        if self.total_scanned == 0:
            return 0.0
        return (self.matched_count / self.total_scanned) * 100


def apply_filter(
    apps: List[AppDetails],
    keyword_filter: KeywordFilter
) -> FilterResult:
    """Apply a keyword filter to a list of apps.

    Args:
        apps: List of AppDetails to filter
        keyword_filter: KeywordFilter to apply

    Returns:
        FilterResult with filtered apps and statistics
    """
    filtered = []
    category_breakdown = {}

    for app in apps:
        if keyword_filter.matches(app):
            filtered.append(app)
            # Track by category
            cat = app.primary_genre or "Unknown"
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    return FilterResult(
        filtered_apps=filtered,
        total_scanned=len(apps),
        matched_count=len(filtered),
        excluded_count=len(apps) - len(filtered),
        filter_name=keyword_filter.name,
        category_breakdown=category_breakdown
    )
