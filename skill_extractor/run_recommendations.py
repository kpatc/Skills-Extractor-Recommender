#!/usr/bin/env python3
"""
PIPELINE 4: Recommendations - Skills Gap Analysis & Recommendations
Utilise les embeddings, clusters et les données des offres pour générer des recommandations
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des modules
from nlp.advanced_skills_extractor import SkillsExtractor
from recommendtion.clustering_recommender import ClusteringRecommender


def load_modelling_results():
    """Charge les résultats du modelling (embeddings + clustering)"""
    modelling_dir = Path("data/modelling")
    
    # Charge les embeddings
    embeddings_file = list(modelling_dir.glob("embeddings_*.json"))
    if not embeddings_file:
        logger.error("Aucun fichier d'embeddings trouvé!")
        return None
    
    with open(embeddings_file[-1], 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)
    
    # Charge les clusters
    clusters_file = list(modelling_dir.glob("clusters_*.json"))
    if not clusters_file:
        logger.error("Aucun fichier de clusters trouvé!")
        return None
    
    with open(clusters_file[-1], 'r', encoding='utf-8') as f:
        clusters_data = json.load(f)
    
    return {
        'embeddings': embeddings_data,
        'clusters': clusters_data
    }


def load_processed_offers():
    """Charge les offres traitées avec les skills"""
    processed_dir = Path("data/processed")
    processed_files = list(processed_dir.glob("processed_offers_*.json"))
    
    if not processed_files:
        logger.error("Aucun fichier d'offres traitées trouvé!")
        return []
    
    with open(processed_files[-1], 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_user_skills(cv_text):
    """Extrait les skills du CV de l'utilisateur"""
    extractor = SkillsExtractor()
    
    # Utilise la méthode améliorée d'extraction
    skills = extractor.extract_skills_weighted(
        title="",
        description=cv_text,
        profile="",
        technical_skills="",
        desired_skills=""
    )
    
    return [s['skill'] for s in skills]


def generate_recommendations(user_title, user_skills, modelling_results, processed_offers):
    """Génère les recommandations basées sur le titre et les skills de l'utilisateur"""
    
    logger.info("\nGenerating recommendations...")
    
    recommender = ClusteringRecommender()
    
    # Prepare job data with clusters
    job_data = []
    for offer in processed_offers:
        job_data.append({
            'title': offer['title'],
            'skills': [s['skill'] for s in offer.get('skills_weighted', [])],
            'cluster': offer.get('cluster', -1)
        })
    
    # Generate recommendations
    recommendations = recommender.recommend_skills(
        user_title=user_title,
        user_skills=user_skills,
        job_data=job_data
    )
    
    return recommendations


def main():
    logger.info("\n" + "="*80)
    logger.info("PIPELINE 4: RECOMMENDATIONS (Skills Gap Analysis & Recommendations)")
    logger.info("="*80 + "\n")
    
    # 1. Charge les résultats du modelling
    logger.info("Loading modelling results...")
    modelling_results = load_modelling_results()
    if not modelling_results:
        logger.error("Failed to load modelling results")
        return
    
    logger.info(f"✓ Embeddings et clusters chargés\n")
    
    # 2. Charge les offres traitées
    logger.info("Loading processed offers...")
    processed_offers = load_processed_offers()
    logger.info(f"✓ {len(processed_offers)} offres chargées\n")
    
    # 3. Example: Generate recommendations for a developer role
    user_title = "Senior Backend Developer"
    user_skills = ["Python", "Java", "PostgreSQL", "Docker", "Git"]
    
    logger.info(f"User Title: {user_title}")
    logger.info(f"User Skills: {', '.join(user_skills)}\n")
    
    # 4. Generate recommendations
    recommendations = generate_recommendations(
        user_title,
        user_skills,
        modelling_results,
        processed_offers
    )
    
    # 5. Save recommendations
    output_file = Path("data/recommendations") / f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'user_title': user_title,
            'user_skills': user_skills,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nRecommendations saved to {output_file}")
    logger.info(f"\nTop recommended skills:")
    for i, rec in enumerate(recommendations[:5], 1):
        logger.info(f"  {i}. {rec['skill']} (score: {rec['score']:.2f})")


if __name__ == "__main__":
    main()
