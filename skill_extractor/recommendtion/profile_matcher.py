"""
Profile Matcher: Aligne le profil d'un candidat avec les demandes du marché.
Intègre les données du CV Recommender avec les résultats du pipeline d'extraction.
"""

import logging
import sys
from typing import Dict, List, Set, Tuple
from pathlib import Path
from collections import Counter
import json

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)


class CandidateProfile:
    """Représente le profil d'un candidat."""

    def __init__(self, name: str, current_skills: List[str], target_role: str = None):
        """
        Initialise le profil candidat.
        
        Args:
            name: Nom du candidat
            current_skills: Compétences actuelles
            target_role: Rôle cible (data_engineer, backend_dev, etc.)
        """
        self.name = name
        self.current_skills = set(s.lower() for s in current_skills)
        self.target_role = target_role
        self.github_repos = []
        self.linkedin_profile = {}

    def add_github_skills(self, repos: List[Dict]):
        """
        Ajoute des compétences déduites des repos GitHub.
        
        Args:
            repos: Liste des repos avec languages
        """
        self.github_repos = repos

        # Extraire les languages
        languages = set()
        for repo in repos:
            if "languages" in repo:
                languages.update(repo["languages"])

        self.current_skills.update(languages)
        logger.info(f"✓ {len(languages)} skills ajoutées depuis GitHub")

    def add_linkedin_skills(self, skills: List[str]):
        """Ajoute des compétences depuis LinkedIn."""
        self.current_skills.update(s.lower() for s in skills)

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            "name": self.name,
            "current_skills": list(self.current_skills),
            "target_role": self.target_role,
            "skills_count": len(self.current_skills),
            "github_repos_count": len(self.github_repos),
        }


class ProfileMatcher:
    """Match un profil candidat avec les demandes du marché."""

    def __init__(self):
        """Initialise le matcher."""
        self.market_skills = {}
        self.skill_frequency = {}
        self.cluster_skills = {}

    def load_market_data(self, offers: List[Dict]):
        """
        Charge les données du marché depuis les offres.
        
        Args:
            offers: Liste des offres avec compétences extraites
        """
        logger.info("Chargement des données du marché...")

        all_skills = []
        self.cluster_skills = {}

        for offer in offers:
            skills = offer.get("extracted_skills", [])
            cluster = offer.get("cluster", "unknown")

            all_skills.extend(skills)

            if cluster not in self.cluster_skills:
                self.cluster_skills[cluster] = []

            self.cluster_skills[cluster].extend(skills)

        # Calculer les fréquences
        self.skill_frequency = dict(Counter(all_skills))
        self.market_skills = set(all_skills)

        logger.info(f"✓ {len(self.market_skills)} compétences du marché chargées")
        logger.info(f"✓ {len(self.cluster_skills)} clusters identifiés")

    def match_profile_to_cluster(
        self,
        profile: CandidateProfile,
        offers: List[Dict]
    ) -> Dict:
        """
        Match le profil à un cluster spécifique.
        
        Args:
            profile: Profil candidat
            offers: Offres du marché
        
        Returns:
            Résultat du matching
        """
        self.load_market_data(offers)

        # Si rôle cible, trouver le cluster correspondant
        if profile.target_role:
            cluster_id = self._get_cluster_for_role(profile.target_role)
        else:
            # Trouver le meilleur cluster basé sur les skills
            cluster_id = self._find_best_cluster(profile.current_skills)

        # Offres du cluster cible
        cluster_offers = [o for o in offers if o.get("cluster") == cluster_id]

        # Analyser le matching
        cluster_name = self._get_cluster_name(cluster_id)
        cluster_top_skills = self._get_cluster_top_skills(cluster_id, top_n=15)

        matching_score = self._calculate_match_score(
            profile.current_skills,
            set(s[0] for s in cluster_top_skills)
        )

        return {
            "profile_name": profile.name,
            "target_cluster": cluster_name,
            "cluster_id": cluster_id,
            "matching_score": matching_score,
            "matching_offers": len(cluster_offers),
            "cluster_top_skills": cluster_top_skills,
            "candidate_alignment": self._analyze_alignment(
                profile.current_skills,
                cluster_top_skills
            ),
        }

    def _get_cluster_for_role(self, role: str) -> int:
        """Map rôle cible à cluster ID."""
        role_to_cluster = {
            "data_engineer": 0,
            "data_scientist": 0,
            "backend_dev": 1,
            "backend_developer": 1,
            "devops_engineer": 2,
            "devops": 2,
            "ml_engineer": 3,
            "machine_learning": 3,
            "frontend_dev": 4,
            "frontend_developer": 4,
        }
        return role_to_cluster.get(role.lower(), 0)

    def _find_best_cluster(self, candidate_skills: Set[str]) -> int:
        """
        Trouve le cluster le plus proche des compétences du candidat.
        
        Args:
            candidate_skills: Compétences du candidat
        
        Returns:
            ID du meilleur cluster
        """
        best_cluster = 0
        best_score = 0

        for cluster_id, cluster_skills_list in self.cluster_skills.items():
            cluster_skills_set = set(cluster_skills_list)
            overlap = len(candidate_skills & cluster_skills_set)

            if overlap > best_score:
                best_score = overlap
                best_cluster = cluster_id

        return best_cluster

    def _get_cluster_name(self, cluster_id: int) -> str:
        """Retourne le nom du cluster."""
        names = {0: "Data", 1: "Backend", 2: "DevOps", 3: "AI/ML", 4: "Frontend"}
        return names.get(cluster_id, f"Cluster {cluster_id}")

    def _get_cluster_top_skills(self, cluster_id: int, top_n: int = 15) -> List[Tuple]:
        """Retourne les top skills d'un cluster."""
        if cluster_id not in self.cluster_skills:
            return []

        cluster_skills_list = self.cluster_skills[cluster_id]
        skill_counts = Counter(cluster_skills_list)
        return skill_counts.most_common(top_n)

    def _calculate_match_score(self, candidate_skills: Set[str], cluster_skills: Set[str]) -> float:
        """
        Calcule le score de matching (0-100).
        
        Args:
            candidate_skills: Compétences du candidat
            cluster_skills: Compétences du cluster (top)
        
        Returns:
            Score en pourcentage
        """
        if not cluster_skills:
            return 0.0

        overlap = len(candidate_skills & cluster_skills)
        score = (overlap / len(cluster_skills)) * 100

        return round(score, 1)

    def _analyze_alignment(
        self,
        candidate_skills: Set[str],
        cluster_top_skills: List[Tuple]
    ) -> Dict:
        """
        Analyse comment le candidat s'aligne avec le cluster.
        
        Args:
            candidate_skills: Compétences du candidat
            cluster_top_skills: Top skills du cluster
        
        Returns:
            Analyse détaillée
        """
        cluster_skills_set = set(s[0] for s in cluster_top_skills)

        # Compétences maîtrisées dans le cluster
        mastered = candidate_skills & cluster_skills_set

        # Compétences manquantes
        missing = cluster_skills_set - candidate_skills

        # Compétences non pertinentes (candidate a mais pas dans cluster top)
        non_relevant = candidate_skills - cluster_skills_set

        return {
            "mastered_in_cluster": list(mastered),
            "missing_skills": list(missing),
            "non_relevant_skills": list(non_relevant),
            "mastered_count": len(mastered),
            "missing_count": len(missing),
            "alignment_percentage": round(len(mastered) / len(cluster_skills_set) * 100, 1) if cluster_skills_set else 0,
        }

    def generate_matching_report(
        self,
        profile: CandidateProfile,
        offers: List[Dict],
        output_file: str = None
    ) -> Dict:
        """
        Génère un rapport complet de matching.
        
        Args:
            profile: Profil candidat
            offers: Offres du marché
            output_file: Fichier de sauvegarde (optionnel)
        
        Returns:
            Rapport complet
        """
        logger.info(f"Génération du rapport de matching pour {profile.name}...")

        matching = self.match_profile_to_cluster(profile, offers)

        report = {
            "candidate": profile.to_dict(),
            "matching": matching,
            "recommendations": self._generate_recommendations(matching),
        }

        # Sauvegarder si demandé
        if output_file:
            filepath = PROCESSED_DATA_DIR / output_file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Rapport sauvegardé: {filepath}")

        return report

    def _generate_recommendations(self, matching: Dict) -> List[str]:
        """Génère des recommandations basées sur le matching."""
        recommendations = []
        score = matching["matching_score"]
        alignment = matching["candidate_alignment"]

        if score > 80:
            recommendations.append(
                f"✓ Excellent alignement avec le cluster {matching['target_cluster']}"
            )
        elif score > 60:
            recommendations.append(
                f"✓ Bon alignement avec le cluster {matching['target_cluster']}"
            )
        else:
            recommendations.append(
                f"⚠ Alignement faible - considère d'acquérir des compétences clés"
            )

        if alignment["missing_count"] > 0:
            recommendations.append(
                f"📚 {alignment['missing_count']} compétences essentielles à acquérir"
            )

        if alignment["mastered_count"] > 5:
            recommendations.append(
                f"💪 {alignment['mastered_count']} compétences maîtrisées - bonne base"
            )

        return recommendations
