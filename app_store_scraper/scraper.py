"""Core App Store scraper implementation."""

import logging
from typing import List, Optional, Dict, Any, Union
from urllib.parse import quote

from .models import AppDetails, Review, SearchResult
from .categories import (
    Category, Collection, CATEGORY_NAMES,
    get_all_categories, get_all_game_categories,
    parse_category, is_valid_category
)
from .utils import RateLimiter, safe_request, chunk_list, ProgressTracker

logger = logging.getLogger(__name__)


class AppStoreScraper:
    """Scraper for iOS App Store data."""

    # API endpoints
    SEARCH_URL = "https://itunes.apple.com/search"
    LOOKUP_URL = "https://itunes.apple.com/lookup"
    RSS_URL = "https://itunes.apple.com/{country}/rss/{collection}/limit={limit}/genre={genre}/json"
    RSS_URL_NO_GENRE = "https://itunes.apple.com/{country}/rss/{collection}/limit={limit}/json"
    REVIEWS_URL = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"

    def __init__(
        self,
        country: str = 'us',
        language: str = 'en',
        requests_per_minute: int = 20
    ):
        """Initialize the scraper.

        Args:
            country: Two-letter country code (default: 'us')
            language: Language code (default: 'en')
            requests_per_minute: Rate limit for API calls
        """
        self.country = country.lower()
        self.language = language.lower()
        self.rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def search(
        self,
        query: str,
        limit: int = 50,
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Search for apps by keyword.

        Args:
            query: Search term
            limit: Maximum number of results (max 200)
            country: Country code (uses instance default if not specified)

        Returns:
            List of AppDetails objects
        """
        country = country or self.country
        limit = min(limit, 200)  # iTunes API max

        params = {
            'term': query,
            'country': country,
            'media': 'software',
            'entity': 'software',
            'limit': limit
        }

        logger.info(f"Searching for '{query}' in {country.upper()}")

        response = safe_request(
            self.SEARCH_URL,
            params=params,
            rate_limiter=self.rate_limiter
        )
        data = response.json()

        results = []
        for item in data.get('results', []):
            try:
                app = AppDetails.from_itunes_response(item)
                results.append(app)
            except Exception as e:
                logger.warning(f"Failed to parse app: {e}")

        logger.info(f"Found {len(results)} apps")
        return results

    def get_app_details(
        self,
        app_id: Union[int, str],
        country: Optional[str] = None
    ) -> Optional[AppDetails]:
        """Get detailed information for a single app.

        Args:
            app_id: iTunes track ID or bundle ID
            country: Country code

        Returns:
            AppDetails object or None if not found
        """
        country = country or self.country

        # Determine if it's a track ID or bundle ID
        params = {'country': country}
        if isinstance(app_id, int) or app_id.isdigit():
            params['id'] = int(app_id)
        else:
            params['bundleId'] = app_id

        logger.debug(f"Fetching app details for {app_id}")

        try:
            response = safe_request(
                self.LOOKUP_URL,
                params=params,
                rate_limiter=self.rate_limiter
            )
            data = response.json()

            results = data.get('results', [])
            if not results:
                logger.warning(f"App not found: {app_id}")
                return None

            return AppDetails.from_itunes_response(results[0])

        except Exception as e:
            logger.error(f"Failed to fetch app {app_id}: {e}")
            return None

    def get_app_details_batch(
        self,
        app_ids: List[Union[int, str]],
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Get details for multiple apps.

        Args:
            app_ids: List of app IDs
            country: Country code

        Returns:
            List of AppDetails objects
        """
        country = country or self.country
        results = []

        # iTunes API allows up to 200 IDs per request
        for chunk in chunk_list(app_ids, 200):
            # Filter to numeric IDs only (bundle IDs need individual lookup)
            numeric_ids = [id for id in chunk if str(id).isdigit()]
            bundle_ids = [id for id in chunk if not str(id).isdigit()]

            # Batch lookup for numeric IDs
            if numeric_ids:
                params = {
                    'id': ','.join(map(str, numeric_ids)),
                    'country': country
                }

                try:
                    response = safe_request(
                        self.LOOKUP_URL,
                        params=params,
                        rate_limiter=self.rate_limiter
                    )
                    data = response.json()

                    for item in data.get('results', []):
                        try:
                            app = AppDetails.from_itunes_response(item)
                            results.append(app)
                        except Exception as e:
                            logger.warning(f"Failed to parse app: {e}")

                except Exception as e:
                    logger.error(f"Batch lookup failed: {e}")

            # Individual lookup for bundle IDs
            for bundle_id in bundle_ids:
                app = self.get_app_details(bundle_id, country)
                if app:
                    results.append(app)

        return results

    def get_top_apps(
        self,
        category_id: Optional[int] = None,
        collection: str = Collection.TOP_FREE,
        limit: int = 100,
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Get top apps from a collection.

        Args:
            category_id: Category/genre ID (None for all categories)
            collection: Collection type (TOP_FREE, TOP_PAID, etc.)
            limit: Number of apps to fetch (max 200)
            country: Country code

        Returns:
            List of AppDetails objects
        """
        country = country or self.country
        limit = min(limit, 200)

        if category_id:
            url = self.RSS_URL.format(
                country=country,
                collection=collection,
                limit=limit,
                genre=category_id
            )
        else:
            url = self.RSS_URL_NO_GENRE.format(
                country=country,
                collection=collection,
                limit=limit
            )

        logger.info(f"Fetching top {limit} apps from {collection}")
        if category_id:
            logger.info(f"Category: {CATEGORY_NAMES.get(category_id, category_id)}")

        try:
            response = safe_request(url, rate_limiter=self.rate_limiter)
            data = response.json()

            feed = data.get('feed', {})
            entries = feed.get('entry', [])

            if not entries:
                logger.warning("No apps found in feed")
                return []

            # Extract app IDs from RSS feed
            app_ids = []
            for entry in entries:
                app_id = entry.get('id', {}).get('attributes', {}).get('im:id')
                if app_id:
                    app_ids.append(int(app_id))

            logger.info(f"Found {len(app_ids)} apps, fetching details...")

            # Get full details for each app
            return self.get_app_details_batch(app_ids, country)

        except Exception as e:
            logger.error(f"Failed to fetch top apps: {e}")
            return []

    def get_apps_by_category(
        self,
        category: Union[int, str],
        limit: int = 100,
        collection: str = Collection.TOP_FREE,
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Get apps from a specific category.

        Args:
            category: Category ID or name
            limit: Number of apps to fetch
            collection: Collection type
            country: Country code

        Returns:
            List of AppDetails objects
        """
        category_id = parse_category(category)

        if category_id is None:
            logger.error(f"Invalid category: {category}")
            return []

        return self.get_top_apps(
            category_id=category_id,
            collection=collection,
            limit=limit,
            country=country
        )

    def get_developer_apps(
        self,
        developer_id: int,
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Get all apps by a developer.

        Args:
            developer_id: Developer/artist ID
            country: Country code

        Returns:
            List of AppDetails objects
        """
        country = country or self.country

        params = {
            'id': developer_id,
            'entity': 'software',
            'country': country
        }

        logger.info(f"Fetching apps for developer {developer_id}")

        try:
            response = safe_request(
                self.LOOKUP_URL,
                params=params,
                rate_limiter=self.rate_limiter
            )
            data = response.json()

            results = []
            for item in data.get('results', []):
                # Skip the artist entry
                if item.get('wrapperType') == 'artist':
                    continue

                try:
                    app = AppDetails.from_itunes_response(item)
                    results.append(app)
                except Exception as e:
                    logger.warning(f"Failed to parse app: {e}")

            logger.info(f"Found {len(results)} apps")
            return results

        except Exception as e:
            logger.error(f"Failed to fetch developer apps: {e}")
            return []

    def get_reviews(
        self,
        app_id: int,
        country: Optional[str] = None,
        pages: int = 10
    ) -> List[Review]:
        """Get reviews for an app.

        Args:
            app_id: App ID
            country: Country code
            pages: Number of pages to fetch (max 10, 50 reviews per page)

        Returns:
            List of Review objects
        """
        country = country or self.country
        pages = min(pages, 10)  # Max 10 pages available

        logger.info(f"Fetching reviews for app {app_id} ({pages} pages)")

        reviews = []
        for page in range(1, pages + 1):
            url = self.REVIEWS_URL.format(
                country=country,
                page=page,
                app_id=app_id
            )

            try:
                response = safe_request(url, rate_limiter=self.rate_limiter)
                data = response.json()

                feed = data.get('feed', {})
                entries = feed.get('entry', [])

                if not entries:
                    logger.debug(f"No more reviews on page {page}")
                    break

                # First entry is app info, skip it
                review_entries = entries[1:] if len(entries) > 1 else []

                for entry in review_entries:
                    try:
                        review = Review.from_rss_entry(entry, app_id, country)
                        reviews.append(review)
                    except Exception as e:
                        logger.warning(f"Failed to parse review: {e}")

            except Exception as e:
                logger.warning(f"Failed to fetch reviews page {page}: {e}")
                break

        logger.info(f"Fetched {len(reviews)} reviews")
        return reviews

    def get_similar_apps(
        self,
        app_id: int,
        country: Optional[str] = None
    ) -> List[AppDetails]:
        """Get apps similar to the specified app.

        Note: This uses the app's category to find similar apps.

        Args:
            app_id: App ID
            country: Country code

        Returns:
            List of similar AppDetails objects
        """
        country = country or self.country

        # First get the app's category
        app = self.get_app_details(app_id, country)
        if not app:
            return []

        # Get top apps from the same category
        similar = self.get_top_apps(
            category_id=app.primary_genre_id,
            limit=50,
            country=country
        )

        # Filter out the original app
        return [a for a in similar if a.app_id != app_id]

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all available categories.

        Returns:
            List of category dictionaries
        """
        return get_all_categories() + get_all_game_categories()

    def scrape_all_categories(
        self,
        limit_per_category: int = 50,
        collection: str = Collection.TOP_FREE,
        country: Optional[str] = None,
        include_games: bool = True
    ) -> Dict[str, List[AppDetails]]:
        """Scrape top apps from all categories.

        Args:
            limit_per_category: Apps to fetch per category
            collection: Collection type
            country: Country code
            include_games: Include game subcategories

        Returns:
            Dictionary mapping category names to app lists
        """
        country = country or self.country
        results = {}

        categories = get_all_categories()
        if include_games:
            categories.extend(get_all_game_categories())

        total = len(categories)
        tracker = ProgressTracker(total, "Scraping categories")

        for cat in categories:
            cat_name = cat['name']
            cat_id = cat['id']

            logger.info(f"Scraping category: {cat_name}")

            apps = self.get_top_apps(
                category_id=cat_id,
                collection=collection,
                limit=limit_per_category,
                country=country
            )

            results[cat_name] = apps
            tracker.update()
            logger.info(tracker)

        return results
