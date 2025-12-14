"""
Module d'initialisation pour le package scraping.
"""

from .scraper import (
    scrape_all_sources,
    ReKruteScraper,
    EmploiMaScraper,
    LinkedInJobsScraper,
    _generate_test_data,
)

__all__ = [
    "scrape_all_sources",
    "ReKruteScraper",
    "EmploiMaScraper",
    "LinkedInJobsScraper",
    "_generate_test_data",
]
