#!/usr/bin/env python3
"""Setup script for App Store Scraper."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''

setup(
    name='app-store-scraper',
    version='1.0.0',
    description='iOS App Store scraper for extracting app data by category, search, or app ID',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/app-store-scraper',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.28.0',
        'pandas>=1.5.0',
        'openpyxl>=3.0.0',
        'click>=8.0.0',
        'rich>=12.0.0',
        'tenacity>=8.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'appstore=app_store_scraper.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='app-store, ios, scraper, itunes, apple, apps, data-extraction',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/app-store-scraper/issues',
        'Source': 'https://github.com/yourusername/app-store-scraper',
    },
)
