"""Export functionality for App Store data."""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

import pandas as pd
from openpyxl.utils import get_column_letter

from .models import AppDetails, Review, CategoryInfo

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export data to CSV format."""

    @staticmethod
    def export_apps(
        apps: List[AppDetails],
        filepath: Union[str, Path],
        include_screenshots: bool = False
    ) -> Path:
        """Export apps to CSV file.

        Args:
            apps: List of AppDetails objects
            filepath: Output file path
            include_screenshots: Include screenshot URLs (can make CSV large)

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        if not apps:
            logger.warning("No apps to export")
            return filepath

        # Convert to dictionaries
        data = [app.to_dict() for app in apps]

        # Remove screenshot columns if not needed
        if not include_screenshots:
            for row in data:
                row.pop('screenshot_urls', None)
                row.pop('ipad_screenshot_urls', None)

        # Define column order
        columns = [
            'app_id', 'bundle_id', 'name', 'developer_name', 'developer_id', 'developer_website',
            'price', 'currency', 'is_free',
            'primary_genre', 'primary_genre_id', 'genres', 'genre_ids',
            'rating_average', 'rating_count',
            'current_version_rating', 'current_version_rating_count',
            'content_rating', 'version', 'minimum_os_version',
            'size_bytes', 'release_date', 'updated_date',
            'languages', 'url', 'icon_url', 'description', 'release_notes'
        ]

        if include_screenshots:
            columns.extend(['screenshot_urls', 'ipad_screenshot_urls'])

        # Filter to existing columns
        columns = [c for c in columns if c in data[0]]

        df = pd.DataFrame(data)
        df = df[columns]
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Exported {len(apps)} apps to {filepath}")
        return filepath

    @staticmethod
    def export_reviews(
        reviews: List[Review],
        filepath: Union[str, Path]
    ) -> Path:
        """Export reviews to CSV file.

        Args:
            reviews: List of Review objects
            filepath: Output file path

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        if not reviews:
            logger.warning("No reviews to export")
            return filepath

        data = [review.to_dict() for review in reviews]

        columns = [
            'review_id', 'app_id', 'title', 'content',
            'rating', 'author', 'version', 'date', 'country'
        ]

        df = pd.DataFrame(data)
        df = df[columns]
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Exported {len(reviews)} reviews to {filepath}")
        return filepath

    @staticmethod
    def export_categories(
        categories: List[Dict[str, Any]],
        filepath: Union[str, Path]
    ) -> Path:
        """Export categories to CSV file.

        Args:
            categories: List of category dictionaries
            filepath: Output file path

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        if not categories:
            logger.warning("No categories to export")
            return filepath

        df = pd.DataFrame(categories)
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Exported {len(categories)} categories to {filepath}")
        return filepath


class ExcelExporter:
    """Export data to Excel format."""

    @staticmethod
    def export_apps(
        apps: List[AppDetails],
        filepath: Union[str, Path],
        include_screenshots: bool = False
    ) -> Path:
        """Export apps to Excel file.

        Args:
            apps: List of AppDetails objects
            filepath: Output file path
            include_screenshots: Include screenshot URLs

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        if not apps:
            logger.warning("No apps to export")
            return filepath

        data = [app.to_dict() for app in apps]

        if not include_screenshots:
            for row in data:
                row.pop('screenshot_urls', None)
                row.pop('ipad_screenshot_urls', None)

        df = pd.DataFrame(data)

        # Write to Excel with formatting
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Apps', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Apps']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                # Cap at 50 characters
                worksheet.column_dimensions[get_column_letter(idx)].width = min(max_length + 2, 50)

        logger.info(f"Exported {len(apps)} apps to {filepath}")
        return filepath

    @staticmethod
    def export_reviews(
        reviews: List[Review],
        filepath: Union[str, Path]
    ) -> Path:
        """Export reviews to Excel file.

        Args:
            reviews: List of Review objects
            filepath: Output file path

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        if not reviews:
            logger.warning("No reviews to export")
            return filepath

        data = [review.to_dict() for review in reviews]
        df = pd.DataFrame(data)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Reviews', index=False)

        logger.info(f"Exported {len(reviews)} reviews to {filepath}")
        return filepath

    @staticmethod
    def export_full_report(
        apps: List[AppDetails],
        reviews: Optional[List[Review]] = None,
        filepath: Union[str, Path] = None,
        include_summary: bool = True
    ) -> Path:
        """Export comprehensive report with multiple sheets.

        Args:
            apps: List of AppDetails objects
            reviews: Optional list of Review objects
            filepath: Output file path
            include_summary: Include summary statistics sheet

        Returns:
            Path to exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = Path(f'app_store_report_{timestamp}.xlsx')
        else:
            filepath = Path(filepath)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Apps sheet
            if apps:
                apps_data = [app.to_dict() for app in apps]
                for row in apps_data:
                    row.pop('screenshot_urls', None)
                    row.pop('ipad_screenshot_urls', None)
                    row.pop('description', None)  # Too long for Excel cell
                    row.pop('release_notes', None)

                apps_df = pd.DataFrame(apps_data)
                apps_df.to_excel(writer, sheet_name='Apps', index=False)

            # Reviews sheet
            if reviews:
                reviews_data = [review.to_dict() for review in reviews]
                reviews_df = pd.DataFrame(reviews_data)
                reviews_df.to_excel(writer, sheet_name='Reviews', index=False)

            # Summary sheet
            if include_summary and apps:
                summary_data = {
                    'Metric': [
                        'Total Apps',
                        'Free Apps',
                        'Paid Apps',
                        'Average Rating',
                        'Average Rating Count',
                        'Average Price (Paid)',
                        'Most Common Category',
                        'Export Date'
                    ],
                    'Value': [
                        len(apps),
                        sum(1 for a in apps if a.is_free),
                        sum(1 for a in apps if not a.is_free),
                        round(sum(a.rating_average for a in apps) / len(apps), 2) if apps else 0,
                        round(sum(a.rating_count for a in apps) / len(apps), 0) if apps else 0,
                        round(
                            sum(a.price for a in apps if not a.is_free) /
                            max(sum(1 for a in apps if not a.is_free), 1),
                            2
                        ),
                        max(
                            set(a.primary_genre for a in apps),
                            key=lambda x: sum(1 for a in apps if a.primary_genre == x)
                        ) if apps else '',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Rating distribution
                if apps:
                    rating_bins = [0, 1, 2, 3, 4, 5]
                    rating_counts = []
                    for i in range(len(rating_bins) - 1):
                        count = sum(
                            1 for a in apps
                            if rating_bins[i] <= a.rating_average < rating_bins[i + 1]
                        )
                        rating_counts.append({
                            'Rating Range': f'{rating_bins[i]}-{rating_bins[i+1]}',
                            'Count': count
                        })
                    rating_df = pd.DataFrame(rating_counts)
                    rating_df.to_excel(writer, sheet_name='Rating Distribution', index=False)

                # Category breakdown
                if apps:
                    categories = {}
                    for app in apps:
                        cat = app.primary_genre
                        if cat not in categories:
                            categories[cat] = {'count': 0, 'avg_rating': 0, 'total_rating': 0}
                        categories[cat]['count'] += 1
                        categories[cat]['total_rating'] += app.rating_average

                    cat_data = []
                    for cat, data in categories.items():
                        cat_data.append({
                            'Category': cat,
                            'App Count': data['count'],
                            'Average Rating': round(data['total_rating'] / data['count'], 2)
                        })

                    cat_df = pd.DataFrame(cat_data)
                    cat_df = cat_df.sort_values('App Count', ascending=False)
                    cat_df.to_excel(writer, sheet_name='Category Breakdown', index=False)

        logger.info(f"Exported full report to {filepath}")
        return filepath

    @staticmethod
    def export_by_category(
        apps_by_category: Dict[str, List[AppDetails]],
        filepath: Union[str, Path]
    ) -> Path:
        """Export apps organized by category to Excel.

        Args:
            apps_by_category: Dictionary mapping category names to app lists
            filepath: Output file path

        Returns:
            Path to exported file
        """
        filepath = Path(filepath)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            all_apps = []

            for category, apps in apps_by_category.items():
                all_apps.extend(apps)
                if apps:
                    summary_data.append({
                        'Category': category,
                        'App Count': len(apps),
                        'Avg Rating': round(
                            sum(a.rating_average for a in apps) / len(apps), 2
                        ),
                        'Free Apps': sum(1 for a in apps if a.is_free),
                        'Paid Apps': sum(1 for a in apps if not a.is_free)
                    })

            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df = summary_df.sort_values('App Count', ascending=False)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # All apps sheet
            if all_apps:
                all_data = []
                for app in all_apps:
                    row = app.to_dict()
                    row.pop('screenshot_urls', None)
                    row.pop('ipad_screenshot_urls', None)
                    row.pop('description', None)
                    row.pop('release_notes', None)
                    all_data.append(row)

                all_df = pd.DataFrame(all_data)
                all_df.to_excel(writer, sheet_name='All Apps', index=False)

            # Individual category sheets (limit sheet name length)
            for category, apps in apps_by_category.items():
                if not apps:
                    continue

                # Excel sheet names max 31 chars
                sheet_name = category[:31].replace('/', '-').replace('\\', '-')

                data = []
                for app in apps:
                    row = app.to_dict()
                    row.pop('screenshot_urls', None)
                    row.pop('ipad_screenshot_urls', None)
                    row.pop('description', None)
                    row.pop('release_notes', None)
                    data.append(row)

                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Exported {len(all_apps)} apps across {len(apps_by_category)} categories to {filepath}")
        return filepath


def export_data(
    data: Union[List[AppDetails], List[Review], Dict[str, List[AppDetails]]],
    filepath: Union[str, Path],
    format: str = 'auto'
) -> Path:
    """Auto-detect and export data to appropriate format.

    Args:
        data: Apps, reviews, or category dict to export
        filepath: Output file path
        format: 'csv', 'xlsx', or 'auto' (detect from extension)

    Returns:
        Path to exported file
    """
    filepath = Path(filepath)

    # Detect format
    if format == 'auto':
        format = filepath.suffix.lower().lstrip('.')
        if format not in ('csv', 'xlsx', 'xls'):
            format = 'csv'

    # Detect data type and export
    if isinstance(data, dict):
        # Category dict
        if format == 'csv':
            # Flatten to single CSV
            all_apps = []
            for apps in data.values():
                all_apps.extend(apps)
            return CSVExporter.export_apps(all_apps, filepath)
        else:
            return ExcelExporter.export_by_category(data, filepath)

    elif data and isinstance(data[0], AppDetails):
        if format == 'csv':
            return CSVExporter.export_apps(data, filepath)
        else:
            return ExcelExporter.export_apps(data, filepath)

    elif data and isinstance(data[0], Review):
        if format == 'csv':
            return CSVExporter.export_reviews(data, filepath)
        else:
            return ExcelExporter.export_reviews(data, filepath)

    else:
        logger.warning("Unknown data type, cannot export")
        return filepath
