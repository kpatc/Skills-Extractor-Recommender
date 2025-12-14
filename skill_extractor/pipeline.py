"""
Pipeline principal d'extraction et analyse des compétences.
Orchestration complète: Scraping → NLP → Clustering → Recommandation.
"""

import logging
import json
import csv
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from skill_extractor.scrapping.scraper import scrape_all_sources
from skill_extractor.nlp.text_cleaner import clean_offers_pipeline
from skill_extractor.nlp.skills_extractor import extract_skills_pipeline
from skill_extractor.modelling.clustering import cluster_offers
from skill_extractor.recommendtion.recommender import generate_recommendations_pipeline
from skill_extractor.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, JOB_OFFERS_RAW, JOB_OFFERS_CLEANED

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkillExtractionPipeline:
    """Orchestration du pipeline complet."""

    def __init__(self, test_mode: bool = False):
        """
        Initialise le pipeline.
        
        Args:
            test_mode: Si True, utilise des données de test
        """
        self.test_mode = test_mode
        self.offers_raw = None
        self.offers_cleaned = None
        self.offers_with_skills = None
        self.clustering_result = None
        self.recommendations = None

    def run_full_pipeline(self) -> Dict:
        """
        Exécute le pipeline complet.
        
        Returns:
            Dictionnaire avec les résultats finaux
        """
        logger.info("=" * 80)
        logger.info("PIPELINE D'EXTRACTION DE COMPETENCES - DEMARRAGE")
        logger.info("=" * 80)

        try:
            # Étape 1: Scraping
            logger.info("\n[ETAPE 1] SCRAPING DES OFFRES D'EMPLOI")
            logger.info("-" * 80)
            self.offers_raw = self._scrape_step()

            # Étape 2: Nettoyage NLP
            logger.info("\n[ETAPE 2] NETTOYAGE ET PRETRAITEMENT NLP")
            logger.info("-" * 80)
            self.offers_cleaned = self._cleaning_step()

            # Étape 3: Extraction des compétences
            logger.info("\n[ETAPE 3] EXTRACTION DES COMPETENCES")
            logger.info("-" * 80)
            self.offers_with_skills = self._skills_extraction_step()

            # Étape 4: Clustering
            logger.info("\n[ETAPE 4] VECTORISATION ET CLUSTERING")
            logger.info("-" * 80)
            self.clustering_result = self._clustering_step()

            # Étape 5: Recommandations
            logger.info("\n[ETAPE 5] RECOMMANDATIONS PERSONNALISEES")
            logger.info("-" * 80)
            self.recommendations = self._recommendations_step()

            # Résumé final
            self._print_summary()

            return {
                "status": "success",
                "offers_raw_count": len(self.offers_raw),
                "offers_processed": len(self.offers_with_skills),
                "clustering_result": self.clustering_result,
                "recommendations": self.recommendations,
            }

        except Exception as e:
            logger.error(f"Erreur dans le pipeline: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _scrape_step(self) -> List[Dict]:
        """Étape 1: Scraping."""
        logger.info("Récupération des offres d'emploi...")
        offers = scrape_all_sources(test_mode=self.test_mode)
        logger.info(f"✓ {len(offers)} offres récupérées")

        # Sauvegarder les données brutes
        self._save_offers_csv(offers, JOB_OFFERS_RAW)

        return offers

    def _cleaning_step(self) -> List[Dict]:
        """Étape 2: Nettoyage NLP."""
        logger.info("Nettoyage des descriptions...")
        offers = clean_offers_pipeline(self.offers_raw)
        logger.info(f"✓ {len(offers)} offres nettoyées")

        # Sauvegarder les données nettoyées
        self._save_offers_csv(offers, JOB_OFFERS_CLEANED)

        return offers

    def _skills_extraction_step(self) -> List[Dict]:
        """Étape 3: Extraction des compétences."""
        logger.info("Extraction des compétences techniques...")
        offers = extract_skills_pipeline(self.offers_cleaned)
        logger.info(f"✓ Compétences extraites pour {len(offers)} offres")

        # Statistiques
        self._print_skills_statistics(offers)

        return offers

    def _clustering_step(self) -> Dict:
        """Étape 4: Clustering."""
        logger.info("Clustering des offres par profil...")
        result = cluster_offers(self.offers_with_skills)
        logger.info(f"✓ Clustering terminé")

        # Statistiques
        self._print_clustering_statistics(result)

        return result

    def _recommendations_step(self) -> Dict:
        """Étape 5: Recommandations."""
        logger.info("Génération des recommandations personnalisées...")
        recommendations = generate_recommendations_pipeline(self.clustering_result)
        logger.info(f"✓ Recommandations générées pour {len(recommendations)} profils")

        # Sauvegarder les résultats
        self._save_recommendations(recommendations)

        return recommendations

    def _print_summary(self):
        """Affiche un résumé final."""
        logger.info("\n" + "=" * 80)
        logger.info("RESUME DU PIPELINE")
        logger.info("=" * 80)

        if self.offers_raw:
            logger.info(f"• Offres brutes récupérées: {len(self.offers_raw)}")

        if self.offers_with_skills:
            total_skills = sum(
                len(offer.get("extracted_skills", []))
                for offer in self.offers_with_skills
            )
            unique_skills = len(set(
                skill
                for offer in self.offers_with_skills
                for skill in offer.get("extracted_skills", [])
            ))
            logger.info(f"• Total compétences extraites: {total_skills}")
            logger.info(f"• Compétences uniques: {unique_skills}")

        if self.clustering_result:
            logger.info(f"• Clusters formés: {len(self.clustering_result['cluster_stats'])}")

        if self.recommendations:
            logger.info(f"• Profils avec recommandations: {len(self.recommendations)}")

        logger.info("=" * 80)
        logger.info("PIPELINE TERMINE AVEC SUCCES ✓")
        logger.info("=" * 80)

    def _print_skills_statistics(self, offers: List[Dict]):
        """Affiche les statistiques sur les compétences."""
        from collections import Counter

        all_skills = []
        for offer in offers:
            all_skills.extend(offer.get("extracted_skills", []))

        if not all_skills:
            return

        skill_counts = Counter(all_skills)
        top_10 = skill_counts.most_common(10)

        logger.info("\nTop 10 des compétences les plus demandées:")
        for i, (skill, count) in enumerate(top_10, 1):
            logger.info(f"  {i}. {skill}: {count} occurrences")

    def _print_clustering_statistics(self, result: Dict):
        """Affiche les statistiques de clustering."""
        cluster_stats = result.get("cluster_stats", {})

        logger.info("\nStatistiques par cluster:")
        for cluster_id, stats in cluster_stats.items():
            logger.info(f"\n  Cluster {cluster_id} ({stats['size']} offres):")
            top_skills = stats.get("top_skills", [])
            for skill, freq in top_skills[:5]:
                logger.info(f"    - {skill}: {freq}")

    def _save_offers_csv(self, offers: List[Dict], filepath: Path):
        """Sauvegarde les offres en CSV."""
        if not offers:
            logger.warning(f"Aucune donnée à sauvegarder dans {filepath}")
            return

        try:
            # Utiliser une sous-ensemble des champs pour CSV
            keys = [
                "job_id", "title", "company", "location", "description",
                "source", "scrape_date"
            ]

            # Ajouter les champs optionnels s'ils existent
            if "description_cleaned" in offers[0]:
                keys.append("description_cleaned")
            if "extracted_skills" in offers[0]:
                keys.append("extracted_skills")
            if "cluster" in offers[0]:
                keys.append("cluster")

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(offers)

            logger.info(f"✓ Sauvegardé {len(offers)} offres dans {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde CSV: {e}")

    def _save_recommendations(self, recommendations: Dict):
        """Sauvegarde les recommandations en JSON."""
        try:
            filepath = PROCESSED_DATA_DIR / "recommendations.json"

            # Convertir les tuples en listes pour la sérialisation JSON
            recommendations_serializable = {}
            for profile, data in recommendations.items():
                recommendations_serializable[profile] = self._make_serializable(data)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(recommendations_serializable, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Recommandations sauvegardées dans {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des recommandations: {e}")

    @staticmethod
    def _make_serializable(obj):
        """Convertit un objet en format sérialisable JSON."""
        if isinstance(obj, dict):
            return {k: SkillExtractionPipeline._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [SkillExtractionPipeline._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj


def main(test_mode: bool = True):
    """
    Fonction principale d'exécution du pipeline.
    
    Args:
        test_mode: Si True, utilise des données de test
    """
    pipeline = SkillExtractionPipeline(test_mode=test_mode)
    result = pipeline.run_full_pipeline()
    return result


if __name__ == "__main__":
    # Exécuter en mode test par défaut
    main(test_mode=True)
