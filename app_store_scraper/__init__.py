"""App Store Scraper - iOS App Store data extraction library."""

__version__ = '1.0.0'

from .scraper import AppStoreScraper
from .models import AppDetails, Review, SearchResult, CategoryInfo
from .categories import (
    Category,
    GameCategory,
    Collection,
    CATEGORY_NAMES,
    get_category_name,
    get_category_id,
    get_all_categories,
    get_all_game_categories,
    is_valid_category,
    parse_category
)
from .exporters import (
    CSVExporter,
    ExcelExporter,
    export_data
)
from .utils import RateLimiter
from .filters import (
    KeywordFilter,
    SINGLE_PLAYER_FILTER,
    UNITY_FILTER,
    FilterResult,
    apply_filter
)

__all__ = [
    # Main scraper
    'AppStoreScraper',

    # Models
    'AppDetails',
    'Review',
    'SearchResult',
    'CategoryInfo',

    # Categories
    'Category',
    'GameCategory',
    'Collection',
    'CATEGORY_NAMES',
    'get_category_name',
    'get_category_id',
    'get_all_categories',
    'get_all_game_categories',
    'is_valid_category',
    'parse_category',

    # Exporters
    'CSVExporter',
    'ExcelExporter',
    'export_data',

    # Filters
    'KeywordFilter',
    'SINGLE_PLAYER_FILTER',
    'UNITY_FILTER',
    'FilterResult',
    'apply_filter',

    # Utils
    'RateLimiter',
]
