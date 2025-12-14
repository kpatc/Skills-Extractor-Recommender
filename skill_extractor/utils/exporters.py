"""
Utilitaires pour l'exportation et visualisation des résultats.
"""

import json
import csv
import logging
import sys
from typing import Dict, List, Tuple
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)


class ResultsExporter:
    """Exporte les résultats dans différents formats."""

    @staticmethod
    def export_to_json(data: Dict, filename: str = "results.json") -> Path:
        """Exporte les données en JSON."""
        filepath = PROCESSED_DATA_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Données exportées en JSON: {filepath}")
        return filepath

    @staticmethod
    def export_to_excel(
        offers: List[Dict],
        filename: str = "offers_analysis.xlsx"
    ) -> Path:
        """Exporte les offres et statistiques en Excel."""
        try:
            filepath = PROCESSED_DATA_DIR / filename

            # Créer un DataFrame
            df = pd.DataFrame(offers)

            # Sélectionner les colonnes principales
            cols_to_keep = [
                "job_id", "title", "company", "location",
                "source", "skills_count", "cluster"
            ]
            cols_available = [c for c in cols_to_keep if c in df.columns]
            df_export = df[cols_available]

            # Ajouter les compétences extraites
            if "extracted_skills" in df.columns:
                df_export["skills"] = df["extracted_skills"].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else ""
                )

            # Exporter
            df_export.to_excel(filepath, index=False)

            logger.info(f"✓ Données exportées en Excel: {filepath}")
            return filepath

        except ImportError:
            logger.error("pandas ou openpyxl non installés")
            return None

    @staticmethod
    def export_skills_summary(offers: List[Dict], filename: str = "skills_summary.csv") -> Path:
        """Exporte un résumé des compétences."""
        from collections import Counter

        filepath = PROCESSED_DATA_DIR / filename

        # Collecter toutes les compétences
        all_skills = []
        categories = {}

        for offer in offers:
            if "extracted_skills" in offer:
                all_skills.extend(offer["extracted_skills"])

            if "skills_categorized" in offer:
                for category, skills in offer["skills_categorized"].items():
                    if category not in categories:
                        categories[category] = Counter()
                    categories[category].update(skills)

        # Créer le résumé
        skill_counts = Counter(all_skills)
        summary = []

        for skill, count in skill_counts.most_common():
            # Trouver la catégorie
            category = "Autre"
            for cat, cat_skills in categories.items():
                if skill in cat_skills:
                    category = cat
                    break

            summary.append({
                "skill": skill,
                "frequency": count,
                "category": category,
                "percentage": f"{count / len(offers) * 100:.1f}%"
            })

        # Exporter
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["skill", "frequency", "category", "percentage"])
            writer.writeheader()
            writer.writerows(summary)

        logger.info(f"✓ Résumé des compétences exporté: {filepath}")
        return filepath

    @staticmethod
    def export_recommendations_report(
        recommendations: Dict,
        filename: str = "recommendations_report.json"
    ) -> Path:
        """Exporte un rapport des recommandations."""
        filepath = PROCESSED_DATA_DIR / filename

        report = {}

        for profile, data in recommendations.items():
            report[profile] = {
                "current_skills": data.get("current_skills", []),
                "recommended_skills": [
                    {
                        "skill": r["skill"],
                        "priority": round(r["priority"], 2),
                        "frequency": r["frequency"],
                    }
                    for r in data.get("recommended_skills", [])
                ],
                "learning_path": data.get("learning_path", []),
                "total_recommendations": len(data.get("recommended_skills", [])),
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Rapport de recommandations exporté: {filepath}")
        return filepath


class ResultsVisualizer:
    """Génère des visualisations des résultats."""

    @staticmethod
    def print_top_skills(offers: List[Dict], top_n: int = 15):
        """Affiche les compétences les plus demandées."""
        from collections import Counter

        all_skills = []
        for offer in offers:
            if "extracted_skills" in offer:
                all_skills.extend(offer["extracted_skills"])

        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(top_n)

        print("\n" + "=" * 60)
        print("🏆 TOP COMPETENCES LES PLUS DEMANDEES")
        print("=" * 60)

        for i, (skill, count) in enumerate(top_skills, 1):
            percentage = count / len(offers) * 100
            bar = "█" * int(percentage / 5)
            print(f"{i:2}. {skill:20} {count:3} offres ({percentage:5.1f}%) {bar}")

        print("=" * 60)

    @staticmethod
    def print_cluster_summary(clustering_result: Dict):
        """Affiche un résumé des clusters."""
        cluster_stats = clustering_result.get("cluster_stats", {})
        cluster_names = ["Data", "Backend", "DevOps", "AI/ML", "Frontend"]

        print("\n" + "=" * 60)
        print("📊 RESUME DES CLUSTERS")
        print("=" * 60)

        for cluster_id, stats in sorted(cluster_stats.items()):
            cluster_name = cluster_names[cluster_id] if cluster_id < len(cluster_names) else f"Cluster {cluster_id}"
            size = stats.get("size", 0)

            print(f"\n{cluster_name} (Cluster {cluster_id})")
            print(f"  Taille: {size} offres")
            print(f"  Top compétences:")

            top_skills = stats.get("top_skills", [])
            for skill, freq in top_skills[:5]:
                print(f"    - {skill}: {freq}")

        print("\n" + "=" * 60)

    @staticmethod
    def print_recommendations_summary(recommendations: Dict):
        """Affiche un résumé des recommandations."""
        print("\n" + "=" * 60)
        print("🎯 RECOMMANDATIONS PAR PROFIL")
        print("=" * 60)

        for profile, data in recommendations.items():
            print(f"\n{profile.upper()}")
            print(f"  Compétences actuelles: {len(data['current_skills'])}")
            print(f"  Top recommandations:")

            for rec in data["recommended_skills"][:5]:
                skill = rec["skill"]
                priority = rec.get("priority", 0)
                print(f"    - {skill} (priorité: {priority:.1f})")

            print(f"\n  Plan d'apprentissage:")
            for phase in data.get("learning_path", []):
                print(f"    • {phase['phase']}")
                skills = phase.get("skills", [])
                for skill in skills[:3]:
                    print(f"      - {skill}")
                if len(skills) > 3:
                    print(f"      - ... et {len(skills) - 3} autres")

        print("\n" + "=" * 60)

    @staticmethod
    def create_summary_report(
        offers: List[Dict],
        clustering_result: Dict,
        recommendations: Dict,
        filename: str = "summary_report.txt"
    ) -> Path:
        """Crée un rapport textuel complet."""
        filepath = PROCESSED_DATA_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT D'EXTRACTION DE COMPETENCES\n")
            f.write("=" * 80 + "\n\n")

            # Section 1: Statistiques générales
            f.write("1. STATISTIQUES GENERALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Nombre d'offres analysées: {len(offers)}\n")

            total_skills = sum(
                len(offer.get("extracted_skills", []))
                for offer in offers
            )
            unique_skills = len(set(
                skill
                for offer in offers
                for skill in offer.get("extracted_skills", [])
            ))

            f.write(f"Compétences extraites (total): {total_skills}\n")
            f.write(f"Compétences uniques: {unique_skills}\n")
            f.write(f"Moyenne compétences/offre: {total_skills / len(offers):.1f}\n\n")

            # Section 2: Top compétences
            from collections import Counter

            all_skills = []
            for offer in offers:
                all_skills.extend(offer.get("extracted_skills", []))

            skill_counts = Counter(all_skills)
            top_10 = skill_counts.most_common(10)

            f.write("2. TOP 10 COMPETENCES\n")
            f.write("-" * 80 + "\n")
            for i, (skill, count) in enumerate(top_10, 1):
                f.write(f"{i:2}. {skill:25} {count:3} offres\n")
            f.write("\n")

            # Section 3: Clustering
            cluster_stats = clustering_result.get("cluster_stats", {})

            f.write("3. CLUSTERING\n")
            f.write("-" * 80 + "\n")
            f.write(f"Nombre de clusters: {len(cluster_stats)}\n")
            for cluster_id, stats in sorted(cluster_stats.items()):
                f.write(f"\nCluster {cluster_id}: {stats['size']} offres\n")
            f.write("\n")

            # Section 4: Recommandations
            f.write("4. RECOMMANDATIONS PAR PROFIL\n")
            f.write("-" * 80 + "\n")
            for profile, data in recommendations.items():
                f.write(f"\n{profile.upper()}\n")
                f.write(f"  Recommandations: {len(data['recommended_skills'])}\n")
                for rec in data["recommended_skills"][:3]:
                    f.write(f"    - {rec['skill']}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"✓ Rapport généré: {filepath}")
        return filepath
