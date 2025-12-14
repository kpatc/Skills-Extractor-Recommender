"""
Initialisation du package skill_extractor.
"""

from .scrapping.scraper import scrape_all_sources
from .nlp.text_cleaner import clean_offers_pipeline
from .nlp.skills_extractor import extract_skills_pipeline
from .modelling.clustering import cluster_offers
from .recommendtion.recommender import generate_recommendations_pipeline

__all__ = [
    "scrape_all_sources",
    "clean_offers_pipeline",
    "extract_skills_pipeline",
    "cluster_offers",
    "generate_recommendations_pipeline",
]
