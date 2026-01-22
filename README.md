# iOS App Store Scraper

A Python library and CLI tool for extracting app data from the iOS App Store using Apple's iTunes Search API and RSS feeds.

**Features:**
- Search apps by keyword
- Scrape top apps from any category
- Get detailed app information (25+ fields)
- Fetch user reviews
- Filter games by keywords (single-player, Unity, etc.)
- Export to CSV or Excel

## Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install package
pip install -e .
```

## Usage

### Command Line

```bash
# Search for apps
appstore search "fitness tracker" --limit 50 --output results.csv

# Get apps from a category (by ID or name)
appstore category 6027 --limit 100 --output health.xlsx
appstore category "Health & Fitness" --limit 100

# Get app details
appstore app 333903271 --reviews

# Get all apps by a developer
appstore developer 389801252 --output apps.csv

# List available categories
appstore categories --games

# Scrape all categories at once
appstore all-categories --limit 50 --output all_apps.xlsx
```

### Single-Player Game Finder (Keyword Filtering)

Find single-player/offline games using keyword filtering on app descriptions:

```bash
# Basic: scrape all game categories and filter
appstore singleplayer-games --output singleplayer.csv

# Extended: also search with 300+ keywords for broader coverage
appstore singleplayer-games --include-search --output singleplayer.csv

# Filter for Unity-built games only
appstore singleplayer-games --filter-unity --output unity_games.csv

# Include paid apps and show statistics
appstore singleplayer-games --include-paid --stats --output all_sp_games.csv

# Combine options
appstore singleplayer-games --include-search --filter-unity --stats --output unity_sp.csv
```

**Options:**
| Option | Description |
|--------|-------------|
| `--include-search` | Search with 300+ keywords for more results |
| `--include-paid` | Include paid apps (default: free only) |
| `--filter-unity` | Filter for Unity-built games |
| `--stats` | Show filter statistics |
| `--collection` | top_free, top_paid, or top_grossing |

### Python Library

```python
from app_store_scraper import AppStoreScraper, Category, CSVExporter

# Initialize
scraper = AppStoreScraper(country='us')

# Search
apps = scraper.search("productivity", limit=20)

# Get apps by category
health_apps = scraper.get_apps_by_category(Category.HEALTH_FITNESS, limit=100)

# Get app details
app = scraper.get_app_details(333903271)
print(f"{app.name} - {app.rating_average}/5")

# Get reviews
reviews = scraper.get_reviews(333903271, pages=5)

# Export
CSVExporter.export_apps(apps, "output.csv")
```

#### Using Filters in Python

```python
from app_store_scraper import (
    AppStoreScraper,
    GameCategory,
    SINGLE_PLAYER_FILTER,
    UNITY_FILTER,
    apply_filter
)

scraper = AppStoreScraper()

# Get games from a category
games = scraper.get_apps_by_category(GameCategory.ACTION, limit=200)

# Filter for single-player games
result = apply_filter(games, SINGLE_PLAYER_FILTER)
print(f"Found {result.matched_count} single-player games")
print(f"Match rate: {result.match_rate:.1f}%")

# Chain filters for Unity single-player games
unity_result = apply_filter(result.filtered_apps, UNITY_FILTER)
print(f"Found {unity_result.matched_count} Unity single-player games")
```

### Common Options

| Option | Description |
|--------|-------------|
| `-l, --limit` | Max results (default varies, max 200) |
| `-c, --country` | Country code (default: us) |
| `-o, --output` | Output file (.csv or .xlsx) |
| `-v, --verbose` | Verbose output |
