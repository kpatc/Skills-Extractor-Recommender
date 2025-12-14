#!/usr/bin/env python
"""
Script principal d'exécution du pipeline complet.
Utilisation: python run_pipeline.py [--mode test|prod] [--export all|json|excel|csv]
"""

import argparse
import logging
import sys
from pathlib import Path

# Importer le pipeline
from skill_extractor.pipeline import SkillExtractionPipeline
from skill_extractor.utils.exporters import ResultsExporter, ResultsVisualizer

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Pipeline d'extraction de compétences techniques"
    )

    parser.add_argument(
        "--mode",
        choices=["test", "prod"],
        default="test",
        help="Mode d'exécution (test avec données simulées ou prod avec scraping réel)"
    )

    parser.add_argument(
        "--export",
        choices=["all", "json", "excel", "csv", "report"],
        default="all",
        help="Format d'export des résultats"
    )

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Afficher les visualisations en console"
    )

    parser.add_argument(
        "--top-skills",
        type=int,
        default=15,
        help="Nombre de top compétences à afficher"
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("PIPELINE D'EXTRACTION DE COMPETENCES TECH")
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Export: {args.export}")
    logger.info("=" * 80)

    try:
        # Exécuter le pipeline
        test_mode = args.mode == "test"
        pipeline = SkillExtractionPipeline(test_mode=test_mode)
        result = pipeline.run_full_pipeline()

        if result["status"] != "success":
            logger.error("Pipeline échoué!")
            return 1

        # Récupérer les données
        offers = pipeline.offers_with_skills
        clustering_result = pipeline.clustering_result
        recommendations = pipeline.recommendations

        # Visualisations
        if args.visualize:
            logger.info("Génération des visualisations...")
            visualizer = ResultsVisualizer()

            visualizer.print_top_skills(offers, top_n=args.top_skills)
            visualizer.print_cluster_summary(clustering_result)
            visualizer.print_recommendations_summary(recommendations)

        # Exports
        logger.info("Exportation des résultats...")
        exporter = ResultsExporter()

        if args.export in ["all", "json"]:
            exporter.export_to_json(recommendations, "recommendations.json")

        if args.export in ["all", "excel"]:
            exporter.export_to_excel(offers, "offers_analysis.xlsx")

        if args.export in ["all", "csv"]:
            exporter.export_skills_summary(offers, "skills_summary.csv")
            exporter.export_recommendations_report(recommendations, "recommendations_report.json")

        if args.export in ["all", "report"]:
            visualizer.create_summary_report(
                offers,
                clustering_result,
                recommendations,
                "summary_report.txt"
            )

        logger.info("=" * 80)
        logger.info("PIPELINE TERMINE AVEC SUCCES ✓")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
