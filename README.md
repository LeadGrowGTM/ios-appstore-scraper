# iOS App Store Scraper

A Python library and CLI tool for extracting app data from the iOS App Store. Scrape **any category** - health apps, finance apps, games, productivity tools, and more.

**Features:**
- Search apps by keyword
- Scrape top apps from **any** of 24 categories + 18 game subcategories
- Get detailed app information (25+ fields including developer website)
- Fetch user reviews
- Build custom filters with keyword matching
- Export to CSV or Excel

## Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install package (enables CLI commands)
pip install -e .
```

## Usage

### Command Line

```bash
# Search for apps
appstore search "fitness tracker" --limit 50 --output results.csv

# Get apps from ANY category (by ID or name)
appstore category 6027 --limit 100 --output health_apps.xlsx
appstore category "Finance" --limit 100 --output finance_apps.csv
appstore category "Productivity" --limit 50

# Get app details
appstore app 333903271 --reviews

# Get all apps by a developer
appstore developer 389801252 --output apps.csv

# List all available categories
appstore categories --games

# Scrape ALL categories at once
appstore all-categories --limit 50 --output all_apps.xlsx
```

### Category IDs

| ID | Category | ID | Category |
|----|----------|----|----------|
| 6000 | Business | 6015 | Finance |
| 6002 | Utilities | 6016 | Entertainment |
| 6007 | Productivity | 6017 | Education |
| 6008 | Photo & Video | 6023 | Food & Drink |
| 6012 | Lifestyle | 6024 | Shopping |
| 6014 | Games | 6027 | Health & Fitness |

Run `appstore categories --games` to see all 42 categories.

## Building Custom Scrapers

The real power is building your own scraping logic. Here's how:

### Basic: Scrape Any Category

```python
from app_store_scraper import AppStoreScraper, Category, CSVExporter

scraper = AppStoreScraper(country='us')

# Scrape health & fitness apps
health_apps = scraper.get_apps_by_category(Category.HEALTH_FITNESS, limit=200)

# Scrape finance apps
finance_apps = scraper.get_apps_by_category(Category.FINANCE, limit=200)

# Search by keyword
meditation_apps = scraper.search("meditation", limit=100)

# Export
CSVExporter.export_apps(health_apps, "health_apps.csv")
```

### Advanced: Custom Keyword Filters

Build filters to find specific types of apps:

```python
from app_store_scraper import AppStoreScraper, Category, KeywordFilter, apply_filter

# Define your own filter
MY_FILTER = KeywordFilter(
    name="My Custom Filter",
    # Apps MUST contain at least one of these in description
    include_keywords=[
        "meditation", "mindfulness", "calm", "relaxation",
        "sleep", "breathing", "stress relief"
    ],
    # Apps with these keywords are EXCLUDED
    exclude_keywords=[
        "game", "casino", "betting", "workout", "exercise"
    ]
)

# Scrape and filter
scraper = AppStoreScraper()
apps = scraper.get_apps_by_category(Category.HEALTH_FITNESS, limit=200)

result = apply_filter(apps, MY_FILTER)
print(f"Found {result.matched_count} meditation/relaxation apps")
print(f"Match rate: {result.match_rate:.1f}%")

# Export filtered results
CSVExporter.export_apps(result.filtered_apps, "meditation_apps.csv")
```

### Example: Find B2B SaaS Apps

```python
B2B_FILTER = KeywordFilter(
    name="B2B SaaS",
    include_keywords=[
        "enterprise", "business", "team", "collaboration",
        "workflow", "productivity", "crm", "project management",
        "analytics", "dashboard", "reporting"
    ],
    exclude_keywords=[
        "game", "personal", "family", "kids", "photo editor"
    ]
)

apps = scraper.get_apps_by_category(Category.BUSINESS, limit=200)
result = apply_filter(apps, B2B_FILTER)
```

### Example: Find Subscription Apps

```python
# Filter by price model
subscription_apps = [
    app for app in apps
    if "subscription" in app.description.lower()
    or "premium" in app.description.lower()
]
```

## Pre-Built Filters

Two filters are included out of the box:

```bash
# Find single-player/offline games
appstore singleplayer-games --output singleplayer.csv

# With extended search (300+ keywords)
appstore singleplayer-games --include-search --filter-unity --output unity_games.csv
```

## Data Fields

Each app includes 25+ fields:
- `app_id`, `bundle_id`, `name`
- `developer_name`, `developer_id`, `developer_website`
- `price`, `currency`, `is_free`
- `rating_average`, `rating_count`
- `primary_genre`, `description`
- `size_bytes`, `version`, `minimum_os_version`
- `release_date`, `updated_date`
- `url`, `icon_url`, `screenshot_urls`
- And more...

## Common Options

| Option | Description |
|--------|-------------|
| `-l, --limit` | Max results (max 200 per request) |
| `-c, --country` | Country code (default: us) |
| `-o, --output` | Output file (.csv or .xlsx) |
| `-v, --verbose` | Verbose output |
