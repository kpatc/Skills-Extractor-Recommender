"""
Service intégré: Combine l'extraction de compétences du marché avec 
l'analyse de profil candidat pour CV recommendations.

Ceci est l'extension optionnelle du pipeline principal.
"""

import logging
import sys
from typing import Dict, List
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from .profile_matcher import ProfileMatcher, CandidateProfile
from .skill_gap import SkillGapAnalyzer
from .cv_personalizer import CVPersonalizer
from utils.config import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)


class CVRecommenderService:
    """
    Service intégré pour recommandations CV personnalisées.
    
    Workflow:
    1. Charge les résultats du pipeline principal (market insights)
    2. Prend le profil candidat
    3. Analyse le gap candidat vs marché
    4. Génère des recommandations CV personnalisées
    """

    def __init__(self, market_insights: Dict = None):
        """
        Initialise le service.
        
        Args:
            market_insights: Résultats du pipeline d'extraction
        """
        self.market_insights = market_insights or {}
        self.matcher = ProfileMatcher()
        self.gap_analyzer = SkillGapAnalyzer()
        self.cv_personalizer = CVPersonalizer()

        logger.info("✓ CV Recommender Service initialized")

    def analyze_candidate(
        self,
        candidate: CandidateProfile,
        offers: List[Dict],
        target_cluster: str = None
    ) -> Dict:
        """
        Analyse complète d'un candidat contre le marché.
        
        Args:
            candidate: Profil candidat
            offers: Offres du marché (résultats du pipeline)
            target_cluster: Cluster cible optionnel
        
        Returns:
            Analyse complète CV + recommandations
        """
        logger.info(f"Analyse du candidat: {candidate.name}")

        # Étape 1: Match avec le marché
        matching = self.matcher.match_profile_to_cluster(candidate, offers)

        # Étape 2: Analyser l'écart
        cluster_top_skills = matching["cluster_top_skills"]
        skill_frequencies = {s[0]: s[1] for s in cluster_top_skills}

        gap_analysis = self.gap_analyzer.analyze_gap(
            candidate.current_skills,
            cluster_top_skills,
            skill_frequencies
        )

        # Étape 3: Recommandations CV
        cv_recommendations = self.cv_personalizer.generate_cv_recommendations(
            candidate.name,
            matching["target_cluster"],
            gap_analysis,
            list(candidate.current_skills)
        )

        # Assembler le résultat complet
        result = {
            "candidate": candidate.to_dict(),
            "market_analysis": {
                "target_cluster": matching["target_cluster"],
                "cluster_id": matching["cluster_id"],
                "matching_offers": matching["matching_offers"],
                "matching_score": matching["matching_score"],
            },
            "gap_analysis": gap_analysis,
            "cv_recommendations": cv_recommendations,
            "full_report": self._generate_full_report(
                candidate,
                matching,
                gap_analysis,
                cv_recommendations
            ),
        }

        return result

    def batch_analyze_candidates(
        self,
        candidates: List[CandidateProfile],
        offers: List[Dict]
    ) -> List[Dict]:
        """
        Analyse plusieurs candidats.
        
        Args:
            candidates: Liste de profils candidats
            offers: Offres du marché
        
        Returns:
            Analyses de tous les candidats
        """
        logger.info(f"Analyse de {len(candidates)} candidats...")

        results = []
        for candidate in candidates:
            try:
                result = self.analyze_candidate(candidate, offers)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur pour {candidate.name}: {e}")

        logger.info(f"✓ {len(results)} candidats analysés avec succès")
        return results

    def compare_candidates(
        self,
        candidates: List[CandidateProfile],
        offers: List[Dict],
        cluster_id: int = 0
    ) -> Dict:
        """
        Compare les profils de plusieurs candidats.
        
        Args:
            candidates: Candidats à comparer
            offers: Offres du marché
            cluster_id: ID du cluster pour comparaison
        
        Returns:
            Comparaison structurée
        """
        logger.info(f"Comparaison de {len(candidates)} candidats...")

        # Charger les données du marché
        self.matcher.load_market_data(offers)

        cluster_offers = [o for o in offers if o.get("cluster") == cluster_id]
        cluster_top_skills = self.matcher._get_cluster_top_skills(cluster_id, top_n=20)

        # Créer profiles dict pour comparaison
        profiles_dict = {c.name: c.current_skills for c in candidates}

        # Utiliser le comparateur
        comparison = self.gap_analyzer.compare_profiles(profiles_dict, cluster_top_skills)

        # Enrichir avec détails
        detailed_comparison = {
            "cluster": self.matcher._get_cluster_name(cluster_id),
            "comparison": comparison,
            "candidates_details": {},
        }

        # Ajouter les détails de chaque candidat
        for candidate in candidates:
            gap = self.gap_analyzer.analyze_gap(
                candidate.current_skills,
                cluster_top_skills
            )
            detailed_comparison["candidates_details"][candidate.name] = {
                "alignment": comparison["profiles"][candidate.name]["alignment"],
                "missing_critical": len([p for p in gap["priorities"] if p["level"] == "CRITICAL"]),
                "quick_wins": len(gap["quick_wins"]),
            }

        return detailed_comparison

    def _generate_full_report(
        self,
        candidate: CandidateProfile,
        matching: Dict,
        gap_analysis: Dict,
        cv_recommendations: Dict
    ) -> str:
        """Génère un rapport texte complet."""
        report = f"""
{'='*70}
CV ANALYSIS & RECOMMENDATIONS
{'='*70}

CANDIDATE: {candidate.name}
TARGET ROLE: {cv_recommendations['target_role']}
TARGET CLUSTER: {matching['target_cluster']}

{'='*70}
MARKET ALIGNMENT SCORE: {matching['matching_score']}%
{'='*70}

📊 SKILLS SUMMARY
---------
✓ Mastered Skills: {gap_analysis['mastered_count']}
  {', '.join(gap_analysis['mastered_skills'][:5]) or 'None yet'}

❌ Missing Skills (Critical): {len([p for p in gap_analysis['priorities'] if p['level'] == 'CRITICAL'])}
  {', '.join([p['skill'] for p in gap_analysis['priorities'] if p['level'] == 'CRITICAL'][:3]) or 'None'}

⚡ Quick Wins (2-4 weeks):
  {chr(10).join([f"  • {qw['skill']} ({qw['learning_time']})" for qw in gap_analysis['quick_wins'][:3]]) or '  None'}

{'='*70}
CV RECOMMENDATIONS
{'='*70}

1️⃣ PROFESSIONAL TITLE
   → {cv_recommendations['target_role']}

2️⃣ PROFESSIONAL SUMMARY
   {cv_recommendations['professional_summary']}

3️⃣ SKILLS SECTION ORGANIZATION
   • Expert Level: {', '.join(cv_recommendations['skills_section']['expert_level']['skills'][:3])}
   • Intermediate: {', '.join(cv_recommendations['skills_section']['intermediate_level']['skills'][:3])}
   • Developing: {', '.join(cv_recommendations['skills_section']['developing_level']['skills'][:3])}

4️⃣ ACTION ITEMS
{chr(10).join([f'   {action}' for action in cv_recommendations['action_items'][:3]])}

{'='*70}
"""
        return report

    def export_analysis(
        self,
        analysis: Dict,
        filename: str = None
    ) -> Path:
        """
        Exporte l'analyse en JSON.
        
        Args:
            analysis: Résultat de analyze_candidate
            filename: Nom du fichier
        
        Returns:
            Chemin du fichier sauvegardé
        """
        if filename is None:
            candidate_name = analysis["candidate"]["name"].replace(" ", "_")
            filename = f"cv_analysis_{candidate_name}.json"

        filepath = PROCESSED_DATA_DIR / filename

        # Nettoyer pour sérialisation JSON
        export_data = self._make_serializable(analysis)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Analyse exportée: {filepath}")
        return filepath

    @staticmethod
    def _make_serializable(obj):
        """Rend un objet sérialisable en JSON."""
        if isinstance(obj, dict):
            return {k: CVRecommenderService._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [CVRecommenderService._make_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj


def create_cv_analysis_pipeline(
    pipeline_results: Dict,
    candidate_profiles: List[CandidateProfile],
    batch_analyze: bool = False
) -> Dict:
    """
    Pipeline complet: Extraction + CV Analysis.
    
    Args:
        pipeline_results: Résultats du pipeline d'extraction
        candidate_profiles: Profils candidats à analyser
        batch_analyze: Si True, analyse tous les candidats
    
    Returns:
        Résultats d'analyse CV
    """
    logger.info("Démarrage du pipeline CV Analysis...")

    # Récupérer les offres du pipeline
    offers = pipeline_results.get("offers_clustered", [])

    # Initialiser le service
    service = CVRecommenderService(market_insights=pipeline_results)

    # Analyser les candidats
    if batch_analyze and len(candidate_profiles) > 1:
        results = service.batch_analyze_candidates(candidate_profiles, offers)
    else:
        candidate = candidate_profiles[0] if candidate_profiles else None
        if not candidate:
            logger.error("Aucun candidat fourni")
            return {}

        results = service.analyze_candidate(candidate, offers)

    logger.info("✓ Pipeline CV Analysis terminé")
    return results
