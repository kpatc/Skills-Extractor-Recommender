"""
Module de recommandation de compétences.
"""

import logging
import sys
from typing import List, Dict, Tuple
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import STUDENT_PROFILES, TECH_SKILLS

logger = logging.getLogger(__name__)


class SkillRecommender:
    """Recommande les compétences à apprendre basées sur le profil et les clusters."""

    def __init__(self):
        self.student_profiles = STUDENT_PROFILES
        self.tech_skills = TECH_SKILLS

    def recommend_for_profile(
        self,
        profile_name: str,
        cluster_data: Dict,
        top_n: int = 10
    ) -> Dict:
        """
        Recommande les compétences pour un profil d'étudiant.
        
        Args:
            profile_name: Nom du profil (ex: "data_engineer")
            cluster_data: Données de clustering avec offres et statistiques
            top_n: Nombre de compétences à recommander
        
        Returns:
            Dictionnaire avec recommandations détaillées
        """
        if profile_name not in self.student_profiles:
            raise ValueError(f"Profil inconnu: {profile_name}")

        profile = self.student_profiles[profile_name]
        core_skills = set(profile["core_skills"])

        # Récupérer les offres du cluster pertinent
        offers = cluster_data.get("offers_clustered", [])
        cluster_stats = cluster_data.get("cluster_stats", {})

        # Filtrer les offres correspondant au cluster du profil
        profile_offers = [
            offer for offer in offers
            if offer.get("cluster") == self._get_cluster_id_for_profile(profile["cluster"])
        ]

        logger.info(f"Analyse du profil {profile_name}: {len(profile_offers)} offres trouvées")

        # Collecter toutes les compétences demandées dans ce cluster
        required_skills = []
        for offer in profile_offers:
            if "extracted_skills" in offer:
                required_skills.extend(offer["extracted_skills"])

        skill_frequency = Counter(required_skills)

        # Trier par fréquence
        top_skills = skill_frequency.most_common(top_n * 2)  # Prendre plus pour filtrer

        # Créer les recommandations
        recommendations = []

        for skill, frequency in top_skills:
            in_core = skill in core_skills

            # Calculer un score d'importance
            score = frequency / len(profile_offers) if profile_offers else 0

            recommendation = {
                "skill": skill,
                "frequency": frequency,
                "importance_score": score,
                "already_core": in_core,
                "priority": self._calculate_priority(skill, frequency, in_core),
            }

            recommendations.append(recommendation)

        # Filtrer et limiter
        recommendations = [r for r in recommendations if not r["already_core"]]
        recommendations = sorted(recommendations, key=lambda x: x["priority"], reverse=True)
        recommendations = recommendations[:top_n]

        return {
            "profile": profile_name,
            "cluster": profile["cluster"],
            "current_skills": list(core_skills),
            "recommended_skills": recommendations,
            "matching_offers_count": len(profile_offers),
            "learning_path": self._generate_learning_path(recommendations, profile),
        }

    def recommend_for_all_profiles(
        self,
        cluster_data: Dict,
        top_n: int = 10
    ) -> Dict[str, Dict]:
        """
        Génère les recommandations pour tous les profils.
        
        Args:
            cluster_data: Données de clustering
            top_n: Nombre de compétences par profil
        
        Returns:
            Dictionnaire avec recommandations par profil
        """
        results = {}

        for profile_name in self.student_profiles.keys():
            try:
                results[profile_name] = self.recommend_for_profile(
                    profile_name,
                    cluster_data,
                    top_n
                )
            except Exception as e:
                logger.error(f"Erreur pour profil {profile_name}: {e}")

        return results

    def get_skills_gap(
        self,
        profile_name: str,
        cluster_data: Dict
    ) -> Dict:
        """
        Identifie l'écart entre les compétences actuelles et demandées.
        
        Args:
            profile_name: Nom du profil
            cluster_data: Données de clustering
        
        Returns:
            Analyse de l'écart
        """
        profile = self.student_profiles[profile_name]
        current = set(profile["core_skills"])

        offers = cluster_data.get("offers_clustered", [])
        profile_offers = [
            offer for offer in offers
            if offer.get("cluster") == self._get_cluster_id_for_profile(profile["cluster"])
        ]

        # Toutes les compétences demandées
        demanded_skills = set()
        for offer in profile_offers:
            if "extracted_skills" in offer:
                demanded_skills.update(offer["extracted_skills"])

        # Écart
        missing_skills = demanded_skills - current
        extra_skills = current - demanded_skills

        return {
            "profile": profile_name,
            "current_skills": list(current),
            "demanded_skills": list(demanded_skills),
            "missing_skills": list(missing_skills),
            "extra_skills": list(extra_skills),
            "gap_percentage": (len(missing_skills) / len(demanded_skills) * 100) if demanded_skills else 0,
            "recommendations": list(sorted(missing_skills, key=demanded_skills.count)[-10:]),
        }

    def _get_cluster_id_for_profile(self, cluster_name: str) -> int:
        """Mappe le nom du cluster à son ID (simplifié)."""
        cluster_mapping = {
            "Data": 0,
            "Backend": 1,
            "DevOps": 2,
            "AI/ML": 3,
            "Frontend": 4,
        }
        return cluster_mapping.get(cluster_name, 0)

    def _calculate_priority(
        self,
        skill: str,
        frequency: int,
        in_core: bool
    ) -> float:
        """Calcule la priorité d'une compétence."""
        # Priorité = fréquence + bonus pour compétences transversales
        priority = frequency

        # Bonus pour compétences essentielles (cloud, devops, etc)
        essential_keywords = ["docker", "kubernetes", "aws", "git", "api"]
        if any(keyword in skill.lower() for keyword in essential_keywords):
            priority *= 1.5

        return priority

    def _generate_learning_path(
        self,
        recommendations: List[Dict],
        profile: Dict
    ) -> List[Dict]:
        """
        Génère un chemin d'apprentissage structuré.
        
        Args:
            recommendations: Compétences recommandées
            profile: Profil de l'étudiant
        
        Returns:
            Chemin d'apprentissage par phases
        """
        if not recommendations:
            return []

        # Diviser en 3 phases (court, moyen, long terme)
        path = []

        # Phase 1: Fondamentaux (top 30%)
        phase1_count = max(1, len(recommendations) // 3)
        path.append({
            "phase": "Fondamentaux (0-3 mois)",
            "skills": [r["skill"] for r in recommendations[:phase1_count]],
            "description": "Maîtriser les bases essentielles de votre profil",
        })

        # Phase 2: Spécialisation (30-70%)
        phase2_count = len(recommendations) - phase1_count * 2
        path.append({
            "phase": "Spécialisation (3-6 mois)",
            "skills": [r["skill"] for r in recommendations[phase1_count:phase1_count + phase2_count]],
            "description": "Approfondir les compétences clés du domaine",
        })

        # Phase 3: Avancé (70%+)
        path.append({
            "phase": "Avancé (6+ mois)",
            "skills": [r["skill"] for r in recommendations[phase1_count + phase2_count:]],
            "description": "Maîtriser les technologies avancées et spécialisées",
        })

        return [p for p in path if p["skills"]]  # Retirer les phases vides


def generate_recommendations_pipeline(cluster_data: Dict) -> Dict:
    """Pipeline complet de recommandation."""
    logger.info("Génération des recommandations...")
    recommender = SkillRecommender()
    results = recommender.recommend_for_all_profiles(cluster_data, top_n=15)
    logger.info("Recommandations générées pour tous les profils")
    return results
