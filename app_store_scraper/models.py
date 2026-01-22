"""Data models for App Store scraper."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class AppDetails:
    """Represents detailed information about an iOS app."""

    # Identifiers
    app_id: int
    bundle_id: str
    name: str

    # Description
    description: str = ""

    # Developer info
    developer_name: str = ""
    developer_id: int = 0
    developer_url: str = ""
    developer_website: str = ""  # sellerUrl - actual developer website

    # Pricing
    price: float = 0.0
    currency: str = "USD"
    is_free: bool = True

    # Categories
    primary_genre: str = ""
    primary_genre_id: int = 0
    genres: List[str] = field(default_factory=list)
    genre_ids: List[int] = field(default_factory=list)

    # Ratings
    rating_average: float = 0.0
    rating_count: int = 0
    current_version_rating: float = 0.0
    current_version_rating_count: int = 0

    # Content rating
    content_rating: str = ""

    # Technical details
    size_bytes: int = 0
    minimum_os_version: str = ""
    version: str = ""

    # Dates
    release_date: str = ""
    updated_date: str = ""

    # Release notes
    release_notes: str = ""

    # Languages
    languages: List[str] = field(default_factory=list)

    # URLs
    url: str = ""
    icon_url: str = ""
    screenshot_urls: List[str] = field(default_factory=list)
    ipad_screenshot_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        data = asdict(self)
        # Convert lists to comma-separated strings for CSV compatibility
        data['genres'] = ', '.join(self.genres) if self.genres else ''
        data['genre_ids'] = ', '.join(map(str, self.genre_ids)) if self.genre_ids else ''
        data['languages'] = ', '.join(self.languages) if self.languages else ''
        data['screenshot_urls'] = ', '.join(self.screenshot_urls) if self.screenshot_urls else ''
        data['ipad_screenshot_urls'] = ', '.join(self.ipad_screenshot_urls) if self.ipad_screenshot_urls else ''
        return data

    def to_dict_full(self) -> dict:
        """Convert to dictionary preserving list types."""
        return asdict(self)

    @classmethod
    def from_itunes_response(cls, data: dict) -> 'AppDetails':
        """Create AppDetails from iTunes API response."""
        return cls(
            app_id=data.get('trackId', 0),
            bundle_id=data.get('bundleId', ''),
            name=data.get('trackName', ''),
            description=data.get('description', ''),
            developer_name=data.get('artistName', ''),
            developer_id=data.get('artistId', 0),
            developer_url=data.get('artistViewUrl', ''),
            developer_website=data.get('sellerUrl', ''),
            price=data.get('price', 0.0),
            currency=data.get('currency', 'USD'),
            is_free=data.get('price', 0.0) == 0,
            primary_genre=data.get('primaryGenreName', ''),
            primary_genre_id=data.get('primaryGenreId', 0),
            genres=data.get('genres', []),
            genre_ids=data.get('genreIds', []),
            rating_average=data.get('averageUserRating', 0.0),
            rating_count=data.get('userRatingCount', 0),
            current_version_rating=data.get('averageUserRatingForCurrentVersion', 0.0),
            current_version_rating_count=data.get('userRatingCountForCurrentVersion', 0),
            content_rating=data.get('contentAdvisoryRating', ''),
            size_bytes=int(data.get('fileSizeBytes', 0) or 0),
            minimum_os_version=data.get('minimumOsVersion', ''),
            version=data.get('version', ''),
            release_date=data.get('releaseDate', ''),
            updated_date=data.get('currentVersionReleaseDate', ''),
            release_notes=data.get('releaseNotes', ''),
            languages=data.get('languageCodesISO2A', []),
            url=data.get('trackViewUrl', ''),
            icon_url=data.get('artworkUrl512', data.get('artworkUrl100', '')),
            screenshot_urls=data.get('screenshotUrls', []),
            ipad_screenshot_urls=data.get('ipadScreenshotUrls', [])
        )


@dataclass
class Review:
    """Represents a user review for an app."""

    review_id: str
    app_id: int
    title: str
    content: str
    rating: int
    author: str
    version: str = ""
    date: str = ""
    country: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return asdict(self)

    @classmethod
    def from_rss_entry(cls, entry: dict, app_id: int, country: str = 'us') -> 'Review':
        """Create Review from RSS feed entry."""
        return cls(
            review_id=entry.get('id', {}).get('label', ''),
            app_id=app_id,
            title=entry.get('title', {}).get('label', ''),
            content=entry.get('content', {}).get('label', ''),
            rating=int(entry.get('im:rating', {}).get('label', 0)),
            author=entry.get('author', {}).get('name', {}).get('label', ''),
            version=entry.get('im:version', {}).get('label', ''),
            date=entry.get('updated', {}).get('label', ''),
            country=country
        )


@dataclass
class SearchResult:
    """Represents a search result (minimal app info)."""

    app_id: int
    bundle_id: str
    name: str
    developer_name: str
    icon_url: str
    rating_average: float = 0.0
    rating_count: int = 0
    price: float = 0.0
    is_free: bool = True
    primary_genre: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return asdict(self)

    @classmethod
    def from_itunes_response(cls, data: dict) -> 'SearchResult':
        """Create SearchResult from iTunes API response."""
        return cls(
            app_id=data.get('trackId', 0),
            bundle_id=data.get('bundleId', ''),
            name=data.get('trackName', ''),
            developer_name=data.get('artistName', ''),
            icon_url=data.get('artworkUrl100', ''),
            rating_average=data.get('averageUserRating', 0.0),
            rating_count=data.get('userRatingCount', 0),
            price=data.get('price', 0.0),
            is_free=data.get('price', 0.0) == 0,
            primary_genre=data.get('primaryGenreName', '')
        )


@dataclass
class CategoryInfo:
    """Represents an App Store category."""

    category_id: int
    name: str
    parent_id: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return asdict(self)
