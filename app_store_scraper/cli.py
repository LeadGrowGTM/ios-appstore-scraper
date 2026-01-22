#!/usr/bin/env python3
"""Command-line interface for App Store Scraper."""

import sys
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from app_store_scraper import (
    AppStoreScraper,
    Category,
    Collection,
    CSVExporter,
    ExcelExporter,
    export_data,
    get_all_categories,
    get_all_game_categories,
    parse_category,
    CATEGORY_NAMES
)

console = Console()


def setup_logging(verbose: bool):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False)]
    )


def get_output_path(output: str, default_name: str) -> Path:
    """Get output file path with default extension."""
    if output:
        return Path(output)
    return Path(default_name)


def determine_format(filepath: Path) -> str:
    """Determine export format from file extension."""
    ext = filepath.suffix.lower()
    if ext in ('.xlsx', '.xls'):
        return 'xlsx'
    return 'csv'


@click.group()
@click.version_option(version='1.0.0', prog_name='appstore')
def cli():
    """iOS App Store Scraper - Extract app data from the App Store."""
    pass


@cli.command()
@click.argument('query')
@click.option('-l', '--limit', default=50, help='Maximum number of results (max 200)')
@click.option('-c', '--country', default='us', help='Country code (default: us)')
@click.option('-o', '--output', help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def search(query: str, limit: int, country: str, output: str, verbose: bool):
    """Search for apps by keyword.

    Example: appstore search "fitness tracker" --limit 100
    """
    setup_logging(verbose)

    scraper = AppStoreScraper(country=country)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description=f"Searching for '{query}'...", total=None)
        apps = scraper.search(query, limit=limit)

    if not apps:
        console.print("[yellow]No apps found[/yellow]")
        return

    console.print(f"\n[green]Found {len(apps)} apps[/green]\n")

    # Display table
    table = Table(title=f"Search Results: '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Developer", style="dim")
    table.add_column("Rating", style="yellow")
    table.add_column("Price", style="green")
    table.add_column("Category", style="magenta")

    for app in apps[:20]:  # Show first 20 in table
        price = "Free" if app.is_free else f"${app.price:.2f}"
        rating = f"{app.rating_average:.1f}" if app.rating_count > 0 else "N/A"
        table.add_row(
            str(app.app_id),
            app.name[:40],
            app.developer_name[:25],
            rating,
            price,
            app.primary_genre[:20]
        )

    console.print(table)

    if len(apps) > 20:
        console.print(f"\n[dim]Showing 20 of {len(apps)} results[/dim]")

    # Export if output specified
    if output:
        filepath = get_output_path(output, f'search_{query.replace(" ", "_")}.csv')
        export_data(apps, filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command()
@click.argument('category')
@click.option('-l', '--limit', default=100, help='Maximum number of apps (max 200)')
@click.option('-c', '--country', default='us', help='Country code')
@click.option('--collection', type=click.Choice(['top_free', 'top_paid', 'top_grossing']),
              default='top_free', help='Collection type')
@click.option('-o', '--output', help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def category(category: str, limit: int, country: str, collection: str, output: str, verbose: bool):
    """Get apps from a category.

    CATEGORY can be an ID (6027) or name ("Health & Fitness")

    Example: appstore category 6027 --limit 100
    Example: appstore category "Health & Fitness" --top-free
    """
    setup_logging(verbose)

    # Parse category
    cat_id = parse_category(category)
    if cat_id is None:
        console.print(f"[red]Invalid category: {category}[/red]")
        console.print("\nUse 'appstore categories' to see available categories")
        sys.exit(1)

    cat_name = CATEGORY_NAMES.get(cat_id, category)

    # Map collection names
    collection_map = {
        'top_free': Collection.TOP_FREE,
        'top_paid': Collection.TOP_PAID,
        'top_grossing': Collection.TOP_GROSSING
    }
    coll = collection_map[collection]

    scraper = AppStoreScraper(country=country)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description=f"Fetching {cat_name} apps...", total=None)
        apps = scraper.get_apps_by_category(cat_id, limit=limit, collection=coll)

    if not apps:
        console.print("[yellow]No apps found[/yellow]")
        return

    console.print(f"\n[green]Found {len(apps)} apps in {cat_name}[/green]\n")

    # Display table with live row-by-row animation
    import time
    from rich.live import Live

    table = Table(title=f"{cat_name} - {collection.replace('_', ' ').title()}")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="white", max_width=30)
    table.add_column("Developer", style="dim", max_width=20)
    table.add_column("Rating", style="yellow", justify="right")
    table.add_column("Reviews", style="cyan", justify="right")
    table.add_column("Price", style="green", justify="right")
    table.add_column("Website", style="cyan", max_width=22)

    with Live(table, console=console, refresh_per_second=20) as live:
        for i, app in enumerate(apps[:50], 1):
            price = "Free" if app.is_free else f"${app.price:.2f}"
            rating = f"{app.rating_average:.1f}" if app.rating_count > 0 else "N/A"
            reviews = f"{app.rating_count:,}" if app.rating_count > 0 else "-"
            website = app.developer_website if app.developer_website else "-"
            website = website.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")

            table.add_row(
                str(i),
                app.name[:30],
                app.developer_name[:20],
                rating,
                reviews,
                price,
                website[:22]
            )
            time.sleep(0.08)

    if len(apps) > 50:
        console.print(f"\n[dim]Showing 50 of {len(apps)} results[/dim]")

    # Export
    if output:
        filepath = get_output_path(output, f'{cat_name.replace(" ", "_").replace("&", "and")}.csv')
        export_data(apps, filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command()
@click.argument('app_id')
@click.option('-c', '--country', default='us', help='Country code')
@click.option('--reviews', is_flag=True, help='Also fetch reviews')
@click.option('--review-pages', default=5, help='Number of review pages (max 10)')
@click.option('-o', '--output', help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def app(app_id: str, country: str, reviews: bool, review_pages: int, output: str, verbose: bool):
    """Get details for a specific app.

    APP_ID can be numeric ID or bundle ID

    Example: appstore app 333903271
    Example: appstore app com.twitter.twitter --reviews
    """
    setup_logging(verbose)

    scraper = AppStoreScraper(country=country)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description="Fetching app details...", total=None)
        app_details = scraper.get_app_details(app_id)

        if app_details and reviews:
            progress.update(task, description="Fetching reviews...")
            app_reviews = scraper.get_reviews(app_details.app_id, pages=review_pages)
        else:
            app_reviews = []

    if not app_details:
        console.print(f"[red]App not found: {app_id}[/red]")
        sys.exit(1)

    # Display app info
    console.print(f"\n[bold]{app_details.name}[/bold]")
    console.print(f"[dim]by {app_details.developer_name}[/dim]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    price = "Free" if app_details.is_free else f"${app_details.price:.2f}"
    rating = f"{app_details.rating_average:.1f}/5 ({app_details.rating_count:,} ratings)"
    size_mb = app_details.size_bytes / (1024 * 1024) if app_details.size_bytes else 0

    table.add_row("App ID", str(app_details.app_id))
    table.add_row("Bundle ID", app_details.bundle_id)
    table.add_row("Price", price)
    table.add_row("Rating", rating)
    table.add_row("Category", app_details.primary_genre)
    table.add_row("Version", app_details.version)
    table.add_row("Size", f"{size_mb:.1f} MB")
    table.add_row("Min iOS", app_details.minimum_os_version)
    table.add_row("Age Rating", app_details.content_rating)
    table.add_row("Released", app_details.release_date[:10] if app_details.release_date else "")
    table.add_row("Updated", app_details.updated_date[:10] if app_details.updated_date else "")
    table.add_row("URL", app_details.url)

    console.print(table)

    # Show reviews summary
    if app_reviews:
        console.print(f"\n[bold]Reviews ({len(app_reviews)} fetched)[/bold]\n")

        for review in app_reviews[:5]:
            stars = "*" * review.rating
            console.print(f"[yellow]{stars}[/yellow] [bold]{review.title}[/bold]")
            console.print(f"[dim]{review.content[:200]}...[/dim]" if len(review.content) > 200 else f"[dim]{review.content}[/dim]")
            console.print(f"[dim]- {review.author}, v{review.version}[/dim]\n")

    # Export
    if output:
        filepath = get_output_path(output, f'app_{app_details.app_id}.xlsx')
        if app_reviews:
            ExcelExporter.export_full_report([app_details], app_reviews, filepath)
        else:
            export_data([app_details], filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command()
@click.argument('app_id', type=int)
@click.option('-c', '--country', default='us', help='Country code')
@click.option('-p', '--pages', default=10, help='Number of pages (max 10, 50 reviews each)')
@click.option('-o', '--output', help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def reviews(app_id: int, country: str, pages: int, output: str, verbose: bool):
    """Fetch reviews for an app.

    Example: appstore reviews 333903271 --pages 10
    """
    setup_logging(verbose)

    scraper = AppStoreScraper(country=country)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description=f"Fetching reviews for app {app_id}...", total=None)
        app_reviews = scraper.get_reviews(app_id, pages=pages)

    if not app_reviews:
        console.print("[yellow]No reviews found[/yellow]")
        return

    console.print(f"\n[green]Fetched {len(app_reviews)} reviews[/green]\n")

    # Rating distribution
    ratings = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in app_reviews:
        if r.rating in ratings:
            ratings[r.rating] += 1

    console.print("[bold]Rating Distribution[/bold]")
    for stars in [5, 4, 3, 2, 1]:
        count = ratings[stars]
        bar = "#" * (count // 2)
        console.print(f"{stars}* [{count:3}] {bar}")

    console.print()

    # Show recent reviews
    table = Table(title="Recent Reviews")
    table.add_column("Rating", style="yellow")
    table.add_column("Title", style="white")
    table.add_column("Author", style="dim")
    table.add_column("Version", style="cyan")

    for review in app_reviews[:10]:
        table.add_row(
            "*" * review.rating,
            review.title[:40],
            review.author[:15],
            review.version
        )

    console.print(table)

    # Export
    if output:
        filepath = get_output_path(output, f'reviews_{app_id}.csv')
        export_data(app_reviews, filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command()
@click.argument('developer_id', type=int)
@click.option('-c', '--country', default='us', help='Country code')
@click.option('-o', '--output', help='Output file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def developer(developer_id: int, country: str, output: str, verbose: bool):
    """Get all apps by a developer.

    Example: appstore developer 389801252
    """
    setup_logging(verbose)

    scraper = AppStoreScraper(country=country)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task(description=f"Fetching apps for developer {developer_id}...", total=None)
        apps = scraper.get_developer_apps(developer_id)

    if not apps:
        console.print("[yellow]No apps found[/yellow]")
        return

    developer_name = apps[0].developer_name if apps else "Unknown"
    console.print(f"\n[bold]{developer_name}[/bold]")
    console.print(f"[green]{len(apps)} apps[/green]\n")

    table = Table()
    table.add_column("Name", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Rating", style="yellow")
    table.add_column("Price", style="green")

    for app in apps:
        price = "Free" if app.is_free else f"${app.price:.2f}"
        rating = f"{app.rating_average:.1f}" if app.rating_count > 0 else "N/A"
        table.add_row(app.name[:40], app.primary_genre[:20], rating, price)

    console.print(table)

    # Export
    if output:
        filepath = get_output_path(output, f'developer_{developer_id}.csv')
        export_data(apps, filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command('categories')
@click.option('-o', '--output', help='Output file path')
@click.option('--games', is_flag=True, help='Include game subcategories')
def list_categories(output: str, games: bool):
    """List all available App Store categories.

    Example: appstore categories --games
    """
    categories = get_all_categories()

    table = Table(title="App Store Categories")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")

    for cat in categories:
        table.add_row(str(cat['id']), cat['name'])

    console.print(table)

    if games:
        console.print()
        game_cats = get_all_game_categories()

        game_table = Table(title="Game Subcategories")
        game_table.add_column("ID", style="cyan")
        game_table.add_column("Name", style="white")

        for cat in game_cats:
            game_table.add_row(str(cat['id']), cat['name'])

        console.print(game_table)
        categories.extend(game_cats)

    if output:
        from app_store_scraper.exporters import CSVExporter
        filepath = Path(output)
        CSVExporter.export_categories(categories, filepath)
        console.print(f"\n[green]Exported to {filepath}[/green]")


@cli.command('all-categories')
@click.option('-l', '--limit', default=50, help='Apps per category (max 200)')
@click.option('-c', '--country', default='us', help='Country code')
@click.option('--collection', type=click.Choice(['top_free', 'top_paid', 'top_grossing']),
              default='top_free', help='Collection type')
@click.option('--games/--no-games', default=True, help='Include game categories')
@click.option('-o', '--output', required=True, help='Output file path (.xlsx recommended)')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def all_categories(limit: int, country: str, collection: str, games: bool, output: str, verbose: bool):
    """Scrape top apps from ALL categories.

    Example: appstore all-categories --limit 50 --output all_apps.xlsx
    """
    setup_logging(verbose)

    collection_map = {
        'top_free': Collection.TOP_FREE,
        'top_paid': Collection.TOP_PAID,
        'top_grossing': Collection.TOP_GROSSING
    }
    coll = collection_map[collection]

    scraper = AppStoreScraper(country=country)

    console.print(f"[bold]Scraping all categories[/bold]")
    console.print(f"Limit: {limit} apps per category")
    console.print(f"Collection: {collection}")
    console.print(f"Include games: {games}\n")

    categories = get_all_categories()
    if games:
        categories.extend(get_all_game_categories())

    results = {}
    total_apps = 0

    with Progress(console=console) as progress:
        task = progress.add_task("Scraping categories...", total=len(categories))

        for cat in categories:
            cat_name = cat['name']
            cat_id = cat['id']

            progress.update(task, description=f"Scraping {cat_name}...")

            apps = scraper.get_apps_by_category(cat_id, limit=limit, collection=coll)
            results[cat_name] = apps
            total_apps += len(apps)

            progress.advance(task)

    console.print(f"\n[green]Scraped {total_apps} apps from {len(categories)} categories[/green]")

    # Export
    filepath = Path(output)
    ExcelExporter.export_by_category(results, filepath)
    console.print(f"[green]Exported to {filepath}[/green]")


@cli.command('singleplayer-games')
@click.option('-l', '--limit', default=200, help='Apps per category (max 200)')
@click.option('-c', '--country', default='us', help='Country code')
@click.option('--collection', type=click.Choice(['top_free', 'top_paid', 'top_grossing']),
              default='top_free', help='Collection type')
@click.option('--include-paid', is_flag=True, help='Also include paid apps')
@click.option('--include-search', is_flag=True, help='Also search with multiple keywords (slower but more results)')
@click.option('--filter-unity', is_flag=True, help='Filter for Unity games')
@click.option('--stats', is_flag=True, help='Show detailed statistics')
@click.option('-o', '--output', required=True, help='Output CSV file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def singleplayer_games(
    limit: int,
    country: str,
    collection: str,
    include_paid: bool,
    include_search: bool,
    filter_unity: bool,
    stats: bool,
    output: str,
    verbose: bool
):
    """Scrape single-player games from all game categories.

    Filters games by description keywords to find single-player games.
    Optionally filters for Unity-built games (those mentioning Unity in description).

    Use --include-search to also run multiple keyword searches for broader coverage.

    Examples:
        appstore singleplayer-games --output singleplayer_games.csv
        appstore singleplayer-games --include-search --output more_games.csv
        appstore singleplayer-games --filter-unity --output unity_sp_games.csv
        appstore singleplayer-games --include-paid --stats -o all_sp_games.csv
    """
    setup_logging(verbose)

    from app_store_scraper.filters import (
        SINGLE_PLAYER_FILTER,
        UNITY_FILTER,
        apply_filter
    )

    collection_map = {
        'top_free': Collection.TOP_FREE,
        'top_paid': Collection.TOP_PAID,
        'top_grossing': Collection.TOP_GROSSING
    }
    coll = collection_map[collection]

    scraper = AppStoreScraper(country=country)

    # Display configuration
    console.print("[bold]Single-Player Games Scraper[/bold]")
    console.print(f"Categories: All 18 game subcategories")
    console.print(f"Limit: {limit} apps per category")
    console.print(f"Collection: {collection}")
    console.print(f"Include search: {include_search}")
    console.print(f"Filter Unity: {filter_unity}")
    console.print()

    all_apps = []
    seen_ids = set()

    def add_apps(apps):
        """Add apps to all_apps, deduplicating by app_id."""
        count = 0
        for app in apps:
            if app.app_id not in seen_ids:
                seen_ids.add(app.app_id)
                all_apps.append(app)
                count += 1
        return count

    # Step 1: Scrape all game categories
    console.print("[bold]Step 1: Scraping game categories...[/bold]")

    game_categories = get_all_game_categories()

    with Progress(console=console) as progress:
        task = progress.add_task("Scraping...", total=len(game_categories))

        for cat in game_categories:
            cat_name = cat['name']
            cat_id = cat['id']

            progress.update(task, description=f"Scraping {cat_name}...")

            apps = scraper.get_apps_by_category(cat_id, limit=limit, collection=coll)
            add_apps(apps)

            if include_paid and coll != Collection.TOP_PAID:
                paid_apps = scraper.get_apps_by_category(
                    cat_id, limit=limit, collection=Collection.TOP_PAID
                )
                add_apps(paid_apps)

            progress.advance(task)

    console.print(f"[green]From categories: {len(all_apps)} unique games[/green]")

    # Step 2: Multi-keyword search (optional)
    if include_search:
        console.print("\n[bold]Step 2: Searching with multiple keywords...[/bold]")

        # Search queries designed to find single-player games
        search_queries = [
            # === GENERAL SINGLE-PLAYER TERMS ===
            "single player game",
            "singleplayer",
            "single-player",
            "offline game",
            "solo game",
            "story mode",
            "campaign mode",
            "campaign game",
            "play offline",
            "no internet required",
            "no wifi game",
            "offline play",
            "without internet",
            "no connection needed",
            "airplane mode game",
            "offline mobile game",
            "solo experience",
            "single player mobile",
            "offline ios game",
            "best offline game",
            "top offline game",
            "free offline game",
            "paid offline game",
            "premium offline game",

            # === STORY/NARRATIVE FOCUSED ===
            "story driven game",
            "story game",
            "narrative game",
            "story rich",
            "interactive story",
            "visual novel",
            "text adventure",
            "choice game",
            "episodic game",
            "interactive fiction",
            "choose your adventure",
            "story based game",
            "cinematic game",
            "narrative adventure",
            "drama game",
            "emotional game",
            "story puzzle",
            "detective story",
            "crime story game",
            "romance game",
            "dating sim",
            "otome game",

            # === RPG VARIATIONS ===
            "single player rpg",
            "offline rpg",
            "solo rpg",
            "story rpg",
            "jrpg",
            "action rpg",
            "turn based rpg",
            "dungeon crawler",
            "roguelike",
            "roguelite",
            "rpg offline",
            "role playing offline",
            "fantasy rpg",
            "medieval rpg",
            "sci fi rpg",
            "open world rpg",
            "classic rpg",
            "retro rpg",
            "pixel rpg",
            "anime rpg",
            "gacha offline",
            "hero rpg",
            "monster rpg",
            "dragon rpg",
            "knight rpg",
            "warrior rpg",
            "mage rpg",
            "loot rpg",
            "grind rpg",

            # === ADVENTURE VARIATIONS ===
            "single player adventure",
            "offline adventure",
            "solo adventure",
            "adventure game",
            "point and click",
            "exploration game",
            "mystery game",
            "escape room game",
            "hidden object",
            "puzzle adventure",
            "action adventure",
            "adventure offline",
            "explore game",
            "treasure hunt game",
            "quest game",
            "journey game",
            "epic adventure",
            "fantasy adventure",
            "space adventure",
            "pirate adventure",
            "jungle adventure",
            "ocean adventure",
            "underwater adventure",
            "cave exploration",
            "dungeon adventure",
            "tomb raider like",
            "indiana jones game",

            # === PUZZLE VARIATIONS ===
            "single player puzzle",
            "offline puzzle",
            "brain teaser",
            "logic puzzle",
            "puzzle adventure",
            "match 3",
            "block puzzle",
            "word puzzle",
            "sudoku",
            "crossword",
            "jigsaw puzzle",
            "number puzzle",
            "math puzzle",
            "physics puzzle",
            "puzzle game offline",
            "brain game",
            "mind game",
            "iq game",
            "smart game",
            "thinking game",
            "strategy puzzle",
            "merge game",
            "sort puzzle",
            "sliding puzzle",
            "tile puzzle",
            "color puzzle",
            "shape puzzle",
            "pattern game",
            "memory game",
            "concentration game",
            "trivia offline",
            "quiz offline",
            "riddle game",
            "escape puzzle",
            "room escape",
            "breakout game",

            # === ACTION VARIATIONS ===
            "single player action",
            "offline action",
            "solo action",
            "hack and slash",
            "beat em up",
            "platformer",
            "side scroller",
            "endless runner",
            "runner game",
            "action offline",
            "fighting game offline",
            "combat game",
            "battle game offline",
            "warrior game",
            "ninja game",
            "samurai game",
            "superhero game",
            "martial arts game",
            "kung fu game",
            "boxing game offline",
            "wrestling offline",
            "brawler game",
            "action platformer",
            "metroidvania",
            "souls like",
            "difficult game",
            "challenging game",
            "hardcore game",
            "retro action",
            "arcade action",
            "2d action",
            "3d action offline",

            # === STRATEGY VARIATIONS ===
            "single player strategy",
            "offline strategy",
            "turn based strategy",
            "tower defense",
            "defense game",
            "base building",
            "city builder",
            "tycoon game",
            "management game",
            "idle game",
            "clicker game",
            "strategy offline",
            "war game offline",
            "army game offline",
            "military game offline",
            "tactics game",
            "tactical rpg",
            "real time strategy",
            "rts offline",
            "empire building",
            "kingdom building",
            "civilization game",
            "colony builder",
            "factory game",
            "automation game",
            "resource management",
            "economy game",
            "trading game offline",
            "merchant game",
            "business simulation",
            "company game",
            "startup game",
            "hotel tycoon",
            "airport tycoon",
            "zoo tycoon",
            "theme park game",
            "roller coaster tycoon",
            "transport tycoon",
            "train tycoon",
            "shipping tycoon",

            # === SIMULATION VARIATIONS ===
            "single player simulation",
            "offline simulation",
            "life simulation",
            "farming game",
            "farm simulation",
            "cooking game",
            "restaurant game",
            "pet simulation",
            "virtual pet",
            "sandbox game",
            "simulation offline",
            "simulator offline",
            "life sim",
            "god game",
            "world builder",
            "village builder",
            "town builder",
            "house builder",
            "home design game",
            "interior design game",
            "garden game",
            "gardening simulation",
            "animal simulation",
            "dog simulation",
            "cat simulation",
            "horse simulation",
            "bird simulation",
            "fish simulation",
            "aquarium game",
            "zoo simulation",
            "wildlife simulation",
            "nature simulation",
            "weather simulation",
            "space simulation",
            "planet simulation",
            "universe simulation",

            # === RACING VARIATIONS ===
            "single player racing",
            "offline racing",
            "solo racing",
            "car game offline",
            "drift game",
            "bike racing",
            "racing offline",
            "race game offline",
            "street racing",
            "drag racing",
            "rally racing",
            "formula racing",
            "kart racing",
            "motorcycle game",
            "motocross game",
            "atv game",
            "truck racing",
            "bus simulator",
            "taxi simulator",
            "driving simulator",
            "car simulator",
            "traffic game",
            "highway game",
            "speed game",
            "nitro racing",
            "turbo racing",

            # === SHOOTER VARIATIONS ===
            "single player shooter",
            "offline shooter",
            "solo shooter",
            "fps offline",
            "sniper game",
            "zombie shooter",
            "shooter offline",
            "gun game offline",
            "shooting game offline",
            "first person shooter offline",
            "third person shooter offline",
            "war shooter",
            "military shooter",
            "army shooter",
            "commando game",
            "special ops game",
            "tactical shooter",
            "stealth game",
            "spy game",
            "agent game",
            "hitman like",
            "assassin game",
            "bow and arrow game",
            "archery game",
            "target shooting",
            "hunting simulator",
            "deer hunter",
            "duck hunting",
            "zombie survival",
            "zombie apocalypse",
            "alien shooter",
            "robot shooter",
            "mech game",
            "tank game offline",
            "helicopter game offline",
            "jet fighter game",
            "space shooter",
            "spaceship game",
            "galaga like",
            "bullet hell",
            "shmup",

            # === ARCADE VARIATIONS ===
            "offline arcade",
            "retro arcade",
            "classic arcade",
            "casual offline",
            "arcade offline",
            "old school game",
            "vintage game",
            "80s game",
            "90s game",
            "nostalgic game",
            "simple game offline",
            "easy game offline",
            "quick game offline",
            "time killer offline",
            "addictive game offline",
            "fun offline game",
            "entertaining offline",
            "highscore game",
            "leaderboard offline",
            "pinball game",
            "pacman like",
            "tetris like",
            "brick breaker",
            "breakout clone",
            "pong game",
            "snake game",
            "flappy game",
            "tap game offline",
            "swipe game",
            "one touch game",

            # === SPORTS VARIATIONS ===
            "offline sports",
            "single player sports",
            "golf game",
            "basketball offline",
            "football offline",
            "soccer offline",
            "sports offline",
            "sport game offline",
            "tennis game offline",
            "baseball offline",
            "hockey offline",
            "cricket offline",
            "rugby offline",
            "volleyball offline",
            "bowling game",
            "pool game offline",
            "billiards offline",
            "snooker game",
            "darts game",
            "table tennis",
            "ping pong game",
            "badminton game",
            "skating game",
            "skateboard game",
            "snowboard game",
            "skiing game",
            "surfing game",
            "swimming game",
            "athletics game",
            "olympics game",
            "extreme sports",
            "bmx game",
            "motocross offline",

            # === CARD/BOARD VARIATIONS ===
            "solitaire",
            "card game offline",
            "board game offline",
            "chess offline",
            "mahjong",
            "poker offline",
            "blackjack offline",
            "rummy offline",
            "uno offline",
            "hearts game",
            "spades game",
            "bridge game",
            "gin rummy",
            "freecell",
            "spider solitaire",
            "klondike solitaire",
            "patience game",
            "checkers offline",
            "backgammon offline",
            "dominoes offline",
            "yahtzee offline",
            "dice game offline",
            "monopoly offline",
            "scrabble offline",
            "word board game",
            "trivia board game",
            "strategy board game",
            "classic board game",
            "family board game",
            "party game offline",

            # === HORROR/SURVIVAL ===
            "horror game",
            "survival horror",
            "scary game",
            "survival game offline",
            "horror offline",
            "creepy game",
            "spooky game",
            "haunted game",
            "ghost game",
            "monster game",
            "zombie game offline",
            "vampire game",
            "werewolf game",
            "demon game",
            "evil game",
            "dark game",
            "nightmare game",
            "terror game",
            "fear game",
            "thriller game",
            "suspense game",
            "psychological horror",
            "jump scare game",
            "survival craft",
            "wilderness survival",
            "island survival",
            "desert survival",
            "apocalypse game",
            "post apocalyptic",
            "wasteland game",
            "bunker game",
            "shelter game",

            # === CASUAL/RELAXING ===
            "relaxing game",
            "casual game offline",
            "zen game",
            "meditation game",
            "coloring game",
            "calming game",
            "peaceful game",
            "stress relief game",
            "asmr game",
            "satisfying game",
            "oddly satisfying",
            "cozy game",
            "wholesome game",
            "cute game",
            "kawaii game",
            "adorable game",
            "pretty game",
            "beautiful game",
            "artistic game",
            "creative game",
            "art game",
            "painting game",
            "sketch game",
            "doodle game",
            "decoration game",
            "makeover game",
            "fashion game offline",
            "dress up offline",
            "makeup game offline",
            "nail art game",
            "hair salon game",
            "spa game",

            # === KIDS/EDUCATIONAL ===
            "kids game offline",
            "educational game",
            "learning game",
            "children game offline",
            "toddler game",
            "baby game",
            "preschool game",
            "kindergarten game",
            "school game",
            "alphabet game",
            "abc game",
            "numbers game",
            "counting game",
            "math game kids",
            "reading game",
            "spelling game",
            "vocabulary game",
            "language learning game",
            "science game kids",
            "geography game",
            "history game",
            "animal game kids",
            "dinosaur game kids",
            "space game kids",
            "nature game kids",
            "puzzle kids",
            "coloring kids",
            "drawing kids",
            "music kids",
            "piano kids",

            # === SPECIFIC POPULAR TYPES ===
            "open world game",
            "sandbox offline",
            "crafting game",
            "building game",
            "minecraft like",
            "survival craft",
            "anime game",
            "pixel game",
            "retro game",
            "classic game",
            "indie game offline",
            "premium game",
            "paid game no ads",
            "no ads game",
            "ad free game",
            "full game offline",
            "complete game",
            "finished game",
            "polished game",
            "quality game offline",
            "award winning game",
            "best mobile game",
            "top rated offline",
            "highly rated offline",
            "popular offline game",
            "famous game offline",
            "legendary game",
            "cult classic game",
            "must play game",
            "essential game",

            # === SIMULATORS ===
            "fishing game",
            "hunting game",
            "flight simulator",
            "train simulator",
            "truck simulator",
            "parking game",
            "physics game",
            "drawing game",
            "music game offline",
            "rhythm game offline",
            "airplane simulator",
            "helicopter simulator",
            "ship simulator",
            "boat simulator",
            "submarine simulator",
            "spaceship simulator",
            "rocket simulator",
            "drone simulator",
            "rc simulator",
            "farming simulator",
            "construction simulator",
            "mining simulator",
            "logging simulator",
            "mechanic simulator",
            "surgery simulator",
            "doctor simulator",
            "cooking simulator",
            "barista simulator",
            "bakery simulator",
            "supermarket simulator",

            # === UNIQUE/NICHE ===
            "time travel game",
            "dimension game",
            "portal game",
            "gravity game",
            "magnet game",
            "electricity game",
            "water physics game",
            "fire game",
            "ice game",
            "wind game",
            "elemental game",
            "magic game offline",
            "wizard game",
            "witch game",
            "fairy game",
            "elf game",
            "dwarf game",
            "orc game",
            "goblin game",
            "troll game",
            "giant game",
            "titan game",
            "god simulator",
            "angel game",
            "demon hunter",
            "exorcist game",
            "paranormal game",
            "ufo game",
            "alien game offline",
            "mutant game",
            "cyborg game",
            "android game offline",
            "ai game",
            "hacker game",
            "programmer game",
            "coding game",
            "logic game",
            "circuit game",
            "engineering game",
            "invention game",
            "laboratory game",
            "experiment game",
            "chemistry game",
            "biology game",
            "evolution game",
            "genetics game",
            "virus game",
            "bacteria game",
            "cell game",
            "microscope game",
            "telescope game",
            "astronomy game",
            "constellation game",
            "solar system game",
            "galaxy game",
            "black hole game",
            "quantum game",
            "atom game",
            "particle game",
        ]

        with Progress(console=console) as progress:
            task = progress.add_task("Searching...", total=len(search_queries))

            for query in search_queries:
                progress.update(task, description=f"Searching '{query}'...")

                try:
                    apps = scraper.search(query, limit=200)
                    # Only keep games (primary_genre_id 6014 or genre_ids containing game categories)
                    game_apps = [a for a in apps if a.primary_genre_id == 6014 or
                                 (a.genre_ids and any(gid >= 7000 and gid < 8000 for gid in
                                  [int(x.strip()) for x in str(a.genre_ids).split(',') if x.strip().isdigit()]))]
                    new_count = add_apps(game_apps)
                    if verbose and new_count > 0:
                        console.print(f"  '{query}': +{new_count} new games")
                except Exception as e:
                    if verbose:
                        console.print(f"  [yellow]'{query}': error - {e}[/yellow]")

                progress.advance(task)

        console.print(f"[green]After search: {len(all_apps)} unique games total[/green]")

    unique_apps = all_apps
    console.print(f"\n[green]Total collected: {len(unique_apps)} unique games[/green]")

    # Apply filters
    filtered_apps = unique_apps
    filters_applied = []

    console.print("\n[bold]Filtering for single-player games...[/bold]")
    result = apply_filter(filtered_apps, SINGLE_PLAYER_FILTER)
    filtered_apps = result.filtered_apps
    filters_applied.append(("Single-Player", result))
    console.print(f"[green]Found {result.matched_count} single-player games ({result.match_rate:.1f}% match rate)[/green]")

    if filter_unity:
        console.print("\n[bold]Filtering for Unity games...[/bold]")
        result = apply_filter(filtered_apps, UNITY_FILTER)
        filtered_apps = result.filtered_apps
        filters_applied.append(("Unity", result))
        console.print(f"[green]Found {result.matched_count} Unity games ({result.match_rate:.1f}% match rate)[/green]")

    # Show statistics
    if stats and filters_applied:
        console.print("\n[bold]Statistics:[/bold]")

        for filter_name, result in filters_applied:
            console.print(f"\n{filter_name} Filter:")
            console.print(f"  - Total scanned: {result.total_scanned}")
            console.print(f"  - Matched: {result.matched_count}")
            console.print(f"  - Excluded: {result.excluded_count}")
            console.print(f"  - Match rate: {result.match_rate:.1f}%")

            if result.category_breakdown:
                console.print("  - By category:")
                for cat, count in sorted(result.category_breakdown.items(),
                                        key=lambda x: x[1], reverse=True)[:10]:
                    console.print(f"      {cat}: {count}")

    # Export to CSV
    console.print(f"\n[bold]Exporting to CSV...[/bold]")

    if not filtered_apps:
        console.print("[yellow]No games matched the filters[/yellow]")
        return

    filepath = Path(output)
    CSVExporter.export_apps(filtered_apps, filepath)

    console.print(f"\n[green]Exported {len(filtered_apps)} games to {filepath}[/green]")

    # Final summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total scraped: {len(unique_apps)}")
    console.print(f"  After filters: {len(filtered_apps)}")
    if unique_apps:
        console.print(f"  Retention rate: {(len(filtered_apps)/len(unique_apps)*100):.1f}%")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
