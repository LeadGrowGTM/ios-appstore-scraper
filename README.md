# iOS App Store Scraper

A Python library and CLI tool for extracting app data from the iOS App Store. Scrape any category, search any keyword, and export to CSV or Excel.

**What you can scrape:**
- Any app category (Health, Finance, Productivity, Games, etc.)
- Any search keyword
- Any specific app by ID
- Any developer's full app portfolio
- User reviews

## Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Search any keyword
python -m app_store_scraper.cli search "fitness" --limit 50 --output fitness_apps.csv
python -m app_store_scraper.cli search "meditation" --limit 100 --output meditation.xlsx

# Scrape any category
python -m app_store_scraper.cli category "Health & Fitness" --limit 100 --output health.csv
python -m app_store_scraper.cli category "Finance" --limit 50 --output finance.csv
python -m app_store_scraper.cli category "Productivity" --limit 100 --output productivity.xlsx

# Get any app's details
python -m app_store_scraper.cli app 333903271 --reviews --output app_details.xlsx

# Get all apps from a developer
python -m app_store_scraper.cli developer 389801252 --output developer_apps.csv

# List all categories
python -m app_store_scraper.cli categories --games
```

## Building Custom Scrapers

The real power is building your own scraping logic. Here's how:

### Basic Python Usage

```python
from app_store_scraper import AppStoreScraper, Category, CSVExporter

scraper = AppStoreScraper(country='us')

# Search any keyword
apps = scraper.search("your keyword here", limit=200)

# Scrape any category
apps = scraper.get_apps_by_category(Category.HEALTH_FITNESS, limit=100)
apps = scraper.get_apps_by_category(Category.FINANCE, limit=100)
apps = scraper.get_apps_by_category(Category.PRODUCTIVITY, limit=100)

# Export results
CSVExporter.export_apps(apps, "output.csv")
```

### Custom Keyword Filtering

Filter apps based on description keywords - find exactly what you need:

```python
from app_store_scraper import AppStoreScraper, KeywordFilter, apply_filter

scraper = AppStoreScraper()
apps = scraper.search("your search term", limit=200)

# Create your own filter
my_filter = KeywordFilter(
    name="My Custom Filter",

    # Apps MUST contain at least one of these in their description
    include_keywords=[
        "offline", "no internet", "single player",
        "your", "keywords", "here"
    ],

    # Apps must NOT contain any of these (optional)
    exclude_keywords=[
        "multiplayer", "online required", "pvp",
        "words", "to", "exclude"
    ]
)

# Apply filter
result = apply_filter(apps, my_filter)
print(f"Found {result.matched_count} matching apps")

# Export filtered results
CSVExporter.export_apps(result.filtered_apps, "filtered_results.csv")
```

### Example: Find Offline Finance Apps

```python
from app_store_scraper import AppStoreScraper, Category, KeywordFilter, apply_filter, CSVExporter

scraper = AppStoreScraper()
apps = scraper.get_apps_by_category(Category.FINANCE, limit=200)

offline_filter = KeywordFilter(
    name="Offline Finance",
    include_keywords=["offline", "no internet", "works offline", "without wifi"],
    exclude_keywords=["requires internet", "online only"]
)

result = apply_filter(apps, offline_filter)
CSVExporter.export_apps(result.filtered_apps, "offline_finance_apps.csv")
```

### Example: Find Meditation Apps Without Subscriptions

```python
scraper = AppStoreScraper()
apps = scraper.search("meditation", limit=200)

no_subscription_filter = KeywordFilter(
    name="No Subscription",
    include_keywords=["free", "one time", "no subscription", "premium unlock"],
    exclude_keywords=["subscription", "monthly", "yearly", "trial"]
)

result = apply_filter(apps, no_subscription_filter)
```

## Available Categories

| ID | Category | ID | Category |
|----|----------|----|----------|
| 6000 | Business | 6014 | Games |
| 6002 | Utilities | 6015 | Finance |
| 6005 | Social Networking | 6016 | Entertainment |
| 6007 | Productivity | 6017 | Education |
| 6008 | Photo & Video | 6020 | Medical |
| 6012 | Lifestyle | 6023 | Food & Drink |
| 6013 | Newsstand | 6024 | Shopping |
| 6027 | Health & Fitness | 6028 | Graphics & Design |

Run `python -m app_store_scraper.cli categories --games` to see all categories including game subcategories.

## Data Fields Exported

Each app includes: `name`, `app_id`, `developer`, `rating`, `reviews_count`, `price`, `description`, `release_date`, `version`, `size`, `category`, `developer_website`, `app_store_url`, and more.

## Options

| Option | Description |
|--------|-------------|
| `-l, --limit` | Max results (up to 200) |
| `-c, --country` | Country code (us, gb, de, jp, etc.) |
| `-o, --output` | Output file (.csv or .xlsx) |
| `-v, --verbose` | Show detailed progress |
