"""App Store category definitions."""

from enum import IntEnum
from typing import Dict, Optional, List


class Category(IntEnum):
    """Primary App Store categories."""

    BUSINESS = 6000
    WEATHER = 6001
    UTILITIES = 6002
    TRAVEL = 6003
    SPORTS = 6004
    SOCIAL_NETWORKING = 6005
    REFERENCE = 6006
    PRODUCTIVITY = 6007
    PHOTO_VIDEO = 6008
    NEWS = 6009
    NAVIGATION = 6010
    MUSIC = 6011
    LIFESTYLE = 6012
    GAMES = 6014
    FINANCE = 6015
    ENTERTAINMENT = 6016
    EDUCATION = 6017
    BOOKS = 6018
    MEDICAL = 6020
    MAGAZINES_NEWSPAPERS = 6021
    CATALOGS = 6022
    FOOD_DRINK = 6023
    SHOPPING = 6024
    STICKERS = 6025
    DEVELOPER_TOOLS = 6026
    HEALTH_FITNESS = 6027
    GRAPHICS_DESIGN = 6028


class GameCategory(IntEnum):
    """Game subcategories."""

    ACTION = 7001
    ADVENTURE = 7002
    ARCADE = 7003
    BOARD = 7004
    CARD = 7005
    CASINO = 7006
    DICE = 7007
    EDUCATIONAL = 7008
    FAMILY = 7009
    MUSIC = 7011
    PUZZLE = 7012
    RACING = 7013
    ROLE_PLAYING = 7014
    SIMULATION = 7015
    SPORTS = 7016
    STRATEGY = 7017
    TRIVIA = 7018
    WORD = 7019


class Collection:
    """App Store collection types for top charts."""

    TOP_FREE = 'topfreeapplications'
    TOP_PAID = 'toppaidapplications'
    TOP_GROSSING = 'topgrossingapplications'
    NEW_APPS = 'newapplications'
    NEW_FREE = 'newfreeapplications'
    NEW_PAID = 'newpaidapplications'


# Category name mappings
CATEGORY_NAMES: Dict[int, str] = {
    # Primary categories
    6000: 'Business',
    6001: 'Weather',
    6002: 'Utilities',
    6003: 'Travel',
    6004: 'Sports',
    6005: 'Social Networking',
    6006: 'Reference',
    6007: 'Productivity',
    6008: 'Photo & Video',
    6009: 'News',
    6010: 'Navigation',
    6011: 'Music',
    6012: 'Lifestyle',
    6014: 'Games',
    6015: 'Finance',
    6016: 'Entertainment',
    6017: 'Education',
    6018: 'Books',
    6020: 'Medical',
    6021: 'Magazines & Newspapers',
    6022: 'Catalogs',
    6023: 'Food & Drink',
    6024: 'Shopping',
    6025: 'Stickers',
    6026: 'Developer Tools',
    6027: 'Health & Fitness',
    6028: 'Graphics & Design',

    # Game subcategories
    7001: 'Action',
    7002: 'Adventure',
    7003: 'Arcade',
    7004: 'Board',
    7005: 'Card',
    7006: 'Casino',
    7007: 'Dice',
    7008: 'Educational',
    7009: 'Family',
    7011: 'Music Games',
    7012: 'Puzzle',
    7013: 'Racing',
    7014: 'Role Playing',
    7015: 'Simulation',
    7016: 'Sports Games',
    7017: 'Strategy',
    7018: 'Trivia',
    7019: 'Word',
}

# Reverse lookup: name to ID
CATEGORY_IDS: Dict[str, int] = {name.lower(): id for id, name in CATEGORY_NAMES.items()}


def get_category_name(category_id: int) -> Optional[str]:
    """Get category name by ID."""
    return CATEGORY_NAMES.get(category_id)


def get_category_id(name: str) -> Optional[int]:
    """Get category ID by name (case-insensitive)."""
    return CATEGORY_IDS.get(name.lower())


def get_all_categories() -> List[Dict[str, any]]:
    """Get all primary categories as list of dicts."""
    return [
        {'id': cat_id, 'name': name}
        for cat_id, name in CATEGORY_NAMES.items()
        if 6000 <= cat_id < 7000
    ]


def get_all_game_categories() -> List[Dict[str, any]]:
    """Get all game subcategories as list of dicts."""
    return [
        {'id': cat_id, 'name': name}
        for cat_id, name in CATEGORY_NAMES.items()
        if 7000 <= cat_id < 8000
    ]


def is_valid_category(category_id: int) -> bool:
    """Check if category ID is valid."""
    return category_id in CATEGORY_NAMES


def parse_category(category: str | int) -> Optional[int]:
    """Parse category from ID or name.

    Args:
        category: Category ID (int) or name (str)

    Returns:
        Category ID if valid, None otherwise
    """
    if isinstance(category, int):
        return category if is_valid_category(category) else None

    if isinstance(category, str):
        # Try parsing as int first
        try:
            cat_id = int(category)
            return cat_id if is_valid_category(cat_id) else None
        except ValueError:
            pass

        # Try as name
        return get_category_id(category)

    return None
