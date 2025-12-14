"""
Module d'initialisation pour le package recommendation.
"""

from .recommender import SkillRecommender, generate_recommendations_pipeline

__all__ = [
    "SkillRecommender",
    "generate_recommendations_pipeline",
]
