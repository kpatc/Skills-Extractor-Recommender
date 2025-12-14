"""
Module de vectorisation et clustering des offres d'emploi.
"""

import logging
import sys
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pickle
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import CLUSTERING_CONFIG, MODELS_DIR
from modelling.embeddings import HybridEmbedder

logger = logging.getLogger(__name__)


class SkillsVectorizer:
    """Vectorise les offres basées sur les compétences extraites."""

    def __init__(self, use_gemini: bool = False):
        """
        Initialise le vectoriseur.
        
        Args:
            use_gemini: Si True, essaie d'utiliser Gemini API
        """
        self.embedder = HybridEmbedder()
        self.vectorizer_type = self.embedder.get_method()
        self.embeddings = None
        logger.info(f"✓ Vectorizer initialisé avec {self.vectorizer_type}")

    def vectorize_descriptions(self, offers: List[Dict]) -> np.ndarray:
        """
        Vectorise les descriptions des offres.
        
        Args:
            offers: Liste d'offres avec descriptions
        
        Returns:
            Matrice d'embeddings (n_samples, n_features)
        """
        descriptions = []

        for offer in offers:
            # Utiliser la description nettoyée si disponible
            text = offer.get("description_cleaned", offer.get("description", ""))
            descriptions.append(text)

        logger.info(f"Vectorisation de {len(descriptions)} descriptions...")
        embeddings = self.embedder.encode(descriptions)
        self.embeddings = embeddings
        return embeddings

    def vectorize_skills(self, offers: List[Dict]) -> np.ndarray:
        """
        Vectorise les compétences extraites (approche simple).
        
        Args:
            offers: Liste d'offres avec compétences extraites
        
        Returns:
            Matrice de compétences (n_samples, n_skills_unique)
        """
        # Collecter toutes les compétences uniques
        all_skills = set()
        for offer in offers:
            if "extracted_skills" in offer:
                all_skills.update(offer["extracted_skills"])

        skill_list = sorted(list(all_skills))
        n_offers = len(offers)
        n_skills = len(skill_list)

        # Créer une matrice binaire (1 si la compétence est présente)
        matrix = np.zeros((n_offers, n_skills))

        for idx, offer in enumerate(offers):
            if "extracted_skills" in offer:
                for skill in offer["extracted_skills"]:
                    if skill in skill_list:
                        col_idx = skill_list.index(skill)
                        matrix[idx, col_idx] = 1

        logger.info(f"Matrice des compétences: {matrix.shape}")
        return matrix


class OffersClustering:
    """Regroupe les offres en clusters basés sur les compétences."""

    def __init__(self):
        """Initialise le clustering."""
        self.algorithm = CLUSTERING_CONFIG.get("algorithm", "kmeans")
        self.model = None
        self.labels = None
        self.cluster_centers = None

    def fit(self, embeddings: np.ndarray) -> "OffersClustering":
        """
        Entraîne le modèle de clustering.
        
        Args:
            embeddings: Matrice d'embeddings
        
        Returns:
            Self pour chaînage
        """
        if self.algorithm == "kmeans":
            logger.info(f"Clustering K-Means avec {CLUSTERING_CONFIG['n_clusters']} clusters...")
            from sklearn.cluster import KMeans

            self.model = KMeans(
                n_clusters=CLUSTERING_CONFIG["n_clusters"],
                random_state=CLUSTERING_CONFIG["random_state"],
                n_init=10,
            )
            self.labels = self.model.fit_predict(embeddings)
            self.cluster_centers = self.model.cluster_centers_

        elif self.algorithm == "hdbscan":
            logger.info("Clustering HDBSCAN...")
            try:
                import hdbscan

                self.model = hdbscan.HDBSCAN(
                    min_cluster_size=CLUSTERING_CONFIG.get("min_cluster_size", 3)
                )
                self.labels = self.model.fit_predict(embeddings)
            except ImportError:
                logger.error(
                    "hdbscan non installé. "
                    "Installez avec: pip install hdbscan"
                )
                raise

        return self

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        """Prédit les clusters pour de nouveaux embeddings."""
        if self.model is None:
            raise ValueError("Le modèle doit être entraîné d'abord")

        return self.model.predict(embeddings)

    def save(self, filepath: Optional[Path] = None):
        """Sauvegarde le modèle."""
        if filepath is None:
            filepath = MODELS_DIR / "clustering_model.pkl"

        with open(filepath, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"Modèle sauvegardé: {filepath}")

    def load(self, filepath: Optional[Path] = None):
        """Charge un modèle sauvegardé."""
        if filepath is None:
            filepath = MODELS_DIR / "clustering_model.pkl"

        with open(filepath, "rb") as f:
            self.model = pickle.load(f)
        logger.info(f"Modèle chargé: {filepath}")

        return self


def cluster_offers(offers: List[Dict]) -> Dict:
    """
    Pipeline complet de clustering.
    
    Args:
        offers: Liste d'offres avec compétences extraites
    
    Returns:
        Dictionnaire avec clusters, labels et statistiques
    """
    # Vectoriser
    logger.info("Étape 1: Vectorisation...")
    vectorizer = SkillsVectorizer()
    embeddings = vectorizer.vectorize_descriptions(offers)

    # Clustering
    logger.info("Étape 2: Clustering...")
    clusterer = OffersClustering()
    clusterer.fit(embeddings)

    # Ajouter les labels aux offres
    for idx, offer in enumerate(offers):
        offer["cluster"] = int(clusterer.labels[idx])

    # Statistiques par cluster
    logger.info("Étape 3: Statistiques...")
    cluster_stats = _compute_cluster_statistics(offers, clusterer.labels)

    # Sauvegarder le modèle
    clusterer.save()

    return {
        "offers_clustered": offers,
        "model": clusterer.model,
        "labels": clusterer.labels,
        "cluster_stats": cluster_stats,
        "vectorizer": vectorizer,
    }


def _compute_cluster_statistics(offers: List[Dict], labels: np.ndarray) -> Dict:
    """Calcule les statistiques pour chaque cluster."""
    stats = {}
    n_clusters = len(np.unique(labels))

    for cluster_id in range(n_clusters):
        cluster_offers = [offers[i] for i in range(len(offers)) if labels[i] == cluster_id]

        # Compétences les plus communes dans ce cluster
        all_skills = []
        for offer in cluster_offers:
            if "extracted_skills" in offer:
                all_skills.extend(offer["extracted_skills"])

        from collections import Counter
        top_skills = Counter(all_skills).most_common(10)

        stats[cluster_id] = {
            "size": len(cluster_offers),
            "top_skills": top_skills,
            "titles": [offer.get("title", "") for offer in cluster_offers[:5]],
        }

    return stats
