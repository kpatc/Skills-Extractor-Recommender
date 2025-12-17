#!/usr/bin/env python3
"""
PIPELINE 3: MODELLING - Embeddings + Clustering
================================================
Charge les offres traitées par NLP
Génère les embeddings avec Gemini (fallback TF-IDF)
Effectue le clustering sur les skills extraits
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pickle

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from modelling.embeddings import HybridEmbedder
from modelling.clustering import SkillsVectorizer, OffersClustering
from utils.config import DATA_DIR, MODELS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_offers():
    """Charge les offres traitées par NLP (avec skills extraits)."""
    logger.info("\n" + "="*70)
    logger.info("PIPELINE 3: MODELLING (Embeddings + Clustering)")
    logger.info("="*70)
    
    processed_dir = DATA_DIR / "processed"
    processed_files = sorted(processed_dir.glob("processed_offers_*.json"))
    
    if not processed_files:
        logger.error("❌ Aucun fichier processed trouvé!")
        logger.info("   Exécute d'abord: python3 run_nlp.py")
        return None
    
    latest_file = processed_files[-1]
    logger.info(f"\n📂 Chargement: {latest_file.name}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        logger.info(f"✓ {len(offers)} offres chargées")
        return offers
    except Exception as e:
        logger.error(f"❌ Erreur chargement: {e}")
        return None


def create_skill_corpus(offers):
    """Crée un corpus de skills pour les embeddings."""
    logger.info("\n📊 Création du corpus de skills...")
    
    all_skills = set()
    skill_descriptions = {}
    
    for offer in offers:
        # Essayer skills_weighted (nouveau format) ou skills (ancien format)
        skills_weighted = offer.get("skills_weighted", [])
        skills_simple = offer.get("skills", [])
        
        # Si skills_weighted existe (liste de dicts avec {skill, weight})
        if skills_weighted:
            for skill_obj in skills_weighted:
                if isinstance(skill_obj, dict):
                    skill = skill_obj.get("skill", "")
                else:
                    skill = str(skill_obj)
                
                if skill and skill not in all_skills:
                    all_skills.add(skill)
                    skill_descriptions[skill] = f"Compétence technique: {skill}"
        
        # Sinon utiliser skills simple (liste de strings)
        elif skills_simple:
            for skill in skills_simple:
                if skill and skill not in all_skills:
                    all_skills.add(skill)
                    skill_descriptions[skill] = f"Compétence technique: {skill}"
    
    skills_list = sorted(list(all_skills))
    logger.info(f"✓ {len(skills_list)} skills uniques identifiés")
    
    return skills_list, skill_descriptions


def generate_embeddings(skills_list):
    """Génère les embeddings des skills."""
    logger.info("\n🔄 Génération des embeddings...")
    
    # Initialiser l'embedder (Gemini > TF-IDF)
    embedder = HybridEmbedder()
    logger.info(f"   Méthode: {embedder.get_method().upper()}")
    
    # Générer embeddings pour chaque skill
    embeddings = embedder.encode(skills_list)
    logger.info(f"✓ Embeddings générés: {embeddings.shape}")
    
    return embeddings, embedder.get_method()


def perform_clustering(embeddings, skills_list, n_clusters=None):
    """Effectue le clustering des skills."""
    logger.info("\n📈 Clustering des skills...")
    
    # Auto-déterminer nombre de clusters
    if n_clusters is None:
        n_clusters = max(3, min(10, len(skills_list) // 3))
    
    logger.info(f"   Nombre de clusters: {n_clusters}")
    
    clusterer = OffersClustering()
    clusterer.fit(embeddings)
    clusters = clusterer.labels
    
    logger.info(f"✓ Clustering complété")
    
    return clusters, clusterer


def save_results(offers, skills_list, embeddings, clusters, clusterer, method):
    """Sauvegarde les résultats."""
    logger.info("\n💾 Sauvegarde des résultats...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Sauvegarder les embeddings
    embeddings_file = DATA_DIR / "embeddings" / f"skills_embeddings_{timestamp}.npy"
    embeddings_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_file, embeddings)
    logger.info(f"✓ Embeddings: {embeddings_file.name}")
    
    # 2. Sauvegarder le modèle clusterer
    model_file = MODELS_DIR / f"kmeans_clusterer_{timestamp}.pkl"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(model_file, 'wb') as f:
        pickle.dump(clusterer, f)
    logger.info(f"✓ Modèle KMeans: {model_file.name}")
    
    # 3. Sauvegarder les resultats en JSON
    results = {
        "timestamp": timestamp,
        "embedding_method": method,
        "total_offers": len(offers),
        "total_skills": len(skills_list),
        "num_clusters": len(set(clusters)),
        "skills_with_clusters": [
            {
                "skill": skill,
                "cluster": int(clusters[i])
            }
            for i, skill in enumerate(skills_list)
        ],
        "cluster_analysis": {
            str(cluster_id): [
                skill for i, skill in enumerate(skills_list) 
                if clusters[i] == cluster_id
            ]
            for cluster_id in sorted(set(clusters))
        }
    }
    
    results_file = DATA_DIR / "embeddings" / f"clustering_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"✓ Résultats: {results_file.name}")
    
    return results


def display_clusters(results):
    """Affiche un résumé des clusters."""
    logger.info("\n📊 Résumé des clusters:")
    logger.info("-" * 70)
    
    for cluster_id in sorted(results["cluster_analysis"].keys()):
        skills = results["cluster_analysis"][cluster_id]
        logger.info(f"\n   Cluster {cluster_id} ({len(skills)} skills):")
        for skill in skills[:5]:  # Afficher max 5
            logger.info(f"      • {skill}")
        if len(skills) > 5:
            logger.info(f"      ... et {len(skills) - 5} autres")


def main():
    """Exécute le pipeline de modelling."""
    try:
        # 1. Charger les offres traitées
        offers = load_processed_offers()
        if not offers:
            return False
        
        # 2. Créer le corpus de skills
        skills_list, skill_descriptions = create_skill_corpus(offers)
        if not skills_list:
            logger.warning("⚠️  Aucun skill trouvé!")
            return False
        
        # 3. Générer les embeddings
        embeddings, method = generate_embeddings(skills_list)
        
        # 4. Effectuer le clustering
        clusters, clusterer = perform_clustering(embeddings, skills_list)
        
        # 5. Sauvegarder les résultats
        results = save_results(offers, skills_list, embeddings, clusters, clusterer, method)
        
        # 6. Afficher un résumé
        display_clusters(results)
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("✅ PIPELINE 3 COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"📊 Statistiques:")
        logger.info(f"   - Offres d'emploi: {results['total_offers']}")
        logger.info(f"   - Skills extraits: {results['total_skills']}")
        logger.info(f"   - Clusters créés: {results['num_clusters']}")
        logger.info(f"   - Méthode embedding: {results['embedding_method'].upper()}")
        logger.info("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur pipeline: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
