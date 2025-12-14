"""
Module d'initialisation pour le package recommendation.
Inclut: recommandations par profil + analyse CV personnalisée (extension optionnelle).
"""

from .recommender import SkillRecommender, generate_recommendations_pipeline
from .profile_matcher import ProfileMatcher, CandidateProfile
from .skill_gap import SkillGapAnalyzer
from .cv_personalizer import CVPersonalizer

__all__ = [
    # Recommandations principales
    "SkillRecommender",
    "generate_recommendations_pipeline",
    
    # Extension CV Recommender (optionnelle)
    "ProfileMatcher",
    "CandidateProfile",
    "SkillGapAnalyzer",
    "CVPersonalizer",
]
